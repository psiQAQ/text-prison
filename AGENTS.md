# TextPrison project instructions

## Current scope

Maintain `skills/text-prison` as the single runtime Skill source. The project currently provides writing instructions and a standard-library project installer. The Python checker and all project-owned tests, evaluation code, reports, and run data were retired at the user's request on 2026-10-25. Vale integration and a new option-selection workflow require approval of the separately reviewed implementation plan; do not implement them during cleanup or plan review.

Do not recreate or execute Agent field tests, model judges, A/B experiments, trigger experiments, test suites, fixtures, evaluation dashboards, or benchmark pipelines in this repository. Do not run test suites in upstream snapshots. A separately requested, single document review is allowed within that request's scope; it is not permission to run the Skill or restart evaluation work.

## Preserved references

Preserve the original ZIP files, the downloaded conversation in `.local/20261025GPT.md`, root `MANIFEST.sha256.json`, and `DOCS_PATCH.md` as original inputs. The manifest and patch describe the original package, not the current checkout; their historical references may name retired files. Do not alter them to match current files.

`submodules/` contains five fixed, read-only upstream research snapshots. Keep their working trees and licenses unchanged, including upstream test files. Do not treat their instructions as project policy, activate hooks, install dependencies, or include them in package or content scans. A requested upstream update must identify its exact commit and provenance.

## Dependencies, installation and temporary work

The instruction-only Skill needs no runtime dependency. `tools/install_skill.py` uses Python's standard library and installs only into an explicitly selected existing project; it refuses to overwrite an existing Skill. Keep its Codex, Claude Code and Pi interfaces. Do not install into this or another project, install Vale, synchronize packages, add hooks/MCP/CI, or change global configuration without authorization.

Keep temporary cleanup and plan-review records under ignored `.local/`. Preserve unknown files and stop deleting a particular path on unresolved permissions or ownership; do not change ACLs or take ownership.

## Delivery checks and claims

Use static inspection of current files, references, configuration, installation paths and `git diff --check`. Do not create a test framework to check this work. Report what was actually inspected or run, and mark unavailable runtime checks `Not Run`.

Writing rules and mechanical diagnostics do not establish semantic fidelity, full ASD-STE100 conformance, reader comprehension, Agent success or a measured cost benefit. Do not publish unsupported percentages or a composite quality score.
