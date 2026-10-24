from pathlib import Path
import importlib.util
import json

import pytest
import yaml


ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills/text-prison'
RULES=json.loads((SKILL/'assets/rules.json').read_text(encoding='utf-8'))
spec=importlib.util.spec_from_file_location('metadata_checker',SKILL/'scripts/check.py')
checker=importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)


def test_skill_frontmatter_and_routing_resources_are_portable():
    text=(SKILL/'SKILL.md').read_text(encoding='utf-8')
    frontmatter=yaml.safe_load(text.split('---',2)[1])
    assert frontmatter['name']=='text-prison'
    assert isinstance(frontmatter['description'],str) and frontmatter['description']
    assert set(frontmatter)<={'name','description','license','allowed-tools','metadata'}
    for profile in checker.PROFILES:
        assert (SKILL/'references'/f'{profile}.md').is_file()
    for language in ('en','zh'):
        assert (SKILL/'references'/f'lang-{language}.md').is_file()
    policy=yaml.safe_load((SKILL/'agents/openai.yaml').read_text(encoding='utf-8'))
    assert policy['policy']['allow_implicit_invocation'] is True


@pytest.mark.parametrize('rule',RULES['rules'],ids=lambda rule:rule['id'])
def test_rule_metadata_declares_actual_scope_and_limits(rule):
    assert rule['source'] and rule['source_type']
    assert rule['force'] in {'hard','advisory','review'}
    assert rule['scope']['profiles'] and set(rule['scope']['profiles'])<=set(checker.PROFILES)
    assert rule['scope']['languages'] and set(rule['scope']['languages'])<={'en','zh'}
    assert rule['scope']['content'] and rule['exceptions']
    assert isinstance(rule['coverage']['implemented'],bool)
    assert rule['coverage']['description'] and rule['coverage']['known_blind_spots']
    assert set(rule['examples'])=={'positive','negative','boundary'}
    if rule['checkability']=='semantic':
        assert rule['force']=='review'
        assert rule['coverage']['implemented'] is False


CASES=[(rule['id'],name,example)
       for rule in RULES['rules'] for name,example in rule['examples'].items()]


@pytest.mark.parametrize(('rule_id','case_name','example'),CASES,
                         ids=[f'{rule_id}-{name}' for rule_id,name,_ in CASES])
def test_documented_rule_examples_match_observable_checks(rule_id,case_name,example):
    report=checker.check_text(example['text'],profile=example.get('profile','explanation'),
                              language=example.get('language','en'),
                              contract=example.get('contract'),schema=example.get('schema'))
    actual=any(finding['rule_id']==rule_id for finding in report['findings'])
    expected=example['expected_detection']
    assert expected in {'finding','no_finding','not_evaluated'}
    assert actual is (expected=='finding')
    if expected=='not_evaluated':
        assert rule_id not in report['checks_executed']
    assert report['semantic_status']=='not_evaluated'
