"""Offline prompt size estimates, explicitly distinct from provider-reported usage."""
from __future__ import annotations

import hashlib
from importlib.metadata import version
import os
from pathlib import Path
import urllib.request

import tiktoken

from .common import ROOT, digest, write_json
from .contracts import load_tasks
from .runner import generation_rules

ASSET_URL = 'https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken'
ASSET_SHA256 = '446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d'


def measure(exp, *, fetch: bool = False) -> dict:
    cache = ROOT / '.local' / 'tiktoken'
    asset = cache / hashlib.sha1(ASSET_URL.encode()).hexdigest()
    if not asset.is_file():
        if not fetch:
            raise FileNotFoundError('Tokenizer asset missing; --fetch-tokenizer requires authorization for the pinned public asset')
        with urllib.request.urlopen(ASSET_URL, timeout=30) as response:
            payload = response.read(8_000_000)
        if digest(payload) != ASSET_SHA256:
            raise ValueError('Tokenizer asset hash mismatch; nothing was saved')
        cache.mkdir(parents=True, exist_ok=True)
        asset.write_bytes(payload)
    if digest(asset.read_bytes()) != ASSET_SHA256:
        raise ValueError('Existing tokenizer asset hash mismatch; inspect it before replacing')
    os.environ['TIKTOKEN_CACHE_DIR'] = str(cache)
    tokenizer = tiktoken.get_encoding('o200k_base')
    def count(text):
        return {'tokens': len(tokenizer.encode(text, disallowed_special=())), 'characters': len(text),
                'utf8_bytes': len(text.encode('utf-8')), 'sha256': digest(text)}
    report = {'tokenizer': 'o200k_base', 'implementation': 'tiktoken', 'version': version('tiktoken'),
              'asset_url': ASSET_URL, 'asset_sha256': ASSET_SHA256,
              'interpretation': 'Offline size proxy only; this is not the exact tokenizer or billed usage of the configured models.',
              'skill_entry': count((exp.skill / 'SKILL.md').read_text(encoding='utf-8')), 'tasks': [], 'prompts': {}}
    for task in load_tasks(exp.inputs / 'tasks'):
        report['tasks'].append({'task_id': task['id'],
            'full_B': count(generation_rules(exp.skill, task['profile'], task['language'], full=True)),
            'routed_C': count(generation_rules(exp.skill, task['profile'], task['language'], full=False))})
    for path in sorted(exp.jobs.glob('*/prompt.txt')):
        report['prompts'][path.parent.name] = count(path.read_text(encoding='utf-8'))
    output = exp.path / 'token-estimates.json'
    write_json(output, report)
    return {'path': str(output), 'tokenizer': report['tokenizer'], 'tasks': report['tasks'],
            'interpretation': report['interpretation']}
