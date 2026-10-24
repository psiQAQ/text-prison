"""Mode-aware reports with assigned denominators and explicit evidence boundaries."""
from __future__ import annotations

from collections import Counter, defaultdict

from .analysis import (compare_reviewers, ratio, summarize_ai_reviews, summarize_costs,
                       summarize_execution, summarize_reviews, summarize_triggers)
from .common import digest, now, write_json
from .contracts import load_calibration_packets, load_tasks, loads_json, validate_review


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


def _persisted_judge_review(exp, assigned, attempt, packet, task):
    """Use the latest execution receipt, not an older database projection."""
    status = attempt['status']
    unavailable = {'judge_id': assigned['role'], 'model': attempt.get('model'),
                   'attempt_id': attempt['attempt_id'], 'review': None,
                   'status': 'review_unavailable' if status == 'completed' else status}
    evidence = {'source': 'run_record', 'attempt_id': attempt['attempt_id'], 'sidecar_verified': False}
    if packet is None:
        return unavailable, {**evidence, 'reason': 'artifact_packet_unavailable'}
    sidecar_path = exp.jobs / attempt['attempt_id'] / 'semantic-review.json'
    evidence['sidecar_path'] = str(sidecar_path)
    references = [item for item in attempt.get('review_refs', [])
                  if item.get('review_id') == assigned['review_id'] and item.get('reviewer_id') == assigned['role']]
    if len(references) != 1:
        return unavailable, {**evidence, 'reason': 'review_reference_missing_or_ambiguous'}
    evidence['reference_sha256'] = references[0].get('sha256')
    try:
        raw = sidecar_path.read_bytes()
        evidence['sidecar_sha256'] = digest(raw)
        if evidence['sidecar_sha256'] != evidence['reference_sha256']:
            return unavailable, {**evidence, 'reason': 'sidecar_hash_mismatch'}
        sidecar = loads_json(raw.decode('utf-8-sig'))
        if (not isinstance(sidecar, dict) or sidecar.get('judge_id') != assigned['role'] or
                sidecar.get('attempt_id') != attempt['attempt_id'] or sidecar.get('model') != attempt.get('model')):
            raise ValueError('Sidecar identity does not match the latest execution record')
        if status == 'completed':
            if sidecar.get('status') != 'completed':
                raise ValueError('Completed execution does not have a completed review sidecar')
            sidecar['review'] = validate_review(sidecar.get('review'), task, packet['candidate_text'], packet.get('original_text'))
        else:
            if (sidecar.get('status') != status and not (status == 'failed' and sidecar.get('status') == 'invalid_review')):
                raise ValueError('Sidecar failure state does not match the latest execution record')
            if sidecar.get('review') is not None:
                raise ValueError('An incomplete execution cannot supply a completed review')
        return sidecar, {**evidence, 'source': 'job_sidecar', 'sidecar_verified': True}
    except (OSError, UnicodeError, ValueError) as exc:
        return unavailable, {**evidence, 'reason': 'sidecar_unavailable_or_invalid', 'error': str(exc)}


