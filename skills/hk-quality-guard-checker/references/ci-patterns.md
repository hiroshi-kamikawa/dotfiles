# CI Patterns

Use the repository's existing CI provider and workflow structure. Do not add a second provider or replace a working pipeline during guard setup.

## Reuse the Manual Interface

CI should invoke the same package scripts developers run locally:

```sh
pnpm install --frozen-lockfile
pnpm quality:full
```

Use the selected package manager's immutable-install option. Do not copy the internal lint, test, and build command chain into CI when a reusable script already represents it.

## Minimum Coverage

A minimal quality job normally includes:

- reproducible dependency installation
- full-repository formatting check when a formatter exists
- lint
- type checking when applicable
- unit tests
- build for compiled applications
- secret and forbidden-file checks

Add dependency audits, E2E, runtime accessibility, performance, and visual checks when the mode and project justify them.

## Pull Requests and the Default Branch

Run fast deterministic checks for pull requests and pushes to the protected branch. Use scheduled jobs for expensive history scans or ecosystem audits when appropriate, but do not make a scheduled job the only branch protection.

When secret scanning a pull request from an untrusted fork, avoid exposing privileged secrets. Prefer scanners that can run on checked-out content without elevated tokens.

## Merge Enforcement

Keep workflow presence separate from merge enforcement:

- `enforced`: the provider confirms required checks and branch protection or rulesets, with bypass permissions understood
- `bypassable`: checks run, but merges can proceed without them or broad bypass permissions exist
- `absent`: no relevant CI workflow or merge rule exists
- `unknown`: workflow files exist, but provider-side settings were not accessible or verified

Do not infer `enforced` from committed workflow files. When authorized and tooling is available, inspect the provider's branch-protection, ruleset, required-check, and bypass settings. Treat successful remote execution as evidence that a workflow runs, not by itself as evidence that it blocks merges.

## Versions, Caches, and Permissions

- Follow repository policy for pinning actions, images, and runtimes.
- Derive the runtime from committed version files or manifest constraints.
- Key dependency caches from the selected lockfile.
- Cache dependencies or tool outputs, not unverified build products that bypass checks.
- Grant the narrowest job permissions.
- Do not add write permissions to a read-only quality job without a demonstrated need.

## Husky in CI and Production

Do not depend on hook execution in CI. Run quality scripts directly. Account for installations that omit development dependencies: use the current Husky-supported approach and the repository's environment conventions so `prepare` does not fail or install hooks where Git metadata is unavailable.

## Validation

Use a local workflow linter or provider validator when available. Otherwise validate syntax and inspect command paths, environment variables, permissions, runtime versions, cache keys, and triggers manually. Report remote CI execution as unverified until the provider actually runs it, and report merge enforcement as unknown until provider settings are verified.
