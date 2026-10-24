import json
from pathlib import Path
import subprocess
import sys

import pytest

from eval.pi_adapter import parse_events, isolated_settings, stop_owned_process
from eval.budget import Budget, BudgetExceeded


def encoded(events):
    return ('\n'.join(json.dumps(e, ensure_ascii=False) for e in events) + '\n').encode()


def message(**changes):
    return {'role': 'assistant', 'responseId': 'one', 'stopReason': 'stop',
            'content': [{'type': 'text', 'text': 'A\u2028B\u2029C'}],
            'usage': {'input': 10, 'output': 20, 'cacheRead': 3, 'cacheWrite': 4,
                      'reasoning': 12, 'totalTokens': 37, 'cost': {'total': .1}}, **changes}


def test_final_cumulative_usage_and_copies_not_double_counted():
    msg = message()
    events = [{'type': 'message_update', 'usage': msg['usage']},
              {'type': 'message_end', 'message': msg}, {'type': 'message_end', 'message': msg},
              {'type': 'turn_end', 'message': msg}, {'type': 'agent_end', 'messages': [msg]},
              {'type': 'agent_settled', 'aborted': False}]
    result = parse_events(encoded(events))
    assert result['status'] == 'completed'
    assert result['final_text'] == 'A\u2028B\u2029C'
    assert result['usage']['input_total'] == 17
    assert result['usage']['output_total'] == 20
    assert result['usage']['output_reasoning'] == 12
    assert result['usage']['model_calls'] == 1


@pytest.mark.parametrize('stop', ['error', 'aborted', 'length', 'toolUse'])
def test_exit_zero_is_not_proof_of_success(stop):
    result = parse_events(encoded([{'type': 'message_end', 'message': message(stopReason=stop)},
                                   {'type': 'agent_settled', 'aborted': False}]))
    assert result['status'] == 'failed'


def test_truncated_missing_usage_remains_unknown():
    raw = encoded([{'type': 'message_end', 'message': message(usage=None)}]) + b'{'
    result = parse_events(raw)
    assert result['status'] == 'failed'
    assert result['usage']['coverage'] == 'unknown'
    assert result['usage']['input_total'] is None


def test_agent_end_is_not_settled():
    result = parse_events(encoded([{'type': 'message_end', 'message': message()}, {'type': 'agent_end'}]))
    assert result['status'] == 'failed'
    assert result['usage']['coverage'] == 'partial'


def test_retry_error_zero_is_not_zero_cost():
    failed = message(responseId='failed', stopReason='error', usage={'input': 0, 'output': 0, 'cacheRead': 0, 'cacheWrite': 0, 'totalTokens': 0})
    result = parse_events(encoded([{'type': 'message_end', 'message': failed},
                                   {'type': 'message_end', 'message': message()}, {'type': 'agent_settled'}]))
    assert result['status'] == 'completed'
    assert result['usage']['coverage'] == 'partial'
    assert result['usage']['model_calls'] == 2
    assert result['usage']['input_total'] is None
    assert result['usage']['observed_usage']['input_total'] == 17


def test_cache_warm_and_missing_compaction_usage():
    usage = message()['usage']
    entry = {'type': 'entry_appended', 'entry': {'type': 'usage', 'id': 'cache-one', 'kind': 'cache_warm', 'usage': usage}}
    events = [entry, entry, {'type': 'message_end', 'message': message()}, {'type': 'agent_settled'}]
    parsed = parse_events(encoded(events))
    assert parsed['usage']['input_total'] == 34
    assert parsed['usage']['model_calls'] == 2
    events.insert(-1, {'type': 'compaction_end', 'errorMessage': 'network error', 'aborted': False})
    parsed = parse_events(encoded(events))
    assert parsed['usage']['coverage'] == 'partial'
    assert parsed['usage']['input_total'] is None
    assert parsed['usage']['model_calls'] is None


def test_ambient_context_and_provider_retries_rejected(tmp_path):
    assert isolated_settings(tmp_path)['provider_max_retries'] == 0
    (tmp_path / 'settings.json').write_text('{"retry":{"provider":{"maxRetries":2}}}')
    with pytest.raises(ValueError, match='provider retries'):
        isolated_settings(tmp_path)
    (tmp_path / 'settings.json').write_text('{}')
    (tmp_path / 'APPEND_SYSTEM.md').write_text('extra instructions')
    with pytest.raises(ValueError, match='system prompt'):
        isolated_settings(tmp_path)


def test_new_agent_after_settled_is_incomplete():
    parsed = parse_events(encoded([{'type': 'message_end', 'message': message()},
                                   {'type': 'agent_settled'}, {'type': 'agent_start'}]))
    assert parsed['status'] == 'failed'


@pytest.mark.parametrize('bad', [True, float('inf'), -1, 1.2])
def test_invalid_usage_is_unknown(bad):
    msg = message()
    msg['usage']['input'] = bad
    parsed = parse_events(encoded([{'type': 'message_end', 'message': msg}, {'type': 'agent_settled'}]))
    assert parsed['usage']['input_total'] is None


def test_only_owned_sleeping_child_is_stopped():
    proc = subprocess.Popen([sys._base_executable, '-c', 'import time; time.sleep(5)'])
    try:
        stop_owned_process(proc)
    except PermissionError as exc:
        proc.wait(timeout=10)
        pytest.skip(f'This sandbox denies process-tree termination: {exc}')
    assert proc.poll() is not None
    stop_owned_process(proc)  # Already-exited handles must not target a reused PID.


def test_budget_persists_failures_limits_and_time(tmp_path):
    ledger = tmp_path / 'budget.sqlite'
    budget = Budget(ledger, 2, 20)
    first, timeout = budget.claim('first', 15)
    assert timeout == 15
    with pytest.raises(BudgetExceeded):
        budget.claim('overlap')
    budget.finish(first, 13, 'failed')
    second, timeout = Budget(ledger, 2, 20).claim('retry', 15)
    assert timeout == 7
    budget.finish(second, 7, 'timeout')
    with pytest.raises(BudgetExceeded):
        budget.claim('third')
    assert budget.snapshot()['seconds'] == 20
    with pytest.raises(ValueError):
        Budget(ledger, 3, 20)


def test_interrupted_conservatively_charged(tmp_path):
    budget = Budget(tmp_path / 'budget.sqlite', 2, 10)
    first, _ = budget.claim('interrupted', 6)
    budget.recover_interrupted(first)
    assert budget.snapshot()['seconds'] == 6
    _, timeout = budget.claim('resume')
    assert timeout == 4
