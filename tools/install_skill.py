"""Install the shared skill into an explicitly selected project; never overwrite."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat
import sys


AGENT_ROOTS = {'codex': '.agents', 'claude': '.claude', 'pi': '.pi'}


def is_link_or_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return bool(getattr(info, 'st_file_attributes', 0)
                & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))


def check_target(project: Path, target: Path) -> None:
    current = project
    for part in target.relative_to(project).parts:
        current = current / part
        if is_link_or_reparse(current):
            raise ValueError(f'Refusing a linked installation path: {current}')
        if current == target and current.exists():
            raise ValueError(f'Refusing to overwrite: {current}')
        if current.exists() and not current.is_dir():
            raise ValueError(f'Installation parent is not a directory: {current}')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', choices=['codex', 'claude', 'pi', 'both'], required=True,
                        help='both installs Codex and Claude; Pi is selected separately')
    parser.add_argument('--project', type=Path, required=True)
    args = parser.parse_args(argv)
    project = args.project.resolve()
    if not project.is_dir():
        parser.error('--project must be an existing directory')
    source = Path(__file__).resolve().parents[1] / 'skills' / 'text-prison'
    agents = ['codex', 'claude'] if args.agent == 'both' else [args.agent]
    targets = [project / AGENT_ROOTS[a] / 'skills' / 'text-prison' for a in agents]
    generated_patterns = shutil.ignore_patterns('__pycache__', '*.pyc', 'install-manifest.json')

    def ignore_generated(directory: str, names: list[str]) -> set[str]:
        ignored = set(generated_patterns(directory, names))
        if Path(directory) == source / 'vale' / 'styles':
            ignored.update(set(names) & {'Google', 'Microsoft', '.vale-config'})
        return ignored

    try:
        # Preflight every destination before copying either member of "both".
        for target in targets:
            check_target(project, target)
        for target in targets:
            shutil.copytree(source, target, ignore=ignore_generated)
            files = sorted((p for p in target.rglob('*') if p.is_file()),
                           key=lambda p: p.relative_to(target).as_posix())
            manifest = {p.relative_to(target).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in files}
            (target / 'install-manifest.json').write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2)+'\n',
                encoding='utf-8', newline='\n')
            print(target)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
