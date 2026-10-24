from pathlib import Path
import hashlib
import importlib.util
import json
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('checker',ROOT/'skills/text-prison/scripts/check.py')
checker=importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)

def check(text,**kwargs):
    return checker.check_text(text,profile=kwargs.pop('profile','explanation'),language=kwargs.pop('language','en'),**kwargs)

def test_missing_literal():
    r=check('Timeout: 60 s',contract={'required_literals':['30 s']})
    assert r['counts']['errors']==1 and r['semantic_status']=='not_evaluated'

def test_presence_does_not_prove_meaning():
    r=check((ROOT/'examples/draft-semantic-error.md').read_text(),profile='research',contract=json.loads((ROOT/'examples/contract.json').read_text()))
    assert r['mechanical_status']=='passed' and r['semantic_status']=='not_evaluated'

def test_forbidden_literal():
    assert check('Run rm -rf',contract={'forbidden_literals':['rm -rf']})['findings'][0]['rule_id']=='TP-C002'

def test_required_heading():
    assert check('# Summary',contract={'required_headings':['Result']})['counts']['errors']==1

def test_heading_case():
    assert check('# RESULT',contract={'required_headings':['Result']})['counts']['errors']==0

def test_heading_jump():
    assert any(f['rule_id']=='TP-G002' for f in check('# Title\n\n### Details')['findings'])

def test_initial_heading():
    assert check('### Details')['counts']['warnings']==0

def test_vague_link():
    assert any(f['rule_id']=='TP-G001' for f in check('[click here](https://example.test)')['findings'])

def test_code_excluded():
    assert check('```text\n'+'word '*100+'[click here](https://example.test)\n```')['counts']['warnings']==0

def test_inline_code_excluded():
    assert not check('Use `old term`.',contract={'terms':[{'canonical':'new term','aliases':['old term']}]})['findings']

def test_quotes_excluded():
    assert check('> '+'word '*100)['counts']['warnings']==0

def test_math_excluded():
    assert check('$$\n'+'alpha '*100+'\n$$')['counts']['warnings']==0

def test_procedure_warning():
    assert any(f['rule_id']=='TP-S001' for f in check('word '*21+'.',profile='procedure')['findings'])

def test_chinese_no_english_limit():
    assert not any(f['rule_id']=='TP-S001' for f in check('word '*100,language='zh',profile='procedure')['findings'])

def test_research_no_length_limit():
    assert check('word '*100,profile='research')['counts']['warnings']==0

def test_term_alias():
    assert check('An old term.',contract={'terms':[{'canonical':'new term','aliases':['old term']}]})['findings'][0]['rule_id']=='TP-T001'

def test_alias_boundary():
    assert not check('The foobar.',contract={'terms':[{'canonical':'x','aliases':['foo']}]})['findings']

@pytest.mark.parametrize('contract',[{'required_literals':'30'},{'execute':'bad'},{'terms':[{'canonical':'x','aliases':'a'}]}])
def test_bad_contract(contract):
    with pytest.raises(ValueError): check('text',contract=contract)

@pytest.mark.parametrize('text',['{','{"x":1,"x":2}','{"x":NaN}','```json\n{}\n```',
                               '{"x":1e999}', '{"x":-1e999}', '[{"x":1.7976931348623159e308}]'])
def test_invalid_json(text):
    assert check(text,profile='structured')['counts']['errors']==1

@pytest.mark.parametrize('text',['1.7976931348623157e308', '-1.7976931348623157e308',
                               '1.25e2', '1e-999', '1'+('0'*400)])
def test_finite_json_numeric_boundaries(text):
    assert check(text,profile='structured')['mechanical_status']=='passed'

def test_strict_json_rejects_float_overflow_before_schema():
    with pytest.raises(ValueError,match='finite range'):
        checker.strict_json('{"nested":[1e999]}')
    report=check('{"nested":[1e999]}',profile='structured',schema={'type':'object'})
    assert report['schema_status']=='blocked_by_syntax'
    assert 'TP-J002' not in report['checks_executed']

def test_schema_pass():
    assert check('{"x":1}',profile='structured',schema={'type':'object','required':['x']})['schema_status']=='passed'

def test_schema_fail():
    assert check('{}',profile='structured',schema={'type':'object','required':['x']})['schema_status']=='failed'

def test_schema_absent():
    assert check('{}',profile='structured')['schema_status']=='not_evaluated'

def test_remote_ref():
    with pytest.raises(ValueError): check('{}',profile='structured',schema={'$ref':'https://example.test/schema'})

