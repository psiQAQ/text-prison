import json
import errno
import os
from pathlib import Path
import shutil
import subprocess

import pytest


def test_real_node_boundary_rejects_escape_and_limits_writes(tmp_path):
    node = shutil.which('node')
    assert node, 'Node is required for the Pi adapter'
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    source = workspace / 'source.txt'
    source.write_text('input', encoding='utf-8')
    outside = tmp_path / 'hidden.txt'
    outside.write_text('answer', encoding='utf-8')
    module = (Path(__file__).resolve().parents[1] / 'eval/tool_boundary.mjs').as_uri()
    code = '''
import {makeBoundary} from MODULE;
const b = makeBoundary(CONFIG);
function rejected(fn) { try {fn(); return false;} catch {return true;} }
const output = [b.read('source.txt'), rejected(()=>b.read('../hidden.txt')),
 rejected(()=>b.write('source.txt','changed')), b.write('answer.md','draft'),
 rejected(()=>b.write('answer.md','extra')), rejected(()=>b.check('answer.md'))];
process.stdout.write(JSON.stringify(output));
'''.replace('MODULE', json.dumps(module)).replace('CONFIG', json.dumps({
        'workspace': str(workspace), 'job_dir': str(tmp_path), 'writable_paths': ['answer.md'], 'max_writes': 1,
        'allow_check': False}))
    result = subprocess.run([node, '--input-type=module', '-'], input=code, text=True,
                            capture_output=True, check=True, encoding='utf-8')
    output = json.loads(result.stdout)
    assert output[0] == 'input'
    assert output[1:3] == [True, True]
    assert output[4:] == [True, True]
    assert source.read_text() == 'input'
    assert outside.read_text() == 'answer'


def path_access(workspace, job_dir, relative):
    node = shutil.which('node')
    assert node, 'Node is required for the Pi adapter'
    module = (Path(__file__).resolve().parents[1] / 'eval/tool_boundary.mjs').as_uri()
    config = {'workspace': str(workspace), 'job_dir': str(job_dir),
              'writable_paths': [relative], 'max_writes': 1, 'allow_check': False}
    code = '''
import {makeBoundary, resolveAllowed} from MODULE;
const config = CONFIG;
const name = NAME;
const boundary = makeBoundary(config);
function capture(fn) {
  try { return {ok: true, value: fn()}; }
  catch (error) { return {ok: false, message: error.message}; }
}
process.stdout.write(JSON.stringify({
  resolve: capture(() => resolveAllowed(name, config.workspace, [config.workspace], false)),
  write: capture(() => boundary.write(name, 'must stay inside')),
}));
'''.replace('MODULE', json.dumps(module)).replace('CONFIG', json.dumps(config)).replace('NAME', json.dumps(relative))
    result = subprocess.run([node, '--input-type=module', '-'], input=code, text=True,
                            capture_output=True, check=True, encoding='utf-8')
    return json.loads(result.stdout)


def assert_link_rejected(attempts):
    for operation in ('resolve', 'write'):
        assert attempts[operation]['ok'] is False, attempts
        assert 'Symlink/junction access is not allowed' in attempts[operation]['message']


def test_new_nested_output_remains_writable(tmp_path):
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    attempts = path_access(workspace, tmp_path, 'nested/answer.md')
    assert attempts['resolve']['ok'] and attempts['write']['ok'], attempts
    assert (workspace / 'nested/answer.md').read_text(encoding='utf-8') == 'must stay inside'


@pytest.mark.parametrize('directory', [False, True], ids=['file', 'parent-directory'])
def test_dangling_symlink_is_rejected_before_resolution_or_write(tmp_path, directory):
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    outside = tmp_path / ('outside-directory' if directory else 'outside.md')
    linked = workspace / ('linked' if directory else 'answer.md')
    relative = 'linked/answer.md' if directory else 'answer.md'
    try:
        linked.symlink_to(outside, target_is_directory=directory)
    except OSError as exc:
        if exc.errno in (errno.EPERM, errno.EACCES) or getattr(exc, 'winerror', None) == 1314:
            pytest.skip(f'This host lacks permission to create symlinks: {exc}')
        raise
    try:
        assert not linked.exists() and linked.is_symlink()
        assert_link_rejected(path_access(workspace, tmp_path, relative))
        assert not outside.exists()
    finally:
        linked.unlink()


@pytest.mark.skipif(os.name != 'nt', reason='Windows directory junction behavior')
def test_dangling_windows_junction_is_rejected_before_resolution_or_write(tmp_path):
    workspace = tmp_path / 'workspace'
    workspace.mkdir()
    outside = tmp_path / 'outside-not-created'
    linked = workspace / 'linked'
    created = subprocess.run(['cmd', '/c', 'mklink', '/J', str(linked), str(outside)],
                             capture_output=True, text=True, errors='replace')
    assert created.returncode == 0, created.stderr
    try:
        assert not linked.exists()
        assert_link_rejected(path_access(workspace, tmp_path, 'linked/answer.md'))
        assert not outside.exists()
    finally:
        # Remove this test's junction itself; never traverse or remove its target.
        os.rmdir(linked)
