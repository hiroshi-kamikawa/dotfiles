# Hook Placement

Place a check according to scope, speed, determinism, and whether CI must repeat it.

| Check | Manual | Pre-commit | Pre-push | CI |
|---|---:|---:|---:|---:|
| Formatting | yes | staged only | no | full repository |
| Linting | yes | staged only | optional | full repository |
| Secret detection | yes | staged diff | optional | diff and/or history |
| Forbidden files | yes | staged paths | no | repository |
| Type checking | yes | only if very fast | yes | yes |
| Unit tests | yes | related tests only | yes | yes |
| Build | yes | no | only if fast | yes |
| Static accessibility lint | yes | staged only | no | yes |
| Browser accessibility or E2E | yes | no | normally no | yes |
| Lighthouse or visual regression | yes | no | no | yes |
| Dependency audit | yes | no | no | yes |

## Pre-commit

Target 5 seconds and keep the upper bound near 10 seconds. Route staged paths through lint-staged or an established equivalent. Typical commands are:

```sh
pnpm lint:staged
pnpm secrets:staged
pnpm files:check
```

Use the repository's package manager. Avoid repository-wide type checks, builds, complete test suites, network calls, and long custom shell logic.

## Commit-msg

Use this hook only when the repository already has an accepted commit convention or the user approves adopting one:

```sh
pnpm exec commitlint --edit "$1"
```

Preserve the hook argument exactly. Do not add Conventional Commits, ticket requirements, message-length policies, or forbidden phrases by assumption.

## Pre-push

Target about 30 seconds. Use a manually runnable aggregate such as `quality:push` for repository-wide type checks and unit tests. Add builds only when measured runtime and reliability are acceptable. Do not duplicate the aggregate command inline in the hook.

## CI

Repeat every merge-blocking guarantee in CI because local hooks can be disabled. Run full-file checks rather than staged-only checks. Add builds, integration tests, browser tests, audits, or history scans here when they are too slow or environment-dependent for local hooks.

## Hook Files

Keep `.husky/*` files as command launchers. Put:

- reusable command composition in package scripts
- staged glob routing in lint-staged configuration
- non-trivial policy logic in named scripts with direct tests
- final enforcement and platform setup in CI

Do not parse staged files with large shell loops inside a hook when lint-staged or an existing staged-file tool can express the routing.
