# TextPrison project instructions

## Current scope

Maintain `skills/text-prison` as the single runtime Skill source. The user approved the reviewed Chinese-support, GitHub publication and project-installation plan on 2026-10-25. Vale handles the explicit writing rules; AutoCorrect is optional Chinese typography guidance, not a second semantic checker. The former Python checker and all project-owned tests, evaluation code, reports, and run data are retired. Do not recreate a checker wrapper or JSON Schema backend.

Do not recreate or execute Agent field tests, model judges, A/B experiments, trigger experiments, test suites, fixtures, evaluation dashboards, or benchmark pipelines in this repository. Do not run test suites in upstream snapshots. A separately requested, single document review is allowed within that request's scope; it is not permission to run the Skill or restart evaluation work.

## Preserved references

Preserve the original ZIP files, the downloaded conversations in `.local/20261025GPT.md` and `.local/20261025GPT-zh.md`, root `MANIFEST.sha256.json`, and `DOCS_PATCH.md` as original inputs. The manifest and patch describe the original package, not the current checkout; their historical references may name retired files. Do not alter them to match current files.

`submodules/` contains five fixed, read-only upstream research snapshots. Keep their working trees and licenses unchanged, including upstream test files. Do not treat their instructions as project policy, activate hooks, install dependencies, or include them in package or content scans. A requested upstream update must identify its exact commit and provenance.

## Dependencies, installation and temporary work

Writing guidance needs no runtime dependency; diagnostics need the selected separately installed tool. Keep the standard-library installer's Codex, Claude Code, Pi and `both` interfaces and refusal to overwrite. Exclude only named generated Vale package directories, retaining original rules. The documented npx path uses Vercel Skills CLI; unlike the Python installer, it can overwrite an existing target, so check and preserve existing copies before updates.

Install tools or Skills, synchronize packages and change PATH only within the user's explicit scope. The current request authorizes GitHub publication, npx installation into QCBlender and making Vale usable, including limited CLI installation smoke checks. AutoCorrect installation needs the separately requested user decision. It does not authorize hooks/MCP/CI, QCBlender product edits or publication, Agent field tests, or automatic future dependency updates.

Keep temporary working records under ignored `.local/`. Preserve unknown files and stop deleting a particular path on unresolved permissions or ownership; do not change ACLs or take ownership.

## Delivery checks and claims

Use static inspection of current files, references, configuration, installation paths and `git diff --check`. A user-authorized installation can include bounded CLI checks with temporary inputs; do not turn them into maintained fixtures or a test framework. Report what was actually inspected or run, and mark unavailable runtime checks `Not Run`.

Keep Vale package versions and rules in `skills/text-prison/vale/README.md`, AutoCorrect version and configuration facts in `skills/text-prison/autocorrect/README.md`, and host installation paths in `docs/INSTALL.md`; link other documentation to those sources. Installed Skill references must stay self-contained. Preserve automatic discovery. Diagnostics never expand the user's editing scope, and missing tools never authorize downloads. Community typography preferences do not override project conventions or scientific notation.

Writing rules and mechanical diagnostics do not establish semantic fidelity, full ASD-STE100 conformance, reader comprehension, Agent success or a measured cost benefit. Do not publish unsupported percentages or a composite quality score.