def test_local_ref():
    assert check('3',profile='structured',schema={'$defs':{'i':{'type':'integer'}},'$ref':'#/$defs/i'})['schema_status']=='passed'

def test_boolean_schema():
    assert check('{}',profile='structured',schema=False)['schema_status']=='failed'

def test_json_no_heading_contract():
    with pytest.raises(ValueError): check('{}',profile='structured',contract={'required_headings':['Result']})

def test_do_not_overwrite_input(tmp_path):
    p=tmp_path/'doc.md';p.write_text('text')
    assert checker.main([str(p),'--profile','explanation','--lang','en','--report',str(p)])==2
    assert p.read_text()=='text'

def test_invalid_schema_tool_error(tmp_path):
    p=tmp_path/'doc.json';p.write_text('{}')
    s=tmp_path/'schema.json';s.write_text('{"type":"invalid"}')
    assert checker.main([str(p),'--profile','structured','--lang','en','--schema',str(s)])==2

def test_contract_remains_data():
    assert check('nothing',contract={'required_literals':['__import__("os").system("false")']})['counts']['errors']==1


@pytest.mark.parametrize(('source','candidate','protected'),[
    ('You must not publish before approval.','You must publish before approval.',['publish','approval']),
    ('The effect may occur.','The effect will occur.',['effect','occur']),
    ('Restart only if the checksum matches.','Restart even if the checksum differs.',['Restart','checksum']),
    ('The delay is 30 s.','The delay is 30 ms.',['delay','30']),
    ('The measurements are correlated.','The measurements establish causation.',['measurements']),
])
def test_semantic_changes_are_not_certified_by_literal_presence(source,candidate,protected):
    contract={'required_literals':protected}
    for text in (source,candidate):
        report=check(text,profile='research',contract=contract)
        assert report['mechanical_status']=='passed'
        assert report['semantic_status']=='not_evaluated'
        assert not any(rule.startswith('TP-M') for rule in report['checks_executed'])


def test_equivalent_units_still_require_an_explicit_literal_contract():
    report=check('The delay is 0.5 min.',profile='research',contract={'required_literals':['30 s']})
    assert report['findings'][0]['rule_id']=='TP-C001'
    assert report['semantic_status']=='not_evaluated'


@pytest.mark.parametrize('wrapper',[
    '```text\n{}\n```', '    {}', '`{}`', '> {}',
    '$${}$$', '\\[{}\\]', '${}$', '\\({}\\)',
])
def test_protected_regions_do_not_produce_prose_style_findings(wrapper):
    text=wrapper.format('legacy_api '+'word '*45)
    report=check(text,profile='procedure',contract={
        'required_literals':['legacy_api'],
        'terms':[{'canonical':'current_api','aliases':['legacy_api']}],
    })
    assert report['findings']==[]
    assert report['artifact_sha256']==hashlib.sha256(text.encode('utf-8')).hexdigest()
    assert report['semantic_status']=='not_evaluated'


@pytest.mark.parametrize('wrapper',['```sh\n{}\n```','> {}','$${}$$'])
def test_exact_contracts_include_protected_regions(wrapper):
    report=check(wrapper.format('legacy_api'),contract={'forbidden_literals':['legacy_api']})
    assert [finding['rule_id'] for finding in report['findings']]==['TP-C002']


def test_citation_destination_is_protected_from_terminology_style_checks():
    url='https://example.test/legacy_api'
    report=check(f'[Measurement record]({url})',contract={
        'required_literals':[url],
        'terms':[{'canonical':'current_api','aliases':['legacy_api']}],
    })
    assert report['findings']==[]
    assert report['semantic_status']=='not_evaluated'


def test_overflowing_schema_is_a_tool_error(tmp_path):
    artifact=tmp_path/'doc.json'; artifact.write_text('{}',encoding='utf-8')
    schema=tmp_path/'schema.json'; schema.write_text('{"maximum":1e999}',encoding='utf-8')
    assert checker.main([str(artifact),'--profile','structured','--lang','en','--schema',str(schema)])==2


@pytest.mark.parametrize('profile',checker.PROFILES)
@pytest.mark.parametrize('language',['en','zh'])
def test_every_profile_keeps_semantic_review_separate(profile,language):
    text='{}' if profile=='structured' else 'A supported-looking statement.'
    report=check(text,profile=profile,language=language)
    assert report['semantic_status']=='not_evaluated'
    assert report['asd_ste100_conformance']=='not_evaluated'
