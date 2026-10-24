"""Offline mechanical checks. No semantic, source-support, or STE certification claims."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any
from markdown_it import MarkdownIt
from jsonschema import Draft202012Validator, validators

VERSION = '0.1.0'
RULES = json.loads((Path(__file__).resolve().parents[1]/'assets/rules.json').read_text(encoding='utf-8'))
PROFILES = tuple(RULES['english_sentence_warning'])
WORD = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*|\d+(?:\.\d+)?")
VAGUE = {'here', 'click here', 'this link', 'read more', '这里', '此处', '点击这里'}


def strict_json(text: str) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    def constant(value):
        raise ValueError(f'Non-finite JSON constant: {value}')
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def read_text(path: Path) -> str:
    if not path.is_file() or path.stat().st_size > 10*1024*1024:
        raise ValueError(f'Input must be a regular file of at most 10 MiB: {path}')
    return path.read_text(encoding='utf-8-sig')


def validate_contract(contract: dict) -> None:
    keys = {'required_literals', 'forbidden_literals', 'required_headings', 'terms'}
    if not isinstance(contract, dict) or set(contract)-keys:
        raise ValueError('Contract must be an object with supported keys only')
    for key in keys-{'terms'}:
        items = contract.get(key, [])
        if not isinstance(items, list) or any(not isinstance(v, str) or not v for v in items):
            raise ValueError(f'{key} must be a list of non-empty strings')
    terms = contract.get('terms', [])
    if not isinstance(terms, list):
        raise ValueError('terms must be a list')
    for term in terms:
        if (not isinstance(term, dict) or set(term) != {'canonical','aliases'}
            or not isinstance(term['canonical'], str) or not term['canonical']
            or not isinstance(term['aliases'], list)
            or any(not isinstance(v,str) or not v for v in term['aliases'])):
            raise ValueError('Each term needs canonical and aliases strings')


def local_refs(value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {'$ref','$dynamicRef','$recursiveRef'} and (not isinstance(child,str) or not child.startswith('#')):
                raise ValueError('Only local fragment schema references are supported')
            local_refs(child)
    elif isinstance(value, list):
        for child in value:
            local_refs(child)


def parse_prose(text: str) -> tuple[list, list, list]:
    def blank(match):
        return ''.join('\n' if c == '\n' else ' ' for c in match.group())
    masked = re.sub(r'(?s)\$\$.*?\$\$|\\\[.*?\\\]', blank, text)
    tokens = MarkdownIt('commonmark', {'html':True}).enable('table').parse(masked)
    paragraphs, headings, links = [], [], []
    quote_depth = 0
    for i, token in enumerate(tokens):
        if token.type == 'blockquote_open': quote_depth += 1
        if token.type == 'blockquote_close': quote_depth -= 1
        if token.type != 'inline' or quote_depth: continue
        line = token.map[0]+1 if token.map else 1
        chunks, label, in_link = [], [], False
        for child in token.children or []:
            if child.type == 'link_open':
                in_link, label = True, []
            elif child.type == 'link_close':
                links.append((line, ''.join(label).strip())); in_link = False
            elif child.type in {'text','softbreak','hardbreak'}:
                value = child.content if child.type == 'text' else ' '
                chunks.append(value)
                if in_link: label.append(value)
            elif child.type == 'code_inline':
                chunks.append(' ')
                if in_link: label.append(child.content)
        prose = re.sub(r'(?s)\\\(.*?\\\)|(?<!\\)\$[^\n$]*?\$', ' ', ''.join(chunks))
        previous = tokens[i-1] if i else None
        if previous and previous.type == 'heading_open':
            headings.append((line,int(previous.tag[1:]),prose.strip()))
        elif prose.strip(): paragraphs.append((line,prose))
    return paragraphs, headings, links


def check_text(text: str, *, profile: str, language: str, contract: dict | None = None,
               schema: dict | bool | None = None) -> dict:
    if profile not in PROFILES or language not in {'en','zh'}: raise ValueError('Unsupported profile/language')
    if schema is not None and profile != 'structured': raise ValueError('Schema requires structured profile')
    if contract is not None: validate_contract(contract)
    rulemap = {r['id']:r for r in RULES['rules']}
    findings, performed, paragraphs = [], [], []
    def add(rule, message, line=None):
        findings.append({'rule_id':rule,'severity':rulemap[rule]['severity'],
                         'checkability':rulemap[rule]['checkability'],'line':line,'message':message})
    if contract is not None:
        performed += ['TP-C001','TP-C002']
        for literal in contract.get('required_literals',[]):
            if literal not in text: add('TP-C001', f'Missing protected literal: {literal!r}')
        for literal in contract.get('forbidden_literals',[]):
            offset = text.find(literal)
            if offset >= 0: add('TP-C002', f'Forbidden literal: {literal!r}', text.count('\n',0,offset)+1)
    schema_state = 'not_applicable'
    if profile == 'structured':
        performed.append('TP-J001'); schema_state = 'not_evaluated'
        try: instance = strict_json(text)
        except ValueError as exc:
            add('TP-J001', str(exc), getattr(exc,'lineno',None)); schema_state = 'blocked_by_syntax'
        else:
            if schema is not None:
                if not isinstance(schema,(dict,bool)): raise ValueError('Schema must be object or boolean')
                local_refs(schema)
                cls = validators.validator_for(schema, default=Draft202012Validator)
                cls.check_schema(schema)
                errors = sorted(cls(schema).iter_errors(instance),key=lambda e:str(e.path))
                performed.append('TP-J002')
                for e in errors: add('TP-J002', f'/{"/".join(map(str,e.path))}: {e.message}')
                schema_state = 'failed' if errors else 'passed'
        if contract and contract.get('required_headings'): raise ValueError('JSON cannot have Markdown headings')
    else:
        paragraphs, headings, links = parse_prose(text)
        performed += ['TP-G001','TP-G002']
        previous = None
        for line,level,_ in headings:
            if previous is not None and level > previous+1: add('TP-G002',f'Heading jumps from {previous} to {level}',line)
            previous = level
        for line,label in links:
            if label.casefold() in VAGUE: add('TP-G001', f'Vague link text: {label!r}',line)
        if contract is not None:
            performed.append('TP-C003')
            found = {heading.casefold() for _,_,heading in headings}
            for heading in contract.get('required_headings',[]):
                if heading.casefold() not in found: add('TP-C003',f'Missing required heading: {heading!r}')
            if contract.get('terms'):
                performed.append('TP-T001')
                for term in contract['terms']:
                    for alias in term['aliases']:
                        pattern = rf'(?<!\w){re.escape(alias)}(?!\w)' if alias.isascii() else re.escape(alias)
                        for line,prose in paragraphs:
                            if re.search(pattern,prose,re.I): add('TP-T001',f'Alias {alias!r}; prefer {term["canonical"]!r}',line)
        limit = RULES['english_sentence_warning'][profile]
        if language == 'en' and limit:
            performed.append('TP-S001')
            for line,prose in paragraphs:
                for sentence in re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])',prose):
                    count = len(WORD.findall(sentence))
                    if count > limit: add('TP-S001',f'Approximate English sentence length {count}; advisory target {limit}',line)
    errors = sum(f['severity']=='error' for f in findings)
    warnings = sum(f['severity']=='warning' for f in findings)
    combined = ' '.join(p for _,p in paragraphs)
    return {'schema_version':'0.1','checker_version':VERSION,
            'artifact_sha256':hashlib.sha256(text.encode()).hexdigest(),'profile':profile,'language':language,
            'mechanical_status':'failed' if errors else ('passed_with_warnings' if warnings else 'passed'),
            'semantic_status':'not_evaluated','asd_ste100_conformance':'not_evaluated','schema_status':schema_state,
            'contract_supplied':contract is not None,'counts':{'errors':errors,'warnings':warnings},
            'observations':{'latin_prose_words_approx':len(WORD.findall(combined)),
                            'han_prose_characters':len(re.findall(r'[\u3400-\u4dbf\u4e00-\u9fff]',combined))},
            'checks_executed':performed,'findings':findings,
            'not_evaluated':['semantic entailment','citation support','official STE dictionary/meaning',
                             'human comprehension','agent success'],
            'scope_notes':['Locations are paragraph start lines, not exact sentence offsets',
                           'Code and block quotations excluded from prose style checks',
                           'Common TeX masked; other math dialects may need exclusions',
                           'Schema formats and external references are not validated',
                           'Literal presence and style checks do not prove meaning']}


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact',type=Path)
    parser.add_argument('--profile',required=True,choices=PROFILES)
    parser.add_argument('--lang',required=True,choices=['en','zh'])
    parser.add_argument('--contract',type=Path); parser.add_argument('--schema',type=Path)
    parser.add_argument('--format',choices=['brief','json'],default='brief')
    parser.add_argument('--report',type=Path); parser.add_argument('--max-findings',type=int,default=8)
    args=parser.parse_args(argv)
    try:
        if args.max_findings < 1: raise ValueError('--max-findings must be positive')
        if args.report and args.report.resolve() in [p.resolve() for p in [args.artifact,args.contract,args.schema] if p]:
            raise ValueError('Report cannot overwrite an input')
        report=check_text(read_text(args.artifact),profile=args.profile,language=args.lang,
                          contract=strict_json(read_text(args.contract)) if args.contract else None,
                          schema=strict_json(read_text(args.schema)) if args.schema else None)
        for name,path in [('file',args.artifact),('contract',args.contract),('schema',args.schema)]:
            if path: report[name+'_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        serialized=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True); args.report.write_text(serialized,encoding='utf-8')
        if args.format=='json': print(serialized,end='')
        else:
            counts=report['counts']
            print(f"mechanical={report['mechanical_status']} errors={counts['errors']} warnings={counts['warnings']} semantic=not_evaluated")
            for f in sorted(report['findings'],key=lambda f:f['severity']!='error')[:args.max_findings]:
                print(f"{f['rule_id']}:{f['line'] or '-'} {f['message'][:160]}")
            if len(report['findings'])>args.max_findings: print('More findings omitted; use --report for complete evidence.')
        return 1 if report['counts']['errors'] else 0
    except Exception as exc:
        print(f'check failed ({type(exc).__name__}): {exc}',file=sys.stderr); return 2


if __name__=='__main__': raise SystemExit(main())
