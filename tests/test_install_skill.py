from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

import pytest


ROOT=Path(__file__).resolve().parents[1]


def install(project,agent='pi'):
    return subprocess.run(
        [sys.executable,str(ROOT/'tools/install_skill.py'),'--agent',agent,'--project',str(project)],
        capture_output=True,text=True,encoding='utf-8',errors='replace',
    )


def test_installer_is_scoped_and_refuses_overwrite(tmp_path):
    first=install(tmp_path,'both')
    assert first.returncode==0,first.stderr
    assert (tmp_path/'.agents/skills/text-prison/SKILL.md').is_file()
    assert (tmp_path/'.claude/skills/text-prison/scripts/check.py').is_file()
    assert not (tmp_path/'.pi').exists()
    assert not (tmp_path/'AGENTS.md').exists() and not (tmp_path/'.claude/settings.json').exists()
    before=(tmp_path/'.agents/skills/text-prison/SKILL.md').read_bytes()
    assert install(tmp_path,'both').returncode==2
    assert (tmp_path/'.agents/skills/text-prison/SKILL.md').read_bytes()==before


def test_pi_install_has_a_stable_portable_manifest(tmp_path):
    first=tmp_path/'first'; first.mkdir()
    second=tmp_path/'second'; second.mkdir()
    for project in (first,second):
        result=install(project)
        assert result.returncode==0,result.stderr
        assert not (project/'.agents').exists() and not (project/'.claude').exists()
    target=first/'.pi/skills/text-prison'
    raw=(target/'install-manifest.json').read_bytes()
    assert not raw.startswith(b'\xef\xbb\xbf') and b'\r\n' not in raw
    assert raw==(second/'.pi/skills/text-prison/install-manifest.json').read_bytes()
    manifest=json.loads(raw)
    assert list(manifest)==sorted(manifest)
    assert 'install-manifest.json' not in manifest
    assert 'scripts/check.py' in manifest
    assert all('\\' not in relative and '__pycache__' not in relative for relative in manifest)
    for relative,digest in manifest.items():
        assert hashlib.sha256((target/relative).read_bytes()).hexdigest()==digest


def test_all_destinations_are_checked_before_a_both_install(tmp_path):
    target=tmp_path/'.claude/skills/text-prison'
    target.mkdir(parents=True)
    (target/'user.txt').write_text('keep',encoding='utf-8')
    assert install(tmp_path,'both').returncode==2
    assert not (tmp_path/'.agents').exists()
    assert (target/'user.txt').read_text(encoding='utf-8')=='keep'


def test_non_directory_parent_is_reported_without_copying(tmp_path):
    (tmp_path/'.pi').write_text('keep',encoding='utf-8')
    result=install(tmp_path)
    assert result.returncode==2
    assert 'not a directory' in result.stderr
    assert (tmp_path/'.pi').read_text(encoding='utf-8')=='keep'


@pytest.mark.parametrize('relative',['.pi','.pi/skills','.pi/skills/text-prison'])
def test_linked_destination_or_parent_cannot_escape_project(tmp_path,relative):
    project=tmp_path/'project'; project.mkdir()
    outside=tmp_path/'outside'; outside.mkdir()
    sentinel=outside/'keep.txt'; sentinel.write_text('keep',encoding='utf-8')
    linked=project/relative; linked.parent.mkdir(parents=True,exist_ok=True)
    try:
        linked.symlink_to(outside,target_is_directory=True)
    except OSError as exc:
        pytest.skip(f'This host cannot create directory symlinks: {exc}')
    result=install(project)
    assert result.returncode==2
    assert 'linked installation path' in result.stderr
    assert sorted(path.name for path in outside.iterdir())==['keep.txt']
    assert sentinel.read_text(encoding='utf-8')=='keep'


@pytest.mark.skipif(os.name!='nt',reason='Windows directory junction behavior')
@pytest.mark.parametrize('relative',['.pi','.pi/skills','.pi/skills/text-prison'])
def test_windows_junction_parent_cannot_escape_project(tmp_path,relative):
    project=tmp_path/'project'; project.mkdir()
    outside=tmp_path/'outside'; outside.mkdir()
    linked=project/relative; linked.parent.mkdir(parents=True,exist_ok=True)
    junction=subprocess.run(['cmd','/c','mklink','/J',str(linked),str(outside)],
                            capture_output=True,text=True,errors='replace')
    assert junction.returncode==0,junction.stderr
    try:
        result=install(project)
        assert result.returncode==2
        assert 'linked installation path' in result.stderr
        assert list(outside.iterdir())==[]
    finally:
        os.rmdir(linked)
