import json
from pathlib import Path

import pytest

from eval.runner import Experiment, HumanReviewPending, generation_rules, plan_for
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


@pytest.mark.parametrize('passed,expected', [(True, 0), (False, 1)])
def test_cli_smoke_exit_code_reflects_readiness(monkeypatch, capsys, passed, expected):
    import eval.__main__ as cli
    class SmokeExperiment:
        def smoke(self, *, retry):
            return [{'outcomes': {'smoke_passed': passed}}]
    monkeypatch.setattr(cli, 'Experiment', lambda name: SmokeExperiment())
    assert cli.main(['run', 'smoke']) == expected
    assert json.loads(capsys.readouterr().out)[0]['outcomes']['smoke_passed'] is passed


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


def test_resuming_invalid_review_preserves_validation_status_without_model_call(experiment, monkeypatch):
    import eval.runner as runner
    from eval.common import digest, write_json

    task = load_tasks(experiment.inputs / 'tasks')[0]
    calls = []

    def invalid_model_response(*, job_dir, budget, prompt, **kwargs):
        calls.append(job_dir.name)
        job_dir.mkdir(parents=True)
        (job_dir / 'answer.txt').write_text('{}', encoding='utf-8')
        call_id, timeout = budget.claim(job_dir.name)
        budget.finish(call_id, 0.25, 'completed')
        receipt = {'call_id': call_id, 'host': 'test', 'host_version': 'synthetic',
                   'provider': 'synthetic', 'model': 'offline', 'reasoning_effort': 'high',
                   'prompt_hash': digest(prompt), 'elapsed_seconds': 0.25, 'timeout_seconds': timeout}
        result = {'receipt': receipt, 'status': 'completed', 'settled': True,
                  'messages': [], 'tool_events': [],
                  'usage': {'coverage': 'unknown', 'input_total': None, 'output_total': None, 'raw_log': None}}
        write_json(job_dir / 'receipt.json', receipt)
        write_json(job_dir / 'parsed.json', result)
        return result

    monkeypatch.setattr(runner, 'invoke', invalid_model_response)
    packet = {'review_id': 'synthetic-invalid', 'task': task, 'candidate_text': 'Synthetic draft.'}
    first = experiment._judge(packet, 'deepseek', 'controlled')
    assert first['status'] == 'invalid_review' and first['error']
    path = experiment.jobs / first['attempt_id'] / 'run.json'
    before = path.read_bytes()
    resumed = experiment._judge(packet, 'deepseek', 'controlled')
    assert resumed == first
    assert path.read_bytes() == before
    assert len(calls) == experiment.budget.snapshot()['calls'] == 1


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


def test_ai_inventory_and_readiness_do_not_require_human_reviews(experiment):
    ai = Experiment('ai-offline', create=True, review_mode='ai_only')
    assert len(ai.assignments()) == 263
    assert len(ai.judge_roles) == 6
    assert ai.plan['max_calls'] == 276
    assert sum(ai.plan['allocation'].values()) == 276
    with pytest.raises(RuntimeError, match='AI readiness incomplete'):
        ai.require_calibration()
    assert ai.store.list_batches() == []


def stored_failed_call(experiment):
    from eval.common import write_json
    from eval.contracts import normalize_run
    call, _ = experiment.budget.claim('old-failed')
    experiment.budget.finish(call, 12.5, 'failed')
    record = normalize_run({'schema_version': '0.1', 'run_id': 'old-failed', 'task_id': 't',
        'scenario_id': 's', 'arm': 'A', 'host': 'test', 'model': 'test', 'profile': 'research',
        'language': 'en', 'status': 'failed',
        'usage': {'coverage': 'unknown', 'input_total': None, 'output_total': None, 'raw_log': None},
        'outcomes': {'semantic_status': 'not_evaluated', 'agent_success': None, 'trigger_observed': None}})
    write_json(experiment.jobs / 'old-failed' / 'run.json', record)


