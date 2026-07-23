# Monorepo Guidance

Install and launch Git hooks from the Git root. Do not create independent Husky installations for every package.

## Diagnose the Workspace

Inspect:

- root `package.json` workspaces
- `pnpm-workspace.yaml`
- Turbo, Nx, Lage, Rush, or Lerna configuration
- package-level scripts and tool configuration
- packages using a different language or package manager
- nested `package.json`, `pyproject.toml`, `composer.json`, `go.mod`, `Cargo.toml`, and `Gemfile` manifests
- CI path filters and affected-package commands

Do not infer that every package supports the same checks.

The bundled inspector scans nested manifests to a bounded depth and reports whether the scan was truncated. Nested manifests alone produce `monorepoStatus: candidate`; an explicit workspace or orchestrator signal produces `detected`. Distinguish real workspace packages from examples, fixtures, vendored code, and independent projects by inspecting workspace configuration and repository documentation.

## Command Design

Prefer root commands that delegate through the established orchestrator:

```json
{
  "scripts": {
    "lint:staged": "lint-staged",
    "typecheck": "turbo run typecheck",
    "test:unit": "turbo run test"
  }
}
```

Adapt names and commands to the repository. Do not add an orchestrator solely for quality hooks.

## lint-staged Configuration

Start with one root configuration when tools and rules are shared. Split configuration only when packages require different working directories, extensions, or commands.

When multiple configurations exist, inspect every relevant file. lint-staged uses the closest configuration for a staged file and does not merge it automatically with the root configuration. A package configuration must therefore cover or explicitly extend every required pattern for that package.

## Runtime and CI

Use affected-package execution only when the repository already trusts its dependency graph and CI still has an appropriate complete or scheduled validation path. Cache outputs according to the orchestrator's existing conventions. Avoid running multiple lint-staged processes concurrently because they can compete over Git state.

For a package located below the Git root, verify Husky installation paths against the current Husky documentation and repository layout. Do not use an unsafe parent-directory installation workaround.
