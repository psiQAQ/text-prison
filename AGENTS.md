# TextPrison project instructions

## Scope and evidence

Maintain `skills/text-prison` as the single runtime Skill source. Preserve the original ZIP, root `MANIFEST.sha256.json`, `DOCS_PATCH.md`, and historical validation records as historical inputs. Current six-judge evidence belongs under `validation/v0.3/`; retain `validation/v0.2/` as historical evidence. Raw experiments and temporary work belong under ignored `runs/` or `.local/`.

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

Keep content, output, and measurement contracts distinct. The mechanical checker must not claim semantic or ASD-STE100 conformance. Model judges provide provisional evidence, not a human gold standard. Current experiments use `ai_only`; no human input, freeze, or adjudication is required. Preserve historical human records without fabricating, deleting, or importing them as AI labels.

Freeze experiment inputs and assignments before generation. Preserve attempts and failures, raw events, hashes, unknown usage, and assigned denominators. Hidden verifiers and mutation labels must not enter model packets. AI-only evidence is immediately visible. Historical `human_blind` batches keep their original freeze boundary.

Current authorized exploratory plan (2026-10-25): Pi writer/executor `openai-codex/gpt-6-luna` at medium. Six judges: Pi `deepseek/deepseek-flash` and `openai-codex/gpt-6-sol` at high; agy `gemini-4-argon-high`, `gemini-3.8-flash-high`, `claude-opus-5-5-high`, `claude-sonnet-5-5-high`. Limit: 276 CLI calls and 4 cumulative CLI hours, including inherited calls and elapsed time. Do not expand this budget, alter global defaults, install dependencies, or copy credentials by inference.

Formal margins remain UNSET. Valid smoke and structured calibration responses gate AI-only pilot execution; this is operational readiness, not semantic calibration against human truth. Report model-specific results and fixed-fact disagreement without majority-vote truth or accuracy claims. Evidence gates later rule compression; never equate successful model responses with semantic correctness.