def test_inheritance_keeps_original_and_carries_actual_failed_call_cost(experiment):
    from eval.common import file_manifest
    stored_failed_call(experiment)
    before = file_manifest(experiment.path)
    ai = Experiment.inherit_ai_only('ai-inherited', experiment.name)
    assert file_manifest(experiment.path) == before
    assert ai.budget.snapshot()['calls'] == 1
    assert ai.budget.snapshot()['seconds'] == 12.5
    assert ai.budget.snapshot()['max_calls'] == 276
    assert ai.records()[0]['provenance']['inherited_from']['experiment_id'] == experiment.name
    assert ai.store.list_batches() == []
    with pytest.raises(ValueError, match='already exists'):
        Experiment.inherit_ai_only('ai-inherited', experiment.name)


def test_inheritance_rejects_running_or_unrecorded_calls(experiment):
    call, _ = experiment.budget.claim('unresolved')
    with pytest.raises(ValueError, match='active or unresolved'):
        Experiment.inherit_ai_only('ai-running', experiment.name)
    experiment.budget.finish(call, 1, 'failed')
    with pytest.raises(ValueError, match='do not reconcile'):
        Experiment.inherit_ai_only('ai-unrecorded', experiment.name)


def test_interrupted_budget_import_cannot_resume_as_an_empty_experiment(experiment, monkeypatch):
    from contextlib import contextmanager
    import eval.runner as runner
    from eval.budget import Budget
    from eval.common import file_manifest

    stored_failed_call(experiment)
    before = file_manifest(experiment.path)

    class InterruptedImportBudget(Budget):
        @contextmanager
        def connect(self):
            with super().connect() as db:
                class InterruptAfterInsert:
                    def execute(self, *args, **kwargs):
                        return db.execute(*args, **kwargs)

                    def executemany(self, *args, **kwargs):
                        db.executemany(*args, **kwargs)
                        raise OSError('injected interruption before inherited budget commit')
                yield InterruptAfterInsert()

    monkeypatch.setattr(runner, 'Budget', InterruptedImportBudget)
    with pytest.raises(OSError, match='injected interruption'):
        Experiment.inherit_ai_only('ai-interrupted-import', experiment.name)
    destination = runner.experiment_path('ai-interrupted-import')
    assert not (destination / 'experiment.json').exists()
    assert Budget(destination / 'budget.sqlite', 276, 14400).snapshot()['calls'] == 0
    with pytest.raises(FileNotFoundError, match='not initialized'):
        Experiment('ai-interrupted-import')
    assert file_manifest(experiment.path) == before

    monkeypatch.setattr(runner, 'Budget', Budget)
    recovered = Experiment.inherit_ai_only('ai-recovered-import', experiment.name)
    resumed = Experiment(recovered.name)
    assert resumed.budget.snapshot()['calls'] == 1
    assert resumed.budget.snapshot()['seconds'] == 12.5
    assert len(resumed.records()) == 1
    assert file_manifest(experiment.path) == before


def test_inherited_manifest_with_missing_budget_refuses_resume_until_restored(experiment):
    from contextlib import closing
    import shutil
    import sqlite3
    import eval.runner as runner
    from eval.common import read_json, write_json

    stored_failed_call(experiment)
    ai = Experiment.inherit_ai_only('ai-preserved-ledger', experiment.name)
    destination = runner.experiment_path('ai-budget-recovery')
    shutil.copytree(ai.path, destination, ignore=shutil.ignore_patterns('*.sqlite', '*.sqlite-*'))
    manifest = read_json(destination / 'experiment.json')
    manifest['experiment_id'] = destination.name
    write_json(destination / 'experiment.json', manifest)
    for path in (destination / 'jobs').glob('*/run.json'):
        record = read_json(path)
        record['experiment_id'] = destination.name
        write_json(path, record)
    ledger = destination / 'budget.sqlite'
    with pytest.raises(ValueError, match='Inherited budget is missing'):
        Experiment(destination.name)
    assert not ledger.exists()
    with closing(sqlite3.connect(ai.budget.path)) as source_db, closing(sqlite3.connect(ledger)) as restored_db:
        source_db.backup(restored_db)
    restored = Experiment(destination.name)
    assert restored.budget.snapshot()['calls'] == 1
    assert restored.budget.snapshot()['seconds'] == 12.5


