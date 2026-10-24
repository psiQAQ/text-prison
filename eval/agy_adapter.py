"""Tool-free judges over agy's documented bidirectional headless JSONL protocol.

Protocol: https://antigravity.google/docs/cli/headless/
Agent and ambient configuration: /docs/subagents/, /docs/rules/, /docs/skills/,
/docs/mcp/, and /docs/hooks/. Real compatibility requires the recorded smoke run.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import threading
import time
import uuid

from .budget import Budget
from .common import digest, now, write_json
from .contracts import loads_json
from .pi_adapter import stop_owned_process

MODELS = {
    'gemini_argon': ('google', 'gemini-4-argon-high', 'high'),
    'gemini_flash': ('google', 'gemini-3.8-flash-high', 'high'),
    'claude_opus': ('anthropic', 'claude-opus-5-5-high', 'high'),
    'claude_sonnet': ('anthropic', 'claude-sonnet-5-5-high', 'high'),
}
LOADED_ADAPTER_HASH = digest(Path(__file__).read_bytes())
DENY_REASON = 'TEXTPRISON_NO_TOOLS: all model tool execution is denied'
# This executable's init payload advertises a global build catalog, not the
# selected agent's tool allowlist. Recheck a changed binary before relying on it.
INIT_CATALOG_BINARY_HASH = '22588b6d5a6f6d2d66091c73dfb9255edc7bdafe9aff9dd20d958ce116496695'
HOOK_SCRIPT = r'''"""Job-local agy hook. It never executes a requested tool."""
import json
from pathlib import Path
import sys
import time

audit_path, kind = sys.argv[1:]
reason = 'TEXTPRISON_NO_TOOLS: all model tool execution is denied'
try:
    payload = json.loads(sys.stdin.buffer.read().decode('utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('hook input is not an object')
    invalid = None
except (ValueError, UnicodeError) as exc:
    payload, invalid = {}, type(exc).__name__
record = {'event': kind, 'recorded_at': time.time(), 'input': payload,
          'input_error': invalid, 'decision': 'deny' if kind == 'PreToolUse' else None}
try:
    with Path(audit_path).open('ab') as stream:
        stream.write((json.dumps(record, ensure_ascii=True, allow_nan=False) + '\n').encode('ascii'))
        stream.flush()
except OSError as exc:
    print('TEXTPRISON_HOOK_AUDIT_FAILED: ' + type(exc).__name__, file=sys.stderr)
    if kind != 'PreToolUse':
        raise SystemExit(1)
# A malformed tool input or unavailable audit destination still receives deny.
print(json.dumps({'decision': 'deny', 'reason': reason} if kind == 'PreToolUse' else {}), flush=True)
'''
AMBIENT_PATHS = (
    'AGENTS.md', 'GEMINI.md', 'config/AGENTS.md', 'config/GEMINI.md',
    'config/rules', 'config/rules.json', 'config/skills', 'config/plugins',
    'config/agents', 'config/hooks.json', 'antigravity-cli/AGENTS.md',
    'antigravity-cli/GEMINI.md', 'antigravity-cli/rules',
    'antigravity-cli/rules.json', 'antigravity-cli/skills',
    'antigravity-cli/plugins', 'antigravity-cli/hooks.json',
    'antigravity/skills',
)


def installation() -> dict:
    configured = os.environ.get('TEXTPRISON_AGY_BINARY')
    local = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local')))
    candidate = configured or shutil.which('agy') or str(local / 'agy' / 'bin' / 'agy.exe')
    binary = Path(candidate).resolve()
    if not binary.is_file():
        raise FileNotFoundError('agy missing; configure TEXTPRISON_AGY_BINARY')
    with binary.open('rb') as stream:
        binary_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    # This build exposes neither a product version flag nor populated PE version fields.
    # A binary hash identifies the actual executable without inventing a release number.
    return {'binary': str(binary), 'version': None, 'binary_hash': binary_hash,
            'version_source': 'product version unavailable; executable SHA256 recorded'}


def preflight(home: Path | None = None) -> dict:
    """Reject ambient customizations without editing globals or reading auth files."""
    base = (home or Path.home()) / '.gemini'
    unexpected = []
    for path in (base, base / 'config', base / 'antigravity-cli',
                 base / 'config' / 'mcp_config.json', base / 'antigravity-cli' / 'settings.json'):
        if path.is_symlink() or path.is_junction():
            raise ValueError('Linked agy configuration cannot establish isolation: ' + str(path))
    for name in AMBIENT_PATHS:
        path = base / name
        if path.is_symlink() or path.is_junction() or path.exists():
            unexpected.append(name)
    if unexpected:
        raise ValueError('Ambient agy customizations would contaminate isolation: ' + ', '.join(unexpected))
    settings_path = base / 'antigravity-cli' / 'settings.json'
    settings_raw = settings_path.read_bytes() if settings_path.exists() else b''
    settings = loads_json(settings_raw.decode('utf-8-sig')) if settings_raw.strip() else {}
    if not isinstance(settings, dict) or set(settings) - {'trustedWorkspaces'}:
        raise ValueError('Unreviewed global agy settings; only trustedWorkspaces is allowed')
    mcp_path = base / 'config' / 'mcp_config.json'
    mcp_raw = mcp_path.read_bytes() if mcp_path.exists() else b''
    mcp = loads_json(mcp_raw.decode('utf-8-sig')) if mcp_raw.strip() else {}
    if not isinstance(mcp, dict) or set(mcp) - {'mcpServers'}:
        raise ValueError('Unreviewed global agy MCP configuration')
    servers = mcp.get('mcpServers', {})
    if not isinstance(servers, dict) or any(not isinstance(s, dict) or s.get('disabled') is not True
                                            for s in servers.values()):
        raise ValueError('Enabled global agy MCP servers would contaminate isolation')
    return {'ambient_customizations': [], 'settings_keys': sorted(settings),
            'settings_hash': digest(settings_raw), 'mcp_config_hash': digest(mcp_raw),
            'enabled_mcp_servers': 0, 'scope': 'documented global customization locations',
            'init_catalog_observed': False, 'hook_runtime_verified': False,
            'zero_tool_attempts': None}


def doctor() -> dict:
    return {**installation(), 'isolation': preflight(), 'inference_tested': False}


def _init_errors(event: dict, *, model: str | None = None, agent: str | None = None,
                 cwd: Path | None = None) -> list[str]:
    if event.get('event') != 'init' or not isinstance(event.get('init'), dict):
        return ['first event is not init']
    config = event['init']
    errors = []
    if not isinstance(event.get('conversation_id'), str) or not event['conversation_id']:
        errors.append('init conversation_id is missing')
    if not isinstance(config.get('tools'), list) or any(not isinstance(t, str) for t in config['tools']):
        errors.append('init tools catalog must be a string list')
    if config.get('permission_mode') != 'request-review':
        errors.append('unexpected permission_mode')
    if model is not None and config.get('model') != model:
        errors.append('init model mismatch')
    if agent is not None and config.get('agent') != agent:
        errors.append('init agent mismatch')
    if cwd is not None:
        observed = config.get('cwd')
        if not isinstance(observed, str) or not observed or Path(observed).resolve() != cwd.resolve():
            errors.append('init cwd mismatch')
    return errors


def _tool_event(event: dict) -> bool:
    step = event.get('step_update')
    return isinstance(step, dict) and (step.get('step_type') == 'tool' or bool(step.get('tool_name'))
                                      or bool(step.get('tool_info')) or bool(step.get('subagent_info')))


def _counter(usage: dict, name: str) -> int | None:
    value = usage.get(name)
    return value if type(value) is int and value >= 0 else None


def _decode_event(line: bytes) -> dict:
    event = loads_json(line.decode('utf-8').removesuffix('\r'))
    if not isinstance(event, dict):
        raise ValueError('record is not an object')
    # Reject escaped, unpaired surrogates before persisting UTF-8 parsed records.
    json.dumps(event, ensure_ascii=False, allow_nan=False).encode('utf-8')
    return event


def parse_events(raw: bytes, exit_code: int | None = 0, timed_out: bool = False, *,
                 expected_model: str | None = None, expected_agent: str | None = None,
                 expected_cwd: Path | None = None) -> dict:
    events, errors = [], []
    for index, line in enumerate(raw.split(b'\n')):
        if not line.strip():
            continue
        try:
            events.append(_decode_event(line))
        except (ValueError, UnicodeDecodeError) as exc:
            errors.append({'line': index + 1, 'error': type(exc).__name__})
    initial = events[0] if events else {}
    errors += [{'error': 'isolation', 'detail': detail} for detail in
               _init_errors(initial, model=expected_model, agent=expected_agent, cwd=expected_cwd)]
    conversation = initial.get('conversation_id')
    results, steps, tool_events = [], [], []
    ended = False
    for index, event in enumerate(events):
        kind = event.get('event')
        if index == 0 and kind == 'init':
            continue
        if kind == 'result' and isinstance(event.get('result'), dict):
            result = event['result']
            if result.get('conversation_id') != conversation:
                errors.append({'error': 'conversation_mismatch'})
            if results and result != results[-1]:
                errors.append({'error': 'multiple_results_for_one_prompt'})
            results.append(result)
            ended = True
        elif kind == 'step_update' and isinstance(event.get('step_update'), dict):
            step = event['step_update']
            steps.append(step)
            if ended:
                errors.append({'error': 'step_after_result'})
            if step.get('conversation_id') != conversation:
                errors.append({'error': 'conversation_mismatch'})
            if _tool_event(event):
                tool_events.append(event)
                errors.append({'error': 'tool_or_subagent_forbidden'})
        else:
            errors.append({'error': 'unexpected_event', 'event_index': index})
    final = results[-1] if results else {}
    response = final.get('response')
    final_text = response if isinstance(response, str) else ''
    if final and (type(final.get('num_turns')) is not int or final['num_turns'] != 1):
        errors.append({'error': 'expected_exactly_one_user_turn'})
    settled = bool(final and events[-1].get('event') == 'result'
                   and final.get('status') in {'SUCCESS', 'ERROR', 'CANCELED', 'INTERRUPTED', 'INVALID'})
    status = 'timeout' if timed_out else ('completed' if exit_code == 0 and settled and not errors
                                         and final.get('status') == 'SUCCESS' and isinstance(response, str)
                                         and not final.get('error') else 'failed')
    raw_usage = final.get('usage') if isinstance(final.get('usage'), dict) else {}
    reported = {name: _counter(raw_usage, name) for name in
                ('input_tokens', 'output_tokens', 'thinking_tokens', 'cache_read_tokens', 'total_tokens')}
    trusted_usage = settled and not errors and exit_code == 0 and not timed_out
    # result.usage is cumulative and includes checkpoint steps. Never sum it with
    # step usage or earlier results. The docs do not define cached-input inclusion.
    observed = {'input_total': None, 'input_reported': reported['input_tokens'],
                'output_total': reported['output_tokens'], 'input_cached': reported['cache_read_tokens'],
                'input_cache_write': None, 'output_reasoning': reported['thinking_tokens'],
                'total_reported': reported['total_tokens'], 'estimated_cost_usd': None}
    usage = {'coverage': 'partial' if any(v is not None for v in reported.values()) else 'unknown',
             **{k: v if trusted_usage else None for k, v in observed.items()},
             'observed_usage': observed, 'reported_result_usage': raw_usage or None,
             'model_calls': None, 'user_turns': final.get('num_turns'), 'raw_log': None,
             'aggregation': 'last result.usage only; cumulative session counters',
             'input_semantics': 'cache inclusion unverified; input_total remains unknown',
             'cost_basis': 'not supplied by agy; no invoice or catalog estimate',
             'model_calls_basis': 'num_turns counts user turns; model requests are not reported'}
    messages = [{'role': 'assistant', 'content': [{'type': 'text', 'text': final_text}],
                 'usage': raw_usage or None}] if isinstance(response, str) else []
    return {'status': status, 'settled': settled, 'errors': errors, 'final_text': final_text,
            'messages': messages, 'tool_events': tool_events, 'usage': usage,
            'init': initial.get('init'), 'steps': steps, 'raw_result': final or None}


def _fresh_workspace(workspace: Path) -> None:
    workspace.mkdir()
    git = shutil.which('git')
    if not git:
        raise FileNotFoundError('Git is required to establish the isolated agy workspace boundary')
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env['PYTHONIOENCODING'] = 'utf-8'
    env.update({'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull})
    subprocess.run([git, 'init', '--quiet', '--template=', '--initial-branch=textprison', str(workspace)],
                   env=env, capture_output=True, check=True, timeout=30,
                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)


def _install_hooks(job_dir: Path, workspace: Path) -> dict:
    script, audit = job_dir / 'hook_guard.py', job_dir / 'hook-audit.jsonl'
    script.write_text(HOOK_SCRIPT, encoding='utf-8', newline='\n')
    def handler(kind):
        args = [sys.executable, '-I', str(script), str(audit), kind]
        command = subprocess.list2cmdline(args) if os.name == 'nt' else shlex.join(args)
        return {'type': 'command', 'command': command, 'timeout': 10}
    config = {'textprison-no-tools': {
        'SessionStart': [handler('SessionStart')],
        'PreInvocation': [handler('PreInvocation')],
        'PreToolUse': [{'matcher': '*', 'hooks': [handler('PreToolUse')]}],
    }}
    path = workspace / '.agents' / 'hooks.json'
    write_json(path, config)
    return {'script': str(script), 'script_hash': digest(script.read_bytes()),
            'config': str(path), 'config_hash': digest(path.read_bytes()), 'audit': str(audit)}


def _read_hook_audit(hooks: dict, conversation: str | None, workspace: Path) -> dict:
    records, errors = [], []
    path = Path(hooks['audit'])
    for line in (path.read_bytes() if path.exists() else b'').split(b'\n'):
        if not line.strip():
            continue
        try:
            record = _decode_event(line)
            data = record.get('input')
            if record.get('event') not in {'SessionStart', 'PreInvocation', 'PreToolUse'} or not isinstance(data, dict):
                raise ValueError('unknown hook record')
            if record.get('input_error') or data.get('conversationId') != conversation:
                raise ValueError('hook input or conversation mismatch')
            paths = data.get('workspacePaths')
            if not isinstance(paths, list) or not paths or any(not isinstance(p, str) or Path(p).resolve() != workspace for p in paths):
                raise ValueError('hook workspace mismatch')
            if record['event'] == 'PreToolUse' and record.get('decision') != 'deny':
                raise ValueError('tool hook did not deny')
            records.append(record)
        except (ValueError, UnicodeError, OSError) as exc:
            errors.append(str(exc))
    for key in ('script', 'config'):
        if not Path(hooks[key]).is_file() or digest(Path(hooks[key]).read_bytes()) != hooks[key + '_hash']:
            errors.append('hook ' + key + ' changed')
    starts = sum(r['event'] == 'SessionStart' for r in records)
    invocations = sum(r['event'] == 'PreInvocation' for r in records)
    if starts != 1 or invocations < 1:
        errors.append('SessionStart or PreInvocation hook audit missing')
    return {'runtime_verified': not errors, 'errors': errors, 'records': records,
            'session_starts': starts, 'pre_invocations': invocations,
            'denied_tools': [r for r in records if r['event'] == 'PreToolUse']}


def invoke(*, job_dir: Path, role: str, prompt: str, budget: Budget,
           skill_path: Path | None = None, tools_config: dict | None = None,
           system_prompt: str | None = None) -> dict:
    if skill_path is not None or tools_config is not None:
        raise ValueError('agy judges accept neither tools nor skills')
    return _invoke(job_dir=job_dir, role=role, prompt=prompt, budget=budget, system_prompt=system_prompt)


def probe_no_tools(*, job_dir: Path, role: str, budget: Budget) -> dict:
    """Budgeted real negative probe; requests only a synthetic local file read.

    Ordinary judgment status remains failed on any tool attempt. Check the
    separate probe_status and evidence instead; this is never a review label.
    """
    return _invoke(job_dir=job_dir, role=role, prompt='', budget=budget, probe=True)


def _invoke(*, job_dir: Path, role: str, prompt: str, budget: Budget,
            system_prompt: str | None = None, probe: bool = False) -> dict:
    provider, model, effort = MODELS[role]
    info, isolation = installation(), preflight()
    if info['binary_hash'] != INIT_CATALOG_BINARY_HASH:
        raise ValueError('Changed agy binary requires a fresh init-catalog and hook compatibility check')
    job_dir = job_dir.resolve()
    job_dir.mkdir(parents=True, exist_ok=False)
    workspace = job_dir / 'workspace'
    _fresh_workspace(workspace)
    system = system_prompt if system_prompt is not None else 'Evaluate only the supplied review packet. Use no tools.'
    probe_target, probe_content = None, None
    if probe:
        probe_target = workspace / 'probe-target.txt'
        probe_content = 'SYNTHETIC_BOUNDARY_MARKER_' + uuid.uuid4().hex
        probe_target.write_text(probe_content, encoding='utf-8')
        system = 'Perform the supplied local tool-boundary test. Call view_file exactly once, then report its result. If denied, stop without retries or other tools.'
        prompt = 'Use view_file once to read ' + str(probe_target) + '. If the tool is denied, reply exactly HOOK_DENIED. Do not access any other file or network resource.'
    agent = 'textprison-judge-' + digest(system)[:12]
    # CLI v1.2.1 added excludeDefaultComponents; tools: [] alone retains built-ins.
    # https://antigravity.google/docs/changelog?tab=cli
    definition = ('---\nname: ' + agent + '\ndescription: Isolated TextPrison packet judge\n'
                  'mainAgent: true\nsubagent: false\nmodel: inherit\ntools: ' + ('[view_file]' if probe else '[]') + '\n'
                  'excludeDefaultComponents: true\ninheritCustomizations: true\ninheritMcp: false\n'
                  'commandExecutionPolicy: "off"\nmcpServers: []\nskills: []\nplugins: []\n'
                  '---\n\n# System Prompt\n\n' + system + '\n')
    agent_path = workspace / '.agents' / 'agents' / (agent + '.md')
    agent_path.parent.mkdir(parents=True)
    agent_path.write_text(definition, encoding='utf-8', newline='\n')
    hooks = _install_hooks(job_dir, workspace)
    (job_dir / 'prompt.txt').write_text(prompt, encoding='utf-8', newline='\n')
    (job_dir / 'system.txt').write_text(system, encoding='utf-8', newline='\n')
    call_id, timeout = budget.claim(job_dir.name)
    started = time.monotonic()
    command = [info['binary'], '--input-format', 'stream-json', '--output-format', 'stream-json',
               '--model', model, '--effort', effort, '--agent', agent, '--disable-slash-commands',
               '--print-timeout', str(timeout) + 's', '--log-file', str(job_dir / 'cli.log')]
    receipt = {'call_id': call_id, 'host': 'agy', 'host_version': info['version'],
               'host_version_source': info['version_source'], 'binary_hash': info['binary_hash'],
               'provider': provider, 'model': model, 'reasoning_effort': effort,
               'started_at': now(), 'timeout_seconds': timeout, 'prompt_hash': digest(prompt),
               'system_hash': digest(system), 'agent_definition_hash': digest(definition),
               'command': command, 'pid': None, 'prompt_submitted': False,
               'adapter_hash': digest(Path(__file__).read_bytes()), 'loaded_adapter_hash': LOADED_ADAPTER_HASH,
               'purpose': 'boundary_probe' if probe else 'judge', 'hooks': hooks,
               'isolation': {**isolation, 'workspace_git_boundary': True, 'agent': agent,
                             'customization_inheritance': 'enabled for job-local hooks; ambient preflight required',
                             'init_catalog_basis': 'installed-binary static inspection; not an execution allowlist'}}
    write_json(job_dir / 'receipt.json', receipt)
    events_path = job_dir / 'events.jsonl'
    proc, writer = None, None
    timed_out, transport_errors, writer_errors = False, [], []
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env['PYTHONIOENCODING'] = 'utf-8'
    try:
        with events_path.open('wb') as stdout, (job_dir / 'stderr.txt').open('wb') as stderr:
            proc = subprocess.Popen(command, cwd=workspace, env=env, stdin=subprocess.PIPE,
                                    stdout=stdout, stderr=stderr,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            receipt['pid'] = proc.pid
            write_json(job_dir / 'receipt.json', receipt)
            initialized, pending = False, b''
            with events_path.open('rb') as reader:
                while True:
                    pending += reader.read(65536)
                    while b'\n' in pending:
                        line, pending = pending.split(b'\n', 1)
                        if not line.strip():
                            continue
                        event = _decode_event(line)
                        if not initialized:
                            problems = _init_errors(event, model=model, agent=agent, cwd=workspace)
                            if problems:
                                raise ValueError('; '.join(problems))
                            receipt['isolation'].update({'init_catalog_observed': True, 'init': event})
                            initialized = True
                        elif not receipt['prompt_submitted']:
                            raise ValueError('agy emitted activity before the prompt was submitted')
                        elif _tool_event(event) and not probe:
                            raise ValueError('agy judge attempted a tool or subagent')
                    if initialized and not receipt['prompt_submitted']:
                        if pending.strip():
                            raise ValueError('agy emitted partial activity before prompt submission')
                        write_json(job_dir / 'receipt.json', receipt)
                        payload = (json.dumps({'event': 'user', 'message': {'content': prompt}},
                                              ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
                        def send_prompt():
                            try:
                                proc.stdin.write(payload)
                                proc.stdin.close()
                            except OSError as exc:
                                writer_errors.append(exc)
                        writer = threading.Thread(target=send_prompt, daemon=True)
                        receipt.update({'prompt_submitted': True, 'prompt_submitted_at': now()})
                        writer.start()
                        write_json(job_dir / 'receipt.json', receipt)
                    if writer_errors:
                        raise writer_errors[0]
                    if proc.poll() is not None:
                        break
                    if time.monotonic() - started >= timeout:
                        timed_out = True
                        stop_owned_process(proc)
                        break
                    time.sleep(.025)
            if writer is not None:
                writer.join(timeout=5)
            if writer_errors:
                raise writer_errors[0]
    except KeyboardInterrupt:
        receipt['status'] = 'interrupted'
        if proc is not None:
            stop_owned_process(proc)
        raise
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        transport_errors.append({'error': type(exc).__name__, 'detail': str(exc)})
        if proc is not None and proc.poll() is None:
            try:
                stop_owned_process(proc)
            except (OSError, subprocess.SubprocessError) as cleanup:
                transport_errors.append({'error': type(cleanup).__name__, 'detail': str(cleanup)})
    finally:
        if writer is not None and proc is not None and proc.poll() is not None:
            writer.join(timeout=5)
        raw = events_path.read_bytes() if events_path.exists() else b''
        result = parse_events(raw, proc.returncode if proc else None, timed_out,
                              expected_model=model, expected_agent=agent, expected_cwd=workspace)
        try:
            audit = _read_hook_audit(hooks, receipt['isolation'].get('init', {}).get('conversation_id'), workspace)
        except OSError as exc:
            audit = {'runtime_verified': False, 'errors': [str(exc)], 'records': [],
                     'session_starts': 0, 'pre_invocations': 0, 'denied_tools': []}
        result['hook_audit'] = audit
        attempts = bool(result['tool_events'] or audit['denied_tools'])
        receipt['isolation'].update({'hook_runtime_verified': audit['runtime_verified'],
                                    'zero_tool_attempts': False if attempts else (True if audit['runtime_verified'] else None)})
        if not audit['runtime_verified'] or audit['denied_tools']:
            result['errors'].append({'error': 'hook_boundary', 'detail': audit['errors'],
                                     'denied_tool_count': len(audit['denied_tools'])})
            result['status'] = 'timeout' if timed_out else 'failed'
        if transport_errors:
            result['errors'] += transport_errors
            result['status'] = 'timeout' if timed_out else 'failed'
        if receipt.get('status') == 'interrupted':
            result['status'] = 'interrupted'
        if probe:
            calls = [r['input'].get('toolCall', {}) for r in audit['denied_tools']]
            own_file_only = bool(calls) and all(
                c.get('name') == 'view_file' and isinstance(c.get('args'), dict)
                and c['args'].get('AbsolutePath') == str(probe_target) for c in calls)
            unexpected = [e for e in result['errors'] if e['error'] not in {'tool_or_subagent_forbidden', 'hook_boundary'}]
            proof = {'hook_runtime_verified': audit['runtime_verified'], 'own_synthetic_file_only': own_file_only,
                     'deny_reason_in_stream': DENY_REASON.encode() in raw,
                     'marker_absent_from_stream': probe_content.encode() not in raw,
                     'synthetic_file_unchanged': probe_target.is_file() and probe_target.read_text(encoding='utf-8') == probe_content,
                     'tool_attempt_observed': bool(result['tool_events']),
                     'terminal_success': result['settled'] and result['raw_result'].get('status') == 'SUCCESS'
                                         and proc is not None and proc.returncode == 0 and not timed_out,
                     'no_other_protocol_errors': not unexpected}
            result['probe_status'] = 'Passed' if all(proof.values()) else 'Failed'
            result['probe_evidence'] = proof
            receipt['probe_status'] = result['probe_status']
        result['usage']['raw_log'] = str(events_path)
        receipt.update({'exit_code': proc.returncode if proc else None,
                        'status': receipt.get('status', result['status']),
                        'elapsed_seconds': time.monotonic() - started, 'ended_at': now()})
        if proc is None or proc.poll() is not None:
            budget.finish(call_id, receipt['elapsed_seconds'], receipt['status'])
        else:
            receipt['process_cleanup'] = 'unconfirmed; budget remains pending and blocks new calls'
        write_json(job_dir / 'receipt.json', receipt)
        result['receipt'] = receipt
        (job_dir / 'answer.txt').write_text(result['final_text'], encoding='utf-8', newline='\n')
        write_json(job_dir / 'parsed.json', result)
    return result
