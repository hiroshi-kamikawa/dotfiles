---
name: hk-quality-guard-checker
description: "Inspect software repositories and audit, propose, install, configure, repair, and validate quality safeguards using existing project commands, Git hooks, staged-file tools, and CI. Use when asked to improve linting, formatting, type checks, tests, builds, accessibility, security, secret detection, dependency checks, commit rules, or related repository quality automation."
---

# Repository Quality Guard

Build a repository-specific quality system. Treat hook managers as launchers, staged-file tools as routers, project commands as the reusable interface, specialist tools as the checkers, and CI as a potential merge-enforcement layer. Call CI non-bypassable only after required checks and protected-branch or ruleset settings are verified.

## Select a Mode

Infer the least expansive mode that satisfies the request:

- `audit`: inspect and report without changing files.
- `setup-minimal`: connect existing lint and formatting tools to fast staged checks, add secret and forbidden-file checks when supportable, and repeat the guarantees in CI.
- `setup-full`: extend the minimal setup with suitable type checks, tests, builds, accessibility, dependency security, performance, or visual checks.

If the request does not authorize repository changes, use `audit`. Before adding dependencies, adopting conventions, or materially changing CI, present the proposed files, commands, risks, and expected hook runtime, then obtain approval.

## Inspect Before Designing

1. Read repository instructions and inspect the worktree without changing staged state.
2. Run `node <skill-directory>/scripts/inspect-repository.mjs [repository]`. It detects root and nested manifests for Node.js, Python, PHP, Go, Rust, and Ruby. If Node.js is unavailable, inspect the same manifests manually and report that automated inspection was unavailable.
3. Run `<skill-directory>/scripts/check-hook-conflicts.sh [repository]`.
4. Inspect relevant manifests, lockfiles, tool configuration, workflows, existing hook files, package scripts, task-runner targets, and ecosystem-native commands directly. Treat script output as evidence, not a substitute for source inspection.
5. Identify every detected ecosystem, dependency manager, runtime, framework, typed-language usage, workspace topology, CI provider, tests, linting, formatting, accessibility, security checks, and tool-management conventions. If the automated scan is truncated, continue the relevant inspection manually.
6. Run existing quality commands to establish a baseline when doing so is read-only and practical. Record pre-existing failures separately.

Read [audit-rules.md](references/audit-rules.md) to prioritize gaps. Read [hook-placement.md](references/hook-placement.md) before placing checks. Read [tool-selection.md](references/tool-selection.md) before adding or choosing tools. For workspaces, also read [monorepo.md](references/monorepo.md). Before editing CI, read [ci-patterns.md](references/ci-patterns.md).

## Design the Guard

- Reuse existing scripts and tools. Do not create aliases such as `lint:hook`, `lint:ci`, and `lint:check` for the same command.
- Define manually runnable project commands first, using the repository's established package scripts, task runner, or ecosystem-native interface, then call those commands from hooks and CI.
- Keep hook files to short command invocations. Move selection logic to the established staged-file router and reusable logic to project commands or `scripts/`.
- Prefer staged-only checks in `pre-commit`, repository-wide checks in `pre-push`, and complete enforcement in CI.
- Keep `pre-commit` near 5 seconds and no more than about 10 seconds. Keep `pre-push` near 30 seconds; move slower or unreliable work to CI.
- Never rely on local hooks as the only guarantee because hooks can be bypassed or disabled. A CI workflow is also not a merge guarantee until required-check and branch-protection settings are confirmed.
- Add only necessary files. Do not generate the complete example structure by default.
- Preserve the current package manager, formatter, linter, test framework, hook manager, CI structure, and tool-management approach unless the user approves a migration.
- If another hook manager or multiple hook paths exist, explain the conflict and propose consolidation. Do not install Husky beside it automatically.
- If Husky is appropriate, install it at the Git root and use the package-manager-specific official setup. Account for CI or production installs where development dependencies are absent.
- If no formatter, secret-scanner installation method, commit convention, or policy threshold is established, propose choices instead of selecting one silently.

## Apply Safely

1. Preserve unrelated changes and the user's staged state.
2. Make minimal manifest and lockfile edits using the repository's package manager.
3. Extend existing hook and lint-staged configuration instead of recreating it.
4. Connect hooks to reusable project commands; do not embed substantial shell programs in hook files.
5. Add the equivalent full checks to the existing CI system with its established runtime and cache conventions.
6. Avoid repository-wide formatting, framework migrations, strict new coverage or Lighthouse thresholds, commit-message rules, and large CI rewrites unless separately approved.
7. Let Git retain the change history; do not create backup copies.

## Validate

Run the reusable scripts directly, then the hook entry points. Do not create a real commit merely to test a hook. When staged input is required, do not alter existing staged content; ask before staging a controlled fixture and restore only that fixture afterward.

Validate, as applicable:

1. lint-staged configuration and staged checks
2. secret and forbidden-file checks
3. quick, push, and full quality scripts
4. individual hook files with representative arguments
5. CI workflow syntax or the repository's local CI validator, plus provider-side required-check and protected-branch settings when accessible
6. install behavior with the selected package manager
7. the final diff and staged-state preservation

Do not claim success for commands that were skipped, unavailable, or already failing. Distinguish introduced failures from baseline failures.

## Report

Use headings equivalent to the following in the user's language:

- Investigation Results: detected technology, existing safeguards, and prioritized gaps
- Additions: installed dependencies, changed files, added hooks, and CI changes
- Execution Timing: checks assigned to `pre-commit`, `commit-msg`, `pre-push`, and CI
- Manual Commands: commands developers can run without hooks
- Validation Results: passed, failed, skipped, and unavailable validation, including pre-existing errors
- Remaining Work: residual risks and deferred improvements

For audits, include the expected files and dependencies for each recommendation without modifying the repository. Report CI workflow presence separately from merge-enforcement status using `enforced`, `bypassable`, `absent`, or `unknown`.
