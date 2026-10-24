"""Run with the project virtual environment: python -m eval --help."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .common import read_json, write_json
from .contracts import load_tasks, load_calibration_packets, normalize_run
from .pi_adapter import doctor, parse_events
from .runner import Experiment, HumanReviewPending, preview


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='TextPrison model evaluation and evidence workbench')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('doctor', help='Read-only installation and credential readiness; no inference')
    commands.add_parser('validate', help='Validate task and calibration inventory against versioned schemas offline')
    commands.add_parser('plan', help='Preview the frozen pilot allocation without model calls')
    inherit = commands.add_parser('init-ai', help='Create the approved six-judge experiment, preserving prior calls and human history')
    inherit.add_argument('--experiment', default='ai-six-20261025')
    inherit.add_argument('--inherit-from', default='pilot-20261024')
    run = commands.add_parser('run', help='Explicitly consume model budget; resumable completed assignments')
    run.add_argument('phase', choices=['smoke', 'calibration', 'pilot'])
    run.add_argument('--experiment', default='ai-six-20261025')
    run.add_argument('--retry-failed', action='store_true', help='Retain originals and retry failed assignments only')
    serve = commands.add_parser('serve', help='Start local model evidence workbench (historical human batches remain supported)')
    serve.add_argument('--experiment', default='ai-six-20261025')
    serve.add_argument('--port', type=int, default=8765)
    summary = commands.add_parser('summarize', help='Produce JSON and Markdown from actual records')
    summary.add_argument('--experiment', default='ai-six-20261025')
    tokens = commands.add_parser('tokens', help='Offline o200k_base size proxy; not provider-billed usage')
    tokens.add_argument('--experiment', default='ai-six-20261025')
    tokens.add_argument('--fetch-tokenizer', action='store_true', help='Explicitly fetch the pinned public tokenizer asset if missing')
    load = commands.add_parser('import', help='Convert a legacy record or inspect a Pi JSONL log offline')
    load.add_argument('path', type=Path)
    load.add_argument('--kind', choices=['run', 'pi'], default='run')
    load.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'doctor':
            from .agy_adapter import doctor as agy_doctor
            output = {'pi': doctor(), 'agy': agy_doctor()}
        elif args.command == 'validate':
            tasks, calibration = load_tasks(), load_calibration_packets()
            for item in calibration:
                if not item['candidate_text'].strip():
                    raise ValueError('Empty calibration candidate')
            output = {'status': 'passed', 'tasks': len(tasks), 'calibration_items': len(calibration),
                      'human_acceptance': 'not_run'}
        elif args.command == 'plan':
            output = preview()
        elif args.command == 'init-ai':
            exp = Experiment.inherit_ai_only(args.experiment, args.inherit_from)
            output = {'experiment': exp.name, 'plan': exp.plan, 'budget': exp.budget.snapshot(),
                      'lineage': exp.manifest['lineage']}
        elif args.command == 'run':
            exp = Experiment(args.experiment)
            output = getattr(exp, args.phase)(retry=args.retry_failed)
        elif args.command == 'serve':
            from .web import serve
            exp = Experiment(args.experiment)
            serve(exp.db_path, port=args.port)
            return 0
        elif args.command == 'summarize':
            from .reporting import summarize
            output = summarize(Experiment(args.experiment))
        elif args.command == 'tokens':
            from .token_meter import measure
            output = measure(Experiment(args.experiment), fetch=args.fetch_tokenizer)
        else:
            output = normalize_run(read_json(args.path)) if args.kind == 'run' else parse_events(args.path.read_bytes())
            write_json(args.output, output)
            output = {'saved': str(args.output), 'status': output.get('status')}
        print(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False))
        if args.command == 'run' and args.phase == 'smoke':
            return 0 if output and all(row['outcomes'].get('smoke_passed') for row in output) else 1
        return 0
    except HumanReviewPending as exc:
        print(json.dumps({'status': 'human_review_pending', 'message': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3
    except (ValueError, OSError, RuntimeError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
