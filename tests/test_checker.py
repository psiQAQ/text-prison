from pathlib import Path
import importlib.util
import json
import subprocess
import sys
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

@pytest.mark.parametrize('text',['{','{"x":1,"x":2}','{"x":NaN}','```json\n{}\n```'])
def test_invalid_json(text):
    assert check(text,profile='structured')['counts']['errors']==1

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

def test_installer_is_scoped_and_refuses_overwrite(tmp_path):
    cmd=[sys.executable,str(ROOT/'tools/install_skill.py'),'--agent','both','--project',str(tmp_path)]
    first=subprocess.run(cmd,capture_output=True,text=True)
    assert first.returncode==0,first.stderr
    assert (tmp_path/'.agents/skills/text-prison/SKILL.md').is_file()
    assert (tmp_path/'.claude/skills/text-prison/scripts/check.py').is_file()
    assert not (tmp_path/'AGENTS.md').exists() and not (tmp_path/'.claude/settings.json').exists()
    assert subprocess.run(cmd,capture_output=True).returncode==2

def test_contract_remains_data():
    assert check('nothing',contract={'required_literals':['__import__("os").system("false")']})['counts']['errors']==1
