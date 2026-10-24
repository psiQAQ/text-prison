import json
from pathlib import Path

import pytest

from eval.runner import Experiment, HumanReviewPending, generation_rules
from eval.contracts import load_tasks, model_visible_task
from eval.reporting import complete_inventory, shared_workflow_costs, summarize


@pytest.fixture
def experiment(tmp_path, monkeypatch):
    import eval.runner as runner
    # Redirect only experiment storage; use real versioned input files and SQLite.
    monkeypatch.setattr(runner, 'experiment_path', lambda name: tmp_path / name)
    return Experiment('offline-test', create=True)


def test_inventory_and_human_gate_keep_all_denominators(experiment):
    inventory = experiment.assignments()
    assert len(inventory) == 115
    assert len({row['assignment_id'] for row in inventory}) == 115
    assert sum(row['phase'] == 'executor' for row in inventory) == 8
    assert sum(row['phase'] == 'writer' for row in inventory) == 24
    with pytest.raises(HumanReviewPending):
        experiment.require_calibration()
    report = summarize(experiment)
    assert report['statuses'] == {'not_run': 115}
    details = json.loads(Path(report['json']).read_text(encoding='utf8'))
    assert details['execution']['product_native/A']['assigned'] == 2
    assert details['execution']['product_native/A']['unknown'] == 2
    assert details['triggers']['counts']['unknown_positive'] == 4


def test_smoke_metadata_validates_before_calls():
    assert model_visible_task(Experiment._smoke_task())['rubric']['critical']


def test_unstarted_tasks_and_retries_remain_visible(experiment):
    assignment = experiment.assignments()[0]
    record = {**assignment, 'attempt_id': 'a', 'retry_of': None, 'status': 'failed'}
    retry = {**record, 'attempt_id': 'b', 'retry_of': 'a', 'status': 'completed'}
    rows = complete_inventory(experiment, [record, retry])
    assert len(rows) == 116
    assert sum(row['status'] == 'not_run' for row in rows) == 114


def test_shared_draft_is_not_double_counted_in_actual_costs():
    actual = [{'attempt_id': 'draft', 'usage': {'estimated_cost_usd': 2}},
              {'attempt_id': 'generic', 'shared_draft_ref': 'draft', 'usage': {'estimated_cost_usd': 1}},
              {'attempt_id': 'mechanical', 'shared_draft_ref': 'draft', 'usage': {'estimated_cost_usd': 3}}]
    workflows = shared_workflow_costs(actual)['workflows']
    assert [r['comparable_workflow_usd'] for r in workflows] == [3, 5]
    assert sum(r['usage']['estimated_cost_usd'] for r in actual) == 6


def test_checker_contract_is_restricted_to_supported_fields(experiment):
    task = next(t for t in load_tasks() if t['profile'] == 'procedure')
    config = experiment._tools(task)
    assert config['contract']['required_literals']
    assert set(config['contract']) == {'required_literals', 'required_headings'}
    assert 'executor' not in config['contract']


def test_relative_successful_skill_read_counts_as_trigger(experiment):
    workspace = experiment.path / 'jobs/example/workspace'
    workspace.mkdir(parents=True)
    events = [{'type': 'tool_execution_start', 'toolName': 'read', 'toolCallId': 'read-one',
               'args': {'path': '../../../inputs/skill/SKILL.md'}},
              {'type': 'tool_execution_end', 'toolCallId': 'read-one', 'isError': False}]
    assert experiment._trigger({'tool_events': events, 'settled': True}, workspace)['observed'] is True
    assert experiment._trigger({'tool_events': [], 'settled': True, 'status': 'failed'}, workspace)['observed'] is None


def test_controlled_rules_share_preservation_but_exclude_orchestration(experiment):
    full = generation_rules(experiment.skill, 'explanation', 'zh', full=True)
    routed = generation_rules(experiment.skill, 'explanation', 'zh', full=False)
    assert full.startswith('Preserve source facts') and routed.startswith('Preserve source facts')
    assert '[research.md]' in full and '[research.md]' not in routed
    assert '[lang-en.md]' in full and '[lang-en.md]' not in routed
    assert 'scripts/check.py' not in full and 'check_artifact' not in routed


def test_input_tampering_fails_resume(experiment):
    (experiment.inputs / 'skill/SKILL.md').write_text('changed')
    with pytest.raises(ValueError, match='hashes changed'):
        Experiment('offline-test')