@pytest.mark.parametrize('operation', ['writer', 'generic_feedback', 'mechanical_feedback'])
@pytest.mark.parametrize('empty_output', ['', ' \t\r\n'])
def test_empty_artifact_is_recorded_and_only_explicit_retry_creates_a_new_attempt(experiment, monkeypatch,
                                                                                 operation, empty_output):
    import eval.runner as runner
    from eval.common import digest, read_json, write_json

    task = next(task for task in load_tasks(experiment.inputs / 'tasks') if task['profile'] == 'explanation')
    calls = []

    def fake_model_call(*, job_dir, budget, prompt, **kwargs):
        # Only the external model boundary is synthetic; budget, runner, artifacts,
        # retries, validation, and review storage use their real implementations.
        calls.append(job_dir.name)
        candidate = empty_output if len(calls) == 1 else 'A nonempty synthetic candidate.'
        workspace = job_dir / 'workspace'
        workspace.mkdir(parents=True)
        (workspace / 'candidate.md').write_text(candidate, encoding='utf-8', newline='\n')
        (job_dir / 'drafts').mkdir()
        (job_dir / 'drafts/candidate.md.1.txt').write_text(candidate, encoding='utf-8', newline='\n')
        (job_dir / 'answer.txt').write_text('Saved.', encoding='utf-8')
        call_id, timeout = budget.claim(job_dir.name)
        budget.finish(call_id, 0.25, 'completed')
        receipt = {'call_id': call_id, 'host': 'test', 'host_version': 'synthetic', 'provider': 'synthetic',
                   'model': 'offline', 'reasoning_effort': 'medium', 'prompt_hash': digest(prompt),
                   'elapsed_seconds': 0.25, 'timeout_seconds': timeout}
        result = {'receipt': receipt, 'status': 'completed', 'settled': True, 'messages': [], 'tool_events': [],
                  'usage': {'coverage': 'unknown', 'input_total': None, 'output_total': None, 'raw_log': None}}
        write_json(job_dir / 'receipt.json', receipt)
        write_json(job_dir / 'parsed.json', result)
        return result

    monkeypatch.setattr(runner, 'invoke', fake_model_call)
    seed_text = 'A frozen synthetic draft.'
    seed = {'review_id': 'frozen-draft', 'batch_id': experiment.pilot_batch, 'candidate_text': seed_text,
            'artifact_hash': digest(seed_text), 'task': task, 'ai_reviews': [],
            'private': {'track': 'controlled', 'arm': 'C', 'writer_model': 'synthetic/offline',
                        'writer_attempt': 'original-draft--01'}}

    def generate(*, retry=False):
        if operation == 'writer':
            return experiment._write_candidate(task, 'C', retry=retry)
        return experiment._feedback(seed, operation == 'mechanical_feedback', retry=retry)

    assert generate() is None
    first = experiment.records()[0]
    first_path = experiment.jobs / first['attempt_id'] / 'run.json'
    first_hash = digest(first_path.read_bytes())
    assert first['status'] == 'failed' and first['outcomes']['failure_reason'] == 'empty_artifact'
    assert experiment.budget.snapshot()['calls'] == 1 and len(calls) == 1
    assert generate() is None
    assert experiment.budget.snapshot()['calls'] == 1 and len(calls) == 1

    packet = generate(retry=True)
    assert packet['candidate_text'] == 'A nonempty synthetic candidate.'
    second = read_json(experiment.jobs / packet['private']['writer_attempt'] / 'run.json')
    assert second['status'] == 'completed' and second['retry_of'] == first['attempt_id']
    assert digest(first_path.read_bytes()) == first_hash
    assert experiment.budget.snapshot()['calls'] == 2 and len(calls) == 2
    assert (experiment.jobs / first['attempt_id'] / 'workspace/candidate.md').read_text(encoding='utf-8').strip() == ''
    imported = experiment.store.import_batch(experiment.pilot_batch, [packet])
    assert len(imported['packets']) == 1