def _ai_assigned_groups(exp, batch_id, packets, assignments, actual, tasks):
    """Construct semantic denominators from the plan, even before any packet exists."""
    supplied = {packet['internal_review_id']: packet for packet in packets}
    if len(supplied) != len(packets):
        raise ValueError('Duplicate packet IDs in AI report export')
    planned = defaultdict(list)
    for assignment in assignments:
        if assignment['phase'] == 'judge' and ((assignment['track'] == 'calibration') == (batch_id == exp.calibration_batch)):
            planned[assignment['review_id']].append(assignment)
    if set(supplied) - set(planned):
        raise ValueError('AI report contains packets outside the frozen assignment inventory')
    calibration = {'cal-' + digest(packet['review_id'])[:12]: packet
                   for packet in load_calibration_packets(exp.inputs / 'calibration')}
    by_assignment = {row['assignment_id']: row for row in assignments}
    latest = {row['assignment_id']: row for row in actual}
    groups = defaultdict(list)
    for review_id, judge_assignments in sorted(planned.items()):
        if {row['role'] for row in judge_assignments} != set(exp.judge_roles) or len(judge_assignments) != len(exp.judge_roles):
            raise ValueError('Each artifact must retain every configured judge assignment')
        first = judge_assignments[0]
        if first['track'] == 'calibration':
            task, track, arm = calibration[review_id]['task'], 'calibration', 'calibration'
        else:
            writer = by_assignment[first['source_assignment']]
            task, track, arm = tasks[writer['task_id']], writer['track'], writer['arm']
        packet = supplied.get(review_id)
        if packet:
            # ReviewStore stores a missing original as "". Restore the caller's
            # frozen meaning before both sidecar validation and metric analysis.
            original = packet.get('original_text')
            if track == 'calibration':
                original = calibration[review_id].get('original_text')
            elif track != 'feedback_ablation' and original == '':
                original = None
            packet = {**packet, 'original_text': original}
        stored = packet.get('ai_reviews', []) if packet else []
        stored_by_role = {sidecar['judge_id']: sidecar for sidecar in stored}
        if len(stored_by_role) != len(stored) or set(stored_by_role) - set(exp.judge_roles):
            raise ValueError('AI sidecars must have unique configured judge IDs')
        sidecars, review_evidence = [], {}
        for assigned in judge_assignments:
            role = assigned['role']
            attempt = latest.get(assigned['assignment_id'])
            if attempt is not None:
                sidecar, evidence = _persisted_judge_review(exp, assigned, attempt, packet, task)
            elif role in stored_by_role:
                sidecar = stored_by_role[role]
                evidence = {'source': 'review_store', 'attempt_id': sidecar.get('attempt_id'),
                            'sidecar_verified': False, 'reason': 'no_execution_record_available'}
            else:
                sidecar = {'judge_id': role, 'review': None, 'status': 'not_run'}
                evidence = {'source': 'assignment_inventory', 'attempt_id': None, 'sidecar_verified': False}
            sidecars.append(sidecar)
            review_evidence[role] = evidence
        row = {'artifact_id': review_id, 'scenario_id': task['scenario_id'], 'task': task, 'ai_reviews': sidecars,
               'artifact_available': packet is not None, 'review_evidence': review_evidence}
        if packet:
            row.update(candidate_text=packet['candidate_text'], original_text=packet.get('original_text'))
        groups[f'{track}/{arm}'].append(row)
    return groups


def _human_batch_summary(exp, batch, tasks):
    """Legacy blind batches keep their original freeze boundary."""
    batch_id = batch['batch_id']
    if batch['state'] != 'frozen':
        return ({'status': 'withheld_until_initial_freeze', 'assigned': batch['total'],
                 'initial_submitted': batch['initial_submitted']}, None)
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
        for role in exp.judge_roles:
            sidecar = next((r for r in packet['ai_reviews'] if r['judge_id'] == role), {})
            review = sidecar.get('review') if sidecar.get('status') == 'completed' else None
            groups[f'{track}/{arm}/ai_{role}'].append({'scenario_id': task['scenario_id'], 'review': review, 'task': task})
            pairs[role].append({'human_review': initial, 'ai_review': review, 'human_stage': 'initial', 'task': task})
    if batch_id == exp.pilot_batch:
        supplied = {p['private']['writer_attempt'].rsplit('--', 1)[0] for p in exported['packets']}
        for assigned in exp.assignments():
            if assigned['phase'] != 'writer' or assigned['assignment_id'] in supplied:
                continue
            for stage in ('human_initial', 'human_adjudication', *(f'ai_{role}' for role in exp.judge_roles)):
                groups[f"{assigned['track']}/{assigned['arm']}/{stage}"].append({
                    'scenario_id': assigned['scenario_id'], 'review': None, 'task': tasks[assigned['task_id']]})
    return ({key: summarize_reviews(rows) for key, rows in groups.items()},
            {role: compare_reviewers(rows) for role, rows in pairs.items()})


