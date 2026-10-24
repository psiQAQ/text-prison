"""Offline protocol and subprocess-transport tests; these never call agy models."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from eval import agy_adapter as agy
from eval.budget import Budget, BudgetExceeded
from eval.common import read_json


def encoded(events):
    return ('\n'.join(json.dumps(e, ensure_ascii=False) for e in events) + '\n').encode()


def initial(**changes):
    return {'event': 'init', 'conversation_id': 'one',
            'init': {'cwd': str(Path.cwd()), 'tools': [], 'permission_mode': 'request-review',
                     'agent': 'judge', 'model': 'gemini-4-argon-high', **changes}}


def final(**changes):
    return {'event': 'result', 'result': {'conversation_id': 'one', 'status': 'SUCCESS',
            'response': 'A\u2028B\u2029C', 'num_turns': 1,
            'usage': {'input_tokens': 10418, 'output_tokens': 589, 'thinking_tokens': 551,
                      'cache_read_tokens': 8113, 'total_tokens': 11007}, **changes}}


def step(**changes):
    return {'event': 'step_update', 'step_update': {'conversation_id': 'one',
            'step_index': 1, 'state': 'DONE', 'step_type': 'agent_response',
            'text_delta': 'a partial response', 'usage': {'input_tokens': 10302,
            'output_tokens': 582, 'thinking_tokens': 551, 'cache_read_tokens': 8113,
            'total_tokens': 10884}, **changes}}


def test_authoritative_cumulative_result_is_not_added_to_steps_or_duplicates():
    result = agy.parse_events(encoded([initial(), step(), step(step_type='checkpoint'), final(), final()]))
    assert result['status'] == 'completed'
    assert result['final_text'] == 'A\u2028B\u2029C'
    usage = result['usage']
    assert usage['input_total'] is None
    assert usage['input_reported'] == 10418
    assert usage['output_total'] == 589
    assert usage['input_cached'] == 8113
    assert usage['output_reasoning'] == 551
    assert usage['model_calls'] is None
    assert usage['user_turns'] == 1
    assert usage['input_cache_write'] is None
    assert usage['estimated_cost_usd'] is None


@pytest.mark.parametrize('state', ['ERROR', 'CANCELED', 'INTERRUPTED', 'INVALID', 'WAITING', 'RUNNING'])
def test_exit_zero_does_not_prove_success(state):
    assert agy.parse_events(encoded([initial(), final(status=state)]))['status'] == 'failed'


@pytest.mark.parametrize('changes', [{'tools': [None]}, {'tools': None},
                                    {'permission_mode': 'always-proceed'}, {'model': 'wrong'},
                                    {'agent': 'wrong'}, {'cwd': '/wrong'}])
def test_identity_and_catalog_shape_are_enforced(changes):
    result = agy.parse_events(encoded([initial(**changes), final()]), expected_agent='judge',
                              expected_model='gemini-4-argon-high', expected_cwd=Path.cwd())
    assert result['status'] == 'failed'
    assert result['errors']


def test_init_catalog_is_not_an_execution_allowlist():
    result = agy.parse_events(encoded([initial(tools=['view_file', 'run_command']), final()]))
    assert result['status'] == 'completed'


@pytest.mark.parametrize('raw_tail', [b'{', b'[]\n', b'{"event":"bad","x":NaN}\n',
                                      b'{"event":"result","event":"result"}\n', b'\xff\n',
                                      b'{"event":"bad","text":"\\ud800"}\n'])
def test_malformed_or_truncated_records_cannot_succeed(raw_tail):
    result = agy.parse_events(encoded([initial(), final()]) + raw_tail)
    assert result['status'] == 'failed'
    assert result['usage']['output_total'] is None


def test_missing_result_and_later_activity_are_incomplete():
    for events in ([initial(), step()], [initial(), final(), step()],
                   [initial(), final(), initial()], [final()]):
        assert agy.parse_events(encoded(events))['status'] == 'failed'


def test_different_conversation_or_multiple_turns_are_rejected():
    for events in ([initial(), step(conversation_id='two'), final()],
                   [initial(), final(conversation_id='two')],
                   [initial(), final(), final(num_turns=2)]):
        result = agy.parse_events(encoded(events))
        assert result['status'] == 'failed'
        assert result['usage']['model_calls'] is None


@pytest.mark.parametrize('changes', [{'step_type': 'tool'}, {'tool_name': 'run_command'},
                                    {'tool_info': {'name': 'read_file'}},
                                    {'subagent_info': {'subagents': [{'role': 'researcher'}]}}])
def test_unexpected_tools_and_subagents_invalidate_judgment(changes):
    result = agy.parse_events(encoded([initial(), step(**changes), final()]))
    assert result['status'] == 'failed'
    assert len(result['tool_events']) == 1


@pytest.mark.parametrize('bad', [None, True, -1, 1.2, '42'])
def test_missing_or_invalid_usage_stays_unknown(bad):
    event = final(usage={'input_tokens': bad, 'output_tokens': bad})
    usage = agy.parse_events(encoded([initial(), event]))['usage']
    assert usage['coverage'] == 'unknown'
    assert usage['input_reported'] is None
    assert usage['output_total'] is None
    assert usage['estimated_cost_usd'] is None


def test_timeout_retains_raw_observations_without_claiming_complete_usage():
    result = agy.parse_events(encoded([initial(), final()]), timed_out=True)
    assert result['status'] == 'timeout'
    assert result['usage']['output_total'] is None
    assert result['usage']['observed_usage']['output_total'] == 589


def test_preflight_reads_no_auth_and_accepts_empty_mcp(tmp_path):
    gemini = tmp_path / '.gemini'
    (gemini / 'config').mkdir(parents=True)
    (gemini / 'config' / 'mcp_config.json').write_text('')
    (gemini / 'oauth_creds.json').write_text('not JSON; must never be inspected')
    result = agy.preflight(tmp_path)
    assert result['enabled_mcp_servers'] == 0
    assert result['hook_runtime_verified'] is False


@pytest.mark.parametrize('relative', agy.AMBIENT_PATHS)
def test_preflight_rejects_ambient_customizations(tmp_path, relative):
    path = tmp_path / '.gemini' / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('ambient customization')
    with pytest.raises(ValueError, match='Ambient agy'):
        agy.preflight(tmp_path)


def test_preflight_rejects_enabled_mcp_and_unknown_settings(tmp_path):
    gemini = tmp_path / '.gemini'
    (gemini / 'config').mkdir(parents=True)
    mcp = gemini / 'config' / 'mcp_config.json'
    mcp.write_text('{"mcpServers":{"test":{"command":"unused"}}}')
    with pytest.raises(ValueError, match='Enabled global agy MCP'):
        agy.preflight(tmp_path)
    mcp.write_text('{"mcpServers":{"test":{"disabled":true}}}')
    agy.preflight(tmp_path)
    (gemini / 'antigravity-cli').mkdir()
    settings = gemini / 'antigravity-cli' / 'settings.json'
    settings.write_text('{"trustedWorkspaces":[]}')
    agy.preflight(tmp_path)
    settings.write_text('{"systemPrompt":"ambient"}')
    with pytest.raises(ValueError, match='Unreviewed global agy settings'):
        agy.preflight(tmp_path)


FAKE_TRANSPORT = r'''
import json,sys,time,subprocess
from pathlib import Path
sys.stdin.reconfigure(encoding='utf-8')
mode,model,agent,cwd=sys.argv[1:]
def emit(event):
 print(json.dumps(event),flush=True)
tools=None if mode=='bad-init' else ['view_file', 'run_command']
emit({'event':'init','conversation_id':'one','init':{
 'cwd':cwd,'tools':tools,'permission_mode':'request-review','model':model,'agent':agent}})
line=sys.stdin.readline()
if not line:
 sys.exit(7)
request=json.loads(line)
if sys.stdin.read():
 sys.exit(8)
config=json.loads((Path(cwd)/'.agents'/'hooks.json').read_text())['textprison-no-tools']
common={'conversationId':'one','workspacePaths':[cwd],'modelName':model}
def hook(kind,extra=None):
 entry=config[kind][0]
 if kind=='PreToolUse':
  assert entry['matcher']=='*'
  entry=entry['hooks'][0]
 output=subprocess.run(entry['command'],shell=True,input=json.dumps({**common,**(extra or {})}),
                       capture_output=True,text=True,check=True)
 return json.loads(output.stdout)
if mode!='missing-hooks':
 hook('SessionStart')
 hook('PreInvocation',{'invocationNum':0,'initialNumSteps':1})
if mode=='wait':
 time.sleep(1)
if mode=='tool':
 emit({'event':'step_update','step_update':{'conversation_id':'one','step_index':0,
       'state':'ACTIVE','step_type':'tool','tool_name':'read_file'}})
 time.sleep(.2)
response=request['message']['content']
if mode=='probe':
 denied=hook('PreToolUse',{'stepIdx':1,'toolCall':{'name':'view_file','args':{'AbsolutePath':str(Path(cwd)/'probe-target.txt')}}})
 assert denied['decision']=='deny'
 emit({'event':'step_update','step_update':{'conversation_id':'one','step_index':1,
       'state':'DONE','step_type':'tool','tool_info':{'name':'view_file','error':{'type':'hook_denied','message':denied['reason']}}}})
 response='HOOK_DENIED'
emit({'event':'result','result':{'conversation_id':'one','status':'SUCCESS',
 'response':response,'num_turns':1,
 'usage':{'input_tokens':10,'output_tokens':4,'thinking_tokens':1,'cache_read_tokens':0,'total_tokens':14}}})
'''


def offline_transport(monkeypatch, tmp_path, mode='normal'):
    """Replace only the agy transport endpoint with a local deterministic child."""
    monkeypatch.setattr(agy, 'installation', lambda: {'binary': sys._base_executable,
        'version': None, 'binary_hash': agy.INIT_CATALOG_BINARY_HASH, 'version_source': 'offline fixture'})
    monkeypatch.setattr(agy, 'preflight', lambda: {'init_catalog_observed': False,
        'hook_runtime_verified': False, 'zero_tool_attempts': None})
    original = subprocess.Popen
    children = []
    def launch(command, **kwargs):
        if command[0] == sys._base_executable:
            child = original([sys._base_executable, '-c', FAKE_TRANSPORT, mode,
                              command[command.index('--model') + 1],
                              command[command.index('--agent') + 1], str(kwargs['cwd'])], **kwargs)
            children.append(child)
            return child
        return original(command, **kwargs)
    monkeypatch.setattr(agy.subprocess, 'Popen', launch)
    # Stop only the recorded fixture. Let it exit by EOF to avoid Windows taskkill restrictions.
    def stop(child):
        if child.stdin is not None and not child.stdin.closed:
            child.stdin.close()
        child.wait(timeout=10)
    monkeypatch.setattr(agy, 'stop_owned_process', stop)
    return children


def test_invoke_waits_for_init_then_submits_one_prompt_and_preserves_receipts(monkeypatch, tmp_path):
    children = offline_transport(monkeypatch, tmp_path)
    budget = Budget(tmp_path / 'ledger.sqlite', 2, 10)
    prompt = 'literal @path and $(shell)\nUnicode \u2028 and \u2029' + 'x' * 150000
    result = agy.invoke(job_dir=tmp_path / 'job', role='gemini_argon', prompt=prompt,
                        system_prompt='Only review the supplied content.', budget=budget)
    assert result['status'] == 'completed'
    assert result['final_text'] == prompt
    receipt = result['receipt']
    assert receipt['isolation']['init_catalog_observed'] is True
    assert receipt['isolation']['hook_runtime_verified'] is True
    assert receipt['isolation']['zero_tool_attempts'] is True
    assert receipt['prompt_submitted'] is True
    assert receipt['loaded_adapter_hash'] == agy.LOADED_ADAPTER_HASH
    assert receipt['binary_hash'] == agy.INIT_CATALOG_BINARY_HASH
    assert '--disable-slash-commands' in receipt['command']
    assert '-p' not in receipt['command']
    assert '--dangerously-skip-permissions' not in receipt['command']
    definition = next((tmp_path / 'job' / 'workspace' / '.agents' / 'agents').glob('*.md')).read_text(encoding='utf-8')
    assert '\nexcludeDefaultComponents: true\n' in definition
    assert '\ninheritCustomizations: true\n' in definition
    assert '\ninheritMcp: false\n' in definition
    assert '\n# System Prompt\n' in definition
    assert (tmp_path / 'job' / 'workspace' / '.git' / 'HEAD').is_file()
    assert read_json(tmp_path / 'job' / 'parsed.json')['status'] == 'completed'
    assert budget.snapshot()['pending'] == 0
    assert budget.snapshot()['calls'] == 1
    assert all(child.poll() is not None for child in children)


def test_bad_init_blocks_prompt_before_any_model_request(monkeypatch, tmp_path):
    offline_transport(monkeypatch, tmp_path, 'bad-init')
    budget = Budget(tmp_path / 'ledger.sqlite', 2, 10)
    result = agy.invoke(job_dir=tmp_path / 'job', role='claude_opus', prompt='private packet', budget=budget)
    assert result['status'] == 'failed'
    assert result['receipt']['prompt_submitted'] is False
    assert result['receipt']['isolation']['hook_runtime_verified'] is False
    assert budget.snapshot()['pending'] == 0


def test_failed_process_cleanup_keeps_budget_pending(monkeypatch, tmp_path):
    children = offline_transport(monkeypatch, tmp_path, 'wait')
    def cannot_stop(child):
        raise PermissionError('fixture stop rejected')
    monkeypatch.setattr(agy, 'stop_owned_process', cannot_stop)
    budget = Budget(tmp_path / 'ledger.sqlite', 2, .2)
    try:
        result = agy.invoke(job_dir=tmp_path / 'job', role='gemini_flash', prompt='packet', budget=budget)
        assert result['status'] == 'timeout'
        assert budget.snapshot()['pending'] == 1
        assert 'unconfirmed' in result['receipt']['process_cleanup']
        with pytest.raises(BudgetExceeded):
            budget.claim('next')
    finally:
        for child in children:
            child.wait(timeout=10)


def test_invoke_rejects_tools_and_skills_before_launch(tmp_path):
    budget = Budget(tmp_path / 'ledger.sqlite', 2, 10)
    for extra in ({'tools_config': {}}, {'skill_path': tmp_path}):
        with pytest.raises(ValueError, match='neither tools nor skills'):
            agy.invoke(job_dir=tmp_path / 'job', role='claude_sonnet', prompt='packet', budget=budget, **extra)
    assert budget.snapshot()['calls'] == 0


def test_missing_runtime_hooks_invalidates_an_otherwise_completed_judge(monkeypatch, tmp_path):
    offline_transport(monkeypatch, tmp_path, 'missing-hooks')
    budget = Budget(tmp_path / 'ledger.sqlite', 1, 10)
    result = agy.invoke(job_dir=tmp_path / 'job', role='gemini_argon', prompt='packet', budget=budget)
    assert result['status'] == 'failed'
    assert result['receipt']['isolation']['hook_runtime_verified'] is False
    assert result['receipt']['isolation']['zero_tool_attempts'] is None


def test_negative_probe_requires_actual_hook_denial_and_never_becomes_a_judgment(monkeypatch, tmp_path):
    offline_transport(monkeypatch, tmp_path, 'probe')
    budget = Budget(tmp_path / 'ledger.sqlite', 1, 10)
    result = agy.probe_no_tools(job_dir=tmp_path / 'job', role='gemini_argon', budget=budget)
    assert result['status'] == 'failed'
    assert result['probe_status'] == 'Passed'
    assert result['receipt']['purpose'] == 'boundary_probe'
    assert result['receipt']['isolation']['zero_tool_attempts'] is False
    assert result['hook_audit']['denied_tools'][0]['input']['toolCall']['name'] == 'view_file'
    assert budget.snapshot()['calls'] == 1
    assert budget.snapshot()['pending'] == 0
    assert read_json(tmp_path / 'job' / 'parsed.json')['probe_status'] == 'Passed'


@pytest.mark.parametrize('tool', ['view_file', 'write_to_file', 'run_command', 'read_url_content',
                                'search_web', 'invoke_subagent', 'mcp__unknown', 'future_unknown_tool'])
def test_wildcard_guard_denies_every_tool_without_executing_it(tmp_path, tool):
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    hooks = agy._install_hooks(tmp_path, workspace)
    config = read_json(Path(hooks['config']))['textprison-no-tools']['PreToolUse'][0]
    assert config['matcher'] == '*'
    payload = {'conversationId': 'one', 'workspacePaths': [str(workspace)],
               'toolCall': {'name': tool, 'args': {'untrusted': '$(echo never execute); & whoami'}}}
    proc = subprocess.run([sys.executable, '-I', hooks['script'], hooks['audit'], 'PreToolUse'],
                          input=json.dumps(payload), capture_output=True, text=True, check=True)
    assert json.loads(proc.stdout) == {'decision': 'deny', 'reason': agy.DENY_REASON}
    assert json.loads(Path(hooks['audit']).read_text())['input']['toolCall']['name'] == tool


def test_guard_denies_even_malformed_tool_payload(tmp_path):
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    hooks = agy._install_hooks(tmp_path, workspace)
    proc = subprocess.run([sys.executable, '-I', hooks['script'], hooks['audit'], 'PreToolUse'],
                          input='not JSON', capture_output=True, text=True, check=True)
    assert json.loads(proc.stdout)['decision'] == 'deny'


def test_changed_binary_requires_rechecking_catalog_semantics(monkeypatch, tmp_path):
    monkeypatch.setattr(agy, 'installation', lambda: {'binary_hash': 'changed'})
    monkeypatch.setattr(agy, 'preflight', lambda: {})
    budget = Budget(tmp_path / 'ledger.sqlite', 1, 10)
    with pytest.raises(ValueError, match='Changed agy binary'):
        agy.invoke(job_dir=tmp_path / 'job', role='gemini_argon', prompt='packet', budget=budget)
    assert budget.snapshot()['calls'] == 0
