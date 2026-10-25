# TextPrison project instructions

## Current scope

Maintain `skills/text-prison` as the single runtime Skill source. The user approved the reviewed plan on 2026-10-25: task-specific editing choices, on-demand writing references, Vale configurations and installation/use documentation. Vale is the only mechanical engine. The former Python checker and all project-owned tests, evaluation code, reports, and run data are retired. Do not recreate a checker wrapper or JSON Schema backend.

Do not recreate or execute Agent field tests, model judges, A/B experiments, trigger experiments, test suites, fixtures, evaluation dashboards, or benchmark pipelines in this repository. Do not run test suites in upstream snapshots. A separately requested, single document review is allowed within that request's scope; it is not permission to run the Skill or restart evaluation work.

## Preserved references

Preserve the original ZIP files, the downloaded conversation in `.local/20261025GPT.md`, root `MANIFEST.sha256.json`, and `DOCS_PATCH.md` as original inputs. The manifest and patch describe the original package, not the current checkout; their historical references may name retired files. Do not alter them to match current files.

`submodules/` contains five fixed, read-only upstream research snapshots. Keep their working trees and licenses unchanged, including upstream test files. Do not treat their instructions as project policy, activate hooks, install dependencies, or include them in package or content scans. A requested upstream update must identify its exact commit and provenance.

## Dependencies, installation and temporary work

Writing guidance needs no runtime dependency; mechanical diagnostics require a separately installed Vale. `tools/install_skill.py` uses Python's standard library and installs only into an explicitly selected existing project; it refuses to overwrite an existing Skill. Keep its Codex, Claude Code, Pi and `both` interfaces. Exclude only the named generated Vale package directories when copying, retaining original rules. Do not install into this or another project, install Vale, synchronize packages, add hooks/MCP/CI, or change global configuration without authorization. The current delivery explicitly excludes these executions.

Keep temporary working records under ignored `.local/`. Preserve unknown files and stop deleting a particular path on unresolved permissions or ownership; do not change ACLs or take ownership.

## Delivery checks and claims

Use static inspection of current files, references, configuration, installation paths and `git diff --check`. Do not create a test framework to check this work. Report what was actually inspected or run, and mark unavailable runtime checks `Not Run`.

Keep package versions, enabled rules and configuration choices in `skills/text-prison/vale/README.md`, and host installation paths in `docs/INSTALL.md`; link other documentation to those sources. Installed Skill references must stay self-contained. Preserve automatic discovery. Vale diagnostics never expand the user's editing scope, and missing tools never authorize downloads.

Writing rules and mechanical diagnostics do not establish semantic fidelity, full ASD-STE100 conformance, reader comprehension, Agent success or a measured cost benefit. Do not publish unsupported percentages or a composite quality score.
