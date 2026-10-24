"""Evidence-based reports. Do not reveal semantic labels before human initials freeze."""
from __future__ import annotations

from collections import Counter, defaultdict

from .analysis import compare_reviewers, ratio, summarize_costs, summarize_execution, summarize_reviews, summarize_triggers
from .common import digest, now, read_json, write_json
from .contracts import load_tasks


def complete_inventory(exp, actual):
    known = {record['assignment_id'] for record in actual}
    rows = list(actual)
    for assigned in exp.assignments():
        if assigned['assignment_id'] not in known:
            rows.append({**assigned, 'attempt_id': None, 'retry_of': None, 'status': 'not_run',
                         'outcomes': {'agent_success': None, 'trigger_observed': None},
                         'usage': {}, 'cost_scope': 'production_writer' if assigned['phase'] == 'writer' else
                         ('downstream_executor' if assigned['phase'] == 'executor' else 'evaluation_only')})
    return rows


def shared_workflow_costs(actual):
    """Actual spend counts C once; each comparable feedback workflow includes its own C draft."""
    by_attempt = {record['attempt_id']: record for record in actual}
    results = []
    for record in actual:
        if record.get('shared_draft_ref') is None:
            continue
        draft = by_attempt.get(record['shared_draft_ref'])
        metrics = {}
        for field in ('input_total', 'input_cached', 'input_cache_write', 'output_total', 'output_reasoning', 'model_calls', 'estimated_cost_usd'):
            values = [item.get('usage', {}).get(field) for item in (draft or {}, record)]
            metrics[field] = {'revision_only': values[1],
                              'comparable_workflow': sum(values) if all(value is not None for value in values) else None}
        results.append({'attempt_id': record['attempt_id'], 'shared_draft_ref': record['shared_draft_ref'],
                        'revision_only_usd': metrics['estimated_cost_usd']['revision_only'],
                        'comparable_workflow_usd': metrics['estimated_cost_usd']['comparable_workflow'],
                        'usage': metrics})
    return {'workflows': results, 'note': 'Comparable workflow values must not be summed into actual spend.'}