def summarize(exp):
    actual = exp.records()
    assignments = exp.assignments()
    all_rows = complete_inventory(exp, actual)
    batches = exp.store.list_batches()
    review_mode = exp.plan.get('review_mode', 'human_blind')
    tasks = {task['id']: task for task in load_tasks(exp.inputs / 'tasks')}
    report = {'report_version': '0.3' if review_mode == 'ai_only' else '0.2',
              'experiment_id': exp.name, 'generated_at': now(), 'review_mode': review_mode,
              'plan': exp.plan, 'judge_roles': exp.judge_roles,
              'interpretation': 'Exploratory, four scenarios; no formal success threshold or human-reading result.',
              'budget': exp.budget.snapshot(), 'assigned': len(assignments),
              'attempts': len(actual), 'statuses_including_unstarted': dict(Counter(r['status'] for r in all_rows)),
              'review_batches': batches,
              'human_batches': [batch for batch in batches if batch.get('review_mode', 'human_blind') == 'human_blind'],
              'semantic': {}, 'judge_calibration': {},
              'execution': {}, 'triggers': {}, 'costs': summarize_costs(actual), 'costs_by_workflow': {},
              'shared_workflows': shared_workflow_costs(actual),
              'not_run': ['formal reader study', 'Codex native execution', 'Claude native execution'],
              'provenance': {'inputs_manifest_sha256': digest((exp.path / 'experiment.json').read_bytes()),
                             'run_hashes': {r['attempt_id']: digest((exp.jobs / r['attempt_id'] / 'run.json').read_bytes()) for r in actual},
                             'lineage': exp.manifest.get('lineage')}}
    if review_mode == 'ai_only':
        report['not_run'].append('independent human review and adjudication (disabled in AI-only mode)')
        by_batch = {batch['batch_id']: batch for batch in batches}
        for batch_id in (exp.calibration_batch, exp.pilot_batch):
            batch = by_batch.get(batch_id)
            if batch and batch.get('review_mode', 'human_blind') != 'ai_only':
                raise ValueError('AI-only report cannot reveal a historical human-blind batch')
            packets = exp.store.export_batch(batch_id, include_private=True)['packets'] if batch else []
            groups = _ai_assigned_groups(exp, batch_id, packets, assignments, actual, tasks)
            report['semantic'][batch_id] = {}
            for key, rows in groups.items():
                summary = summarize_ai_reviews(rows, exp.judge_roles)
                evidence_by_artifact = {row['artifact_id']: row['review_evidence'] for row in rows}
                for role, judge in summary['by_judge'].items():
                    for artifact in judge['artifacts']:
                        artifact['review_evidence'] = evidence_by_artifact[artifact['artifact_id']][role]
                report['semantic'][batch_id][key] = {
                    **summary,
                    'artifacts_available': sum(row['artifact_available'] for row in rows),
                    'unavailable_artifact_ids': [row['artifact_id'] for row in rows if not row['artifact_available']]}
            report['judge_calibration'][batch_id] = {
                'status': 'not_applicable', 'reason': 'No independent human reference in AI-only mode; model agreement is not accuracy.'}
    else:
        for batch in batches:
            if batch.get('review_mode', 'human_blind') != 'human_blind':
                raise ValueError('Historical human-blind report contains a different review mode')
            semantic, calibration = _human_batch_summary(exp, batch, tasks)
            report['semantic'][batch['batch_id']] = semantic
            if calibration is not None:
                report['judge_calibration'][batch['batch_id']] = calibration
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
            executable_ids = {task['id'] for task in tasks.values() if task.get('executable')}
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
             f"Review mode: `{review_mode}`; configured judges: {', '.join(exp.judge_roles)}.",
             f"CLI budget consumed: {report['budget']['calls']} / {report['budget']['max_calls']}; "
             f"{report['budget']['seconds']:.1f} / {report['budget']['max_seconds']} seconds.",
             f"Assignments: {report['assigned']}; stored attempts: {report['attempts']}.", '',
             '| Status | Count |', '|---|---:|']
    lines.extend(f'| {key} | {value} |' for key, value in sorted(report['statuses_including_unstarted'].items()))
    if review_mode == 'ai_only':
        lines += ['', 'AI review coverage (valid supplied reviews / assigned artifacts):', '',
                  '| Batch | Track / arm | Judge | Valid reviews | Complete reviews |', '|---|---|---|---:|---:|']
        for batch_id, groups in report['semantic'].items():
            for group, result in groups.items():
                for role, value in result['by_judge'].items():
                    lines.append(f"| {batch_id} | {group} | {role} | {value['reviews_supplied']}/{value['assigned_artifacts']} | "
                                 f"{value['completed_review_coverage']['numerator']}/{value['assigned_artifacts']} |")
        lines += ['', 'AI-only results contain independent model opinions and fixed-fact status disagreement. '
                  'No human review, human calibration, accuracy, or acceptance is established. '
                  'Free claim lists are not aligned; no majority label is used as truth.']
    else:
        lines += ['', 'Human review progress:', '']
        lines.extend(f"- {b['batch_id']}: initial {b['initial_submitted']}/{b['total']}; final {b['adjudication_submitted']}/{b['total']}; {b['state']}." for b in batches)
        lines += ['', 'Semantic findings remain hidden until the whole initial batch is frozen.']
    lines += ['', 'See summary.json for per-model metrics, assigned denominators, missingness, and provenance.',
              'No human labels have been inferred from AI output. Known model costs are catalog estimates, not verified invoices; unavailable costs remain null.', '']
    (exp.path / 'SUMMARY.md').write_text('\n'.join(lines), encoding='utf-8', newline='\n')
    return {'json': str(target), 'markdown': str(exp.path / 'SUMMARY.md'), 'budget': report['budget'],
            'review_mode': review_mode, 'review_batches': batches, 'human_batches': report['human_batches'],
            'statuses': report['statuses_including_unstarted']}
