"""Adapter for the installed Pi CLI's JSONL protocol (verified against Pi 1.4.0)."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import time

from .common import ROOT, digest, now, read_json, write_json
from .budget import Budget
from .contracts import loads_json

MODELS = {'writer': ('openai-codex', 'gpt-6-luna', 'medium'),
          'deepseek': ('deepseek', 'deepseek-flash', 'high'),
          'gpt': ('openai-codex', 'gpt-6-sol', 'high')}
LOADED_ADAPTER_HASH = digest(Path(__file__).read_bytes())


def isolated_settings(agent_dir: Path) -> dict:
    # Pi's no-context-files switch does not suppress these global system prompts.
    unexpected = [name for name in ('SYSTEM.md', 'APPEND_SYSTEM.md') if (agent_dir / name).exists()]
    if unexpected:
        raise ValueError('Ambient Pi system prompt would contaminate isolation: ' + ', '.join(unexpected))
    settings_path = agent_dir / 'settings.json'
    settings = read_json(settings_path) if settings_path.exists() else {}
    retries = settings.get('retry', {}).get('provider', {}).get('maxRetries', 0)
    if type(retries) is not int or retries != 0:
        raise ValueError('Pi provider retries must be zero for measurable single-attempt calls')
    return {'ambient_system_files': [], 'provider_max_retries': retries}


def installation() -> dict:
    agent_dir = Path(os.environ.get('PI_CODING_AGENT_DIR', str(Path.home() / '.pi' / 'agent')))
    launcher = Path(os.environ.get('TEXTPRISON_PI_LAUNCHER', str(agent_dir / 'bin' / 'pi-launcher.js')))
    node = os.environ.get('TEXTPRISON_NODE') or shutil.which('node')
    if not node or not launcher.is_file():
        raise FileNotFoundError('Pi launcher or Node missing; configure TEXTPRISON_PI_LAUNCHER/TEXTPRISON_NODE')
    version = (agent_dir / 'install' / 'current-version').read_text(encoding='utf-8').strip()
    return {'node': str(node), 'launcher': str(launcher), 'agent_dir': str(agent_dir), 'version': version}


def doctor() -> dict:
    info = installation()
    checks = {}
    for role, (provider, model, _) in MODELS.items():
        result = subprocess.run([info['node'], info['launcher'], 'auth', 'check', '--provider', provider,
                                 '--model', model, '--json', '--no-refresh'], capture_output=True, timeout=30)
        try:
            check = json.loads(result.stdout.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            check = {'status': 'invalid', 'reason': 'unparseable_auth_check'}
        checks[role] = {k: check[k] for k in ('status', 'provider', 'reason', 'authType') if k in check}
    return {**info, 'auth': checks, 'inference_tested': False}


def parse_events(raw: bytes, exit_code: int | None = 0, timed_out: bool = False) -> dict:
    events, errors = [], []
    lines = raw.split(b'\n')  # str.splitlines also splits U+2028/U+2029 inside JSON strings.
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            event = loads_json(line.decode('utf-8').removesuffix('\r'))
            if not isinstance(event, dict):
                raise ValueError('record is not an object')
            events.append(event)
        except (ValueError, UnicodeDecodeError) as exc:
            errors.append({'line': index + 1, 'error': type(exc).__name__})
    messages, seen = [], set()
    incomplete_usage = False
    incomplete_calls = False
    compactions, extra_usage = [], []
    tool_events = []
    for event in events:
        if event.get('type') == 'message_end' and event.get('message', {}).get('role') == 'assistant':
            msg = event['message']
            identity = msg.get('responseId') or digest(json.dumps(msg, sort_keys=True, ensure_ascii=False))
            if identity not in seen:
                seen.add(identity)
                messages.append(msg)
        elif event.get('type') == 'compaction_end':
            result = event.get('result')
            if result:
                compactions.append(result)
                if not result.get('usage'):
                    incomplete_usage = True
            else:
                incomplete_usage = True
                incomplete_calls = True
        elif event.get('type') == 'entry_appended' and event.get('entry', {}).get('type') == 'usage':
            entry = event['entry']
            identity = 'usage:' + (entry.get('id') or digest(json.dumps(entry, sort_keys=True)))
            if identity not in seen:
                seen.add(identity)
                extra_usage.append(entry)
                if entry.get('kind') != 'cache_warm':
                    incomplete_usage = True
        elif event.get('type', '').startswith('summarization_retry_'):
            incomplete_usage = True
            incomplete_calls = True
        elif event.get('type', '').startswith('tool_execution_'):
            tool_events.append(event)
    usages = []
    for msg in [*messages, *compactions, *extra_usage]:
        usage = msg.get('usage')
        keys = ('input', 'output', 'cacheRead', 'cacheWrite')
        if not isinstance(usage, dict) or any(type(usage.get(k)) is not int or usage[k] < 0 for k in keys):
            incomplete_usage = True
            continue
        # Pi initializes failed/aborted responses with zero-filled usage, which isn't proof of zero cost.
        if msg.get('stopReason') in ('error', 'aborted') and not usage.get('totalTokens'):
            incomplete_usage = True
            continue
        usages.append(usage)
    meaningful = [e for e in events if e.get('type') in {'message_end', 'agent_start', 'agent_end', 'agent_settled', 'compaction_end'}]
    settled = bool(meaningful and meaningful[-1].get('type') == 'agent_settled')
    aborted = any(e.get('type') == 'agent_settled' and e.get('aborted') for e in events)
    final = messages[-1] if messages else None
    status = 'completed'
    if timed_out:
        status = 'timeout'
    elif errors or exit_code != 0 or not settled or aborted or not final or final.get('stopReason') != 'stop':
        status = 'failed'
    complete = bool(usages) and not incomplete_usage and not errors and settled
    def total(key):
        return sum(u.get(key, 0) for u in usages) if usages else None
    final_text = ''.join(b.get('text', '') for b in (final or {}).get('content', []) if b.get('type') == 'text')
    # Pi's input excludes cache reads/writes; normalized input_total includes all input categories.
    input_total = sum(u['input'] + u['cacheRead'] + u['cacheWrite'] for u in usages) if usages else None
    estimated = sum(u['cost']['total'] for u in usages) if usages and all(type(u.get('cost', {}).get('total')) in (int, float) and math.isfinite(u['cost']['total']) and u['cost']['total'] >= 0 for u in usages) else None
    observed_usage = {'input_total': input_total, 'output_total': total('output'),
                      'input_cached': total('cacheRead'), 'input_cache_write': total('cacheWrite'),
                      'output_reasoning': sum(u['reasoning'] for u in usages) if usages and all(type(u.get('reasoning')) is int and u['reasoning'] >= 0 for u in usages) else None,
                      'estimated_cost_usd': estimated}
    return {'status': status, 'settled': settled, 'errors': errors, 'final_text': final_text,
            'messages': messages, 'tool_events': tool_events,
            'usage': {'coverage': 'complete' if complete else ('partial' if usages else 'unknown'),
                      **{key: value if complete else None for key, value in observed_usage.items()},
                      'observed_usage': observed_usage,
                      'model_calls': len(messages) + len(compactions) + len(extra_usage) if settled and not errors and not incomplete_calls else None,
                      'raw_log': None,
                      'aggregation': 'unique message_end + compaction_end; reasoning is a subset of output',
                      'cost_basis': 'installed Pi catalog estimate, not a verified invoice'}}


def stop_owned_process(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if os.name == 'nt':
        stopped = subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True, timeout=15)
        if stopped.returncode and proc.poll() is None:
            reason = stopped.stderr.decode(errors='replace').strip()
            if 'Access denied' in reason:
                raise PermissionError('taskkill: ' + reason)
            raise OSError('Owned process cleanup failed: ' + reason)
    else:
        proc.kill()
    proc.wait(timeout=15)


def invoke(*, job_dir: Path, role: str, prompt: str, budget: Budget,
           skill_path: Path | None = None, tools_config: dict | None = None,
           system_prompt: str | None = None) -> dict:
    info = installation()
    isolation = isolated_settings(Path(info['agent_dir']))
    provider, model, thinking = MODELS[role]
    job_dir.mkdir(parents=True, exist_ok=False)
    workspace = job_dir / 'workspace'
    workspace.mkdir()
    (workspace / '.pi').mkdir()
    # Project settings apply for this one explicitly trusted fresh workspace, not the user's global defaults.
    write_json(workspace / '.pi' / 'settings.json', {'retry': {'enabled': False}, 'compaction': {'enabled': False}})
    prompt_path = job_dir / 'prompt.txt'
    prompt_path.write_text(prompt, encoding='utf-8', newline='\n')
    command = [info['node'], info['launcher'], '--mode', 'json', '--no-session', '--no-extensions',
               '--no-mcp', '--no-skills', '--no-prompt-templates', '--no-context-files', '--no-themes',
               '--approve', '--offline', '--provider', provider, '--model', model, '--thinking', thinking]
    env = os.environ.copy()
    env['PI_TELEMETRY'] = '0'
    env['PYTHONIOENCODING'] = 'utf-8'
    if tools_config:
        config = {**tools_config, 'workspace': str(workspace), 'job_dir': str(job_dir),
                  'skill_path': str(skill_path) if skill_path else None}
        if config.get('allow_check'):
            contract_path = job_dir / 'contract.json'
            write_json(contract_path, config.pop('contract', {}))
            config['contract_path'] = str(contract_path)
        write_json(job_dir / 'tools.json', config)
        for relative, content in config.get('initial_files', {}).items():
            path = (workspace / relative).resolve()
            if not path.is_relative_to(workspace.resolve()):
                raise ValueError('Invalid initial file path')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8', newline='\n')
        env['TEXTPRISON_TOOL_CONFIG'] = str(job_dir / 'tools.json')
        command += ['--no-builtin-tools', '--extension', str(ROOT / 'eval' / 'pi_tools.ts'),
                    '--tools', 'read,write_artifact' + (',check_artifact' if config.get('allow_check') else '')]
    else:
        command += ['--no-tools']
    if skill_path:
        command += ['--skill', str(skill_path)]
    if system_prompt:
        system_path = job_dir / 'system.txt'
        system_path.write_text(system_prompt, encoding='utf-8', newline='\n')
        command += ['--system-prompt', str(system_path)]
    # File payload avoids Windows command-line length limits and keeps source material out of shell parsing.
    command += ['@' + str(prompt_path)]
    call_id, timeout = budget.claim(job_dir.name)
    started = time.monotonic()
    receipt = {'call_id': call_id, 'host': 'pi', 'host_version': info['version'], 'provider': provider,
               'model': model, 'reasoning_effort': thinking, 'started_at': now(), 'timeout_seconds': timeout,
               'prompt_hash': digest(prompt), 'command': command, 'pid': None}
    receipt['initial_hashes'] = {p.relative_to(workspace).as_posix(): digest(p.read_bytes())
                                for p in workspace.rglob('*') if p.is_file()}
    receipt['adapter_hash'] = digest(Path(__file__).read_bytes())
    receipt['loaded_adapter_hash'] = LOADED_ADAPTER_HASH
    receipt['isolation'] = isolation
    receipt['tool_hashes'] = {name: digest((ROOT / 'eval' / name).read_bytes())
                             for name in ('pi_tools.ts', 'tool_boundary.mjs')}
    write_json(job_dir / 'receipt.json', receipt)
    timed_out = False
    proc = None
    try:
        with (job_dir / 'events.jsonl').open('wb') as stdout, (job_dir / 'stderr.txt').open('wb') as stderr:
            proc = subprocess.Popen(command, cwd=workspace, env=env, stdout=stdout, stderr=stderr,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            receipt['pid'] = proc.pid
            write_json(job_dir / 'receipt.json', receipt)
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                # Only this recorded launcher process tree; never terminate by executable name.
                stop_owned_process(proc)
        result = parse_events((job_dir / 'events.jsonl').read_bytes(), proc.returncode, timed_out)
        result['usage']['raw_log'] = str(job_dir / 'events.jsonl')
        receipt.update({'exit_code': proc.returncode, 'status': result['status']})
    except KeyboardInterrupt:
        receipt['status'] = 'interrupted'
        if proc is not None:
            stop_owned_process(proc)
        raise
    except (OSError, subprocess.SubprocessError) as exc:
        result = {'status': 'failed', 'final_text': '', 'messages': [], 'tool_events': [],
                  'errors': [{'error': type(exc).__name__, 'detail': str(exc)}],
                  'usage': {'coverage': 'unknown', 'input_total': None, 'output_total': None,
                            'raw_log': str(job_dir / 'events.jsonl')}}
        receipt.update({'status': 'failed', 'error': str(exc)})
    finally:
        elapsed = time.monotonic() - started
        status = receipt.get('status', 'interrupted')
        child_alive = proc is not None and proc.poll() is None
        if not child_alive:
            budget.finish(call_id, elapsed, status)
        else:
            receipt['process_cleanup'] = 'unconfirmed; budget remains pending and blocks new calls'
        receipt.update({'elapsed_seconds': elapsed, 'ended_at': now()})
        write_json(job_dir / 'receipt.json', receipt)
    result['receipt'] = receipt
    (job_dir / 'answer.txt').write_text(result['final_text'], encoding='utf-8', newline='\n')
    write_json(job_dir / 'parsed.json', result)
    return result