def summarize(exp):
    actual = exp.records()
    all_rows = complete_inventory(exp, actual)
    batches = exp.store.list_batches()
    report = {'report_version': '0.2', 'experiment_id': exp.name, 'generated_at': now(),
              'interpretation': 'Exploratory, four scenarios; no formal success threshold or human-reading result.',
              'budget': exp.budget.snapshot(), 'assigned': len(exp.assignments()),
              'attempts': len(actual), 'statuses_including_unstarted': dict(Counter(r['status'] for r in all_rows)),
              'human_batches': batches, 'semantic': {}, 'judge_calibration': {},
              'execution': {}, 'triggers': {}, 'costs': summarize_costs(actual), 'costs_by_workflow': {},
              'shared_workflows': shared_workflow_costs(actual),
              'not_run': ['formal reader study', 'Codex native execution', 'Claude native execution'],
              'provenance': {'inputs_manifest_sha256': digest((exp.path / 'experiment.json').read_bytes()),
                             'run_hashes': {r['attempt_id']: digest((exp.jobs / r['attempt_id'] / 'run.json').read_bytes()) for r in actual}}}
    for batch in batches:
        batch_id = batch['batch_id']
        if batch['state'] != 'frozen':
            report['semantic'][batch_id] = {'status': 'withheld_until_initial_freeze', 'assigned': batch['total'],
                                            'initial_submitted': batch['initial_submitted']}
            continue
        exported = exp.store.export_batch(batch_id, include_private=True)
        groups, pairs = defaultdict(list), defaultdict(list)
        for packet in exported['packets']:
            task = packet['task']
            private = packet['private']
            track, arm = private.get('track', 'calibration'), private.get('arm', 'calibration')
            initial = packet['initial']['review'] if packet['initial']['state'] == 'frozen' else None
            final = packet.get('adjudication', {})
            final_review = final.get('review') if final.get('state') == 'submitted' else None
            for stage, review in [('human_initial', initial), ('human_adjudication', final_review)]:
                groups[f'{track}/{arm}/{stage}'].append({'scenario_id': task['scenario_id'], 'review': review, 'task': task})
            for role in ('deepseek', 'gpt'):
                sidecar = next((r for r in packet['ai_reviews'] if r['judge_id'] == role), {})
                review = sidecar.get('review') if sidecar.get('status') == 'completed' else None
                groups[f'{track}/{arm}/ai_{role}'].append({'scenario_id': task['scenario_id'], 'review': review, 'task': task})
                pairs[role].append({'human_review': initial, 'ai_review': review, 'human_stage': 'initial', 'task': task})
        # Include failed generation assignments in the same per-arm denominators.
        if batch_id == exp.pilot_batch:
            supplied = {p['private']['writer_attempt'].rsplit('--', 1)[0] for p in exported['packets']}
            tasks = {t['id']: t for t in load_tasks(exp.inputs / 'tasks')}
            for assigned in exp.assignments():
                if assigned['phase'] != 'writer' or assigned['assignment_id'] in supplied:
                    continue
                for stage in ('human_initial', 'human_adjudication', 'ai_deepseek', 'ai_gpt'):
                    groups[f"{assigned['track']}/{assigned['arm']}/{stage}"].append({
                        'scenario_id': assigned['scenario_id'], 'review': None, 'task': tasks[assigned['task_id']]})
        report['semantic'][batch_id] = {key: summarize_reviews(rows) for key, rows in groups.items()}
        report['judge_calibration'][batch_id] = {role: compare_reviewers(rows) for role, rows in pairs.items()}
    for track in ('product_native', 'controlled'):
        for arm in (('A', 'D') if track == 'product_native' else ('B', 'C')):
            key = f'{track}/{arm}'
            group = [r for r in all_rows if r['track'] == track and r['arm'] == arm]
            execution = summarize_execution(group)
            originals = [r for r in group if r['phase'] == 'executor' and r.get('retry_of') is None]
            violations = [r.get('outcomes', {}).get('constraint_violations') for r in originals]
            n, unknown = len(violations), sum(value is None for value in violations)
            bad = sum(value is not None and value > 0 for value in violations)
            execution['constraint_violation_incidence'] = {'verified': ratio(bad, n, assessed=n-unknown),
                                                           'possible': ratio(bad+unknown, n, assessed=n-unknown)}
            report['execution'][key] = execution
            production = [r for r in actual if r['track'] == track and r['arm'] == arm and r['phase'] in ('writer', 'executor')]
            executable_ids = {t['id'] for t in load_tasks(exp.inputs / 'tasks') if t.get('executable')}
            successes = execution['successes'] if execution['unknown'] == 0 else None
            report['costs_by_workflow'][key] = {
                'all_tasks': summarize_costs(production),
                'executable_tasks': summarize_costs([r for r in production if r['task_id'] in executable_ids], successes=successes),
                'success_denominator': 'first complete executor success, executable tasks only; unknown outcomes defer unit cost'}
    trigger_rows = [r for r in all_rows if r['phase'] == 'trigger' and r.get('retry_of') is None]
    report['triggers'] = summarize_triggers(trigger_rows)
    target = exp.path / 'summary.json'
    write_json(target, report)
    lines = ['# TextPrison local evidence', '', f"Experiment: `{exp.name}`. Exploratory results only.", '',
             f"CLI budget consumed: {report['budget']['calls']} / 128; {report['budget']['seconds']:.1f} / 14400 seconds.",
             f"Assignments: {report['assigned']}; stored attempts: {report['attempts']}.", '',
             '| Status | Count |', '|---|---:|']
    lines.extend(f'| {key} | {value} |' for key, value in sorted(report['statuses_including_unstarted'].items()))
    lines += ['', 'Human review progress:', '']
    lines.extend(f"- {b['batch_id']}: initial {b['initial_submitted']}/{b['total']}; final {b['adjudication_submitted']}/{b['total']}; {b['state']}." for b in batches)
    lines += ['', 'Semantic findings remain hidden until the whole initial batch is frozen. See summary.json for denominators and provenance.',
              'No human labels have been inferred from AI output. Model cost is the installed Pi catalog estimate, not a verified invoice.', '']
    (exp.path / 'SUMMARY.md').write_text('\n'.join(lines), encoding='utf-8', newline='\n')
    return {'json': str(target), 'markdown': str(exp.path / 'SUMMARY.md'), 'budget': report['budget'],
            'human_batches': batches, 'statuses': report['statuses_including_unstarted']}
