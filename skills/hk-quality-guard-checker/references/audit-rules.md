# Audit Rules

Use these rules to classify findings and order recommendations. Adjust priority when repository instructions or team constraints provide stronger evidence.

## Required

Treat these as required for a typical production repository:

- A reproducible dependency install with one selected package manager and committed lockfile.
- Manually runnable lint or equivalent static analysis when the language ecosystem supports it.
- Type checking for typed projects.
- Tests for behavior-bearing code, using the existing framework.
- A build check for compiled or bundled applications.
- Secret detection before merge, with logs redacted.
- CI execution of the checks that protect the default branch, with required-check enforcement verified or explicitly marked unknown.
- No conflicting Git-hook managers or unexplained custom `core.hooksPath`.

Do not invent a check that the ecosystem cannot support. Record the gap and the reason instead.

## Recommended

Recommend these when relevant:

- Staged linting and formatting for fast local feedback.
- Forbidden-file checks for `.env`, credentials, generated output, large binaries, or platform artifacts that the repository excludes.
- Dependency vulnerability review in CI.
- Static accessibility lint for user-interface code.
- `pre-push` type checks and unit tests when their runtime is acceptable.
- End-to-end and runtime accessibility tests in CI.
- Caching that preserves reproducibility and does not hide validation.

## Optional

Recommend these only when project risk, maturity, or existing infrastructure justifies them:

- Commit-message enforcement.
- Coverage thresholds.
- Lighthouse budgets.
- Visual regression testing.
- License policy checks.
- Changed-package acceleration in a monorepo.

## Evidence and Priority

For every finding, record:

- evidence: files, scripts, dependencies, or command output
- status: present, partial, absent, conflicting, or unknown
- priority: required, recommended, or optional
- placement: manual, pre-commit, commit-msg, pre-push, or CI
- runtime estimate and failure cost
- proposed files and dependencies
- migration or rollout risk

For CI, record two separate facts:

- workflow status: present, partial, absent, or unknown
- merge-enforcement status: enforced, bypassable, absent, or unknown

Workflow files alone are not evidence that checks are required. Verify provider-side branch protection, rulesets, merge checks, and any bypass permissions when access is available. Otherwise mark enforcement `unknown`.

Prefer high-signal, low-cost safeguards. A missing full-repository CI lint is normally more urgent than a missing local formatting hook. A secret already committed to history is an incident to report, not merely a hook configuration gap.

## Baseline Rules

Run existing commands before changes when practical. Preserve the exit code and enough output to identify the failure without exposing secrets. After changes, rerun the same command and compare:

- pre-existing failure: failed before and after without a relevant regression
- introduced failure: passed before or is caused by the new configuration
- fixed failure: failed before and passes after
- unverified: could not run because of missing dependencies, credentials, services, platform support, or time

Never weaken an existing check merely to obtain a green result without explicit approval.
