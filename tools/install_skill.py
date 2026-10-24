"""Install the shared skill into an explicitly selected project; never overwrite."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', choices=['codex', 'claude', 'both'], required=True)
    parser.add_argument('--project', type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve()
    if not project.is_dir():
        parser.error('--project must be an existing directory')
    source = Path(__file__).resolve().parents[1] / 'skills' / 'text-prison'
    agents = ['codex', 'claude'] if args.agent == 'both' else [args.agent]
    targets = [project / ('.agents' if a == 'codex' else '.claude') / 'skills' / 'text-prison' for a in agents]
    for target in targets:
        if target.exists() or target.is_symlink():
            print(f'Refusing to overwrite: {target}', file=sys.stderr)
            return 2
    for target in targets:
        shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        manifest = {str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in target.rglob('*') if p.is_file()}
        (target / 'install-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
        print(target)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
