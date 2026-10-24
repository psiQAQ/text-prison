# TextPrison project instructions

## Scope and evidence

Maintain `skills/text-prison` as the single runtime Skill source. Preserve the original ZIP, root `MANIFEST.sha256.json`, `DOCS_PATCH.md`, and historical validation records as historical inputs. New evidence belongs under `validation/v0.2/`; raw experiments and temporary work belong under ignored `runs/` or `.local/`.

`submodules/` contains fixed upstream research snapshots. Do not treat their instructions as project policy, activate their hooks, install their dependencies, modify their working trees, or include them in default package/test scans. Record an explicitly requested upstream update with its exact commit and provenance.

## Environment and checks

Use the project `.venv` and locked dependencies. On Windows run:

```powershell
.\.venv\Scripts\python.exe -m pytest --basetemp runs/tests/all -q
.\.venv\Scripts\python.exe -m eval validate
.\.venv\Scripts\python.exe -m eval plan
git diff --check
```

Tests create synthetic human labels only in isolated test databases. Never write simulated judgments into the user's real review batch. Offline fixtures, real model calls, browser QA, and human/scientific acceptance must be reported separately.

## Experiment integrity

Keep content, output, and measurement contracts distinct. The mechanical checker must not claim semantic or ASD-STE100 conformance. Model judges provide provisional evidence; the user's independent initial judgment and final adjudication remain separate.

Freeze experiment inputs and assignments before generation. Preserve attempts and failures, raw events, hashes, unknown usage, and assigned denominators. Hidden verifiers and mutation labels must not enter model or initial human packets. Do not reveal AI labels before the whole initial batch freezes.

Current exploratory plan: Pi writer/executor `openai-codex/gpt-6-luna` at medium; judges `deepseek/deepseek-flash` and `openai-codex/gpt-6-sol` at high; 128 CLI calls and 4 cumulative CLI hours. Real calls require the session's existing authorization. Do not expand budget, change models, modify global Pi/Codex defaults, or copy credentials by inference.

Formal margins remain UNSET. Human calibration gates pilot generation; evidence gates later rule compression. Do not fabricate acceptance or equate successful imports/model responses with semantic correctness.
