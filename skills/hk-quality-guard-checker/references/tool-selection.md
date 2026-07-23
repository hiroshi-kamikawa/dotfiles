# Tool Selection

Preserve established tools. Select a new tool only after showing why the repository needs it, how it will be installed, which files it changes, and how developers and CI will run it.

## Staged-file Routing

Use lint-staged when Husky launches checks for selected staged paths. Generate configuration from detected tools:

- Biome: route supported files to the repository's existing `biome check --write` convention.
- ESLint and Prettier: route source files to `eslint --fix` and supported text files to `prettier --write`.
- Stylelint: add supported stylesheet extensions to `stylelint --fix`, followed by the established formatter when compatible.
- No formatter: propose a formatter; do not choose one silently.

Remember that lint-staged passes matched file paths to commands, mutates and re-stages results by default, and may use Git operations to protect or hide working changes. Inspect its current version and configuration semantics before changing flags. In monorepos, the nearest configuration is selected and configurations are not automatically merged.

## Linting and Formatting

- Do not migrate ESLint to Biome, or the reverse, as part of routine guard setup.
- Do not enable `--fix` for a tool that is currently check-only without assessing staged changes.
- Keep full-repository check and write commands distinct, for example `format:check` and `format`.
- Apply a newly adopted formatter to changed files first. Put repository-wide formatting in a separate approved change.

## Tests and Builds

Reuse detected Vitest, Jest, Node test, Playwright, Cypress, or framework commands. Do not replace the test framework. Separate quick unit tests from E2E or service-dependent suites. Use affected or related-test modes only if they are already reliable for the repository; CI must still provide complete coverage.

## Secret Detection

Prefer an existing scanner. When proposing Gitleaks:

- use its supported staged Git mode for pre-commit and redact output
- use a complete repository, diff, or history scan in CI as appropriate
- check current command syntax for the installed version
- never print detected secret values in reports

Gitleaks is not a normal JavaScript development dependency. Follow an established tool-management path:

- mise, asdf, or another version manager: add it there
- a committed Brewfile: propose adding it there
- an established container workflow: propose a pinned container image
- GitHub Actions: propose the official or project-approved action, pinned according to repository policy
- no established method: present options and wait for a choice

If a secret is found, stop exposing output, identify the affected path safely, and recommend revocation and history-remediation steps separately from hook setup.

## Accessibility, Performance, and Supply Chain

- Add static accessibility lint only for supported templates or components.
- Put axe-based browser checks in CI unless the repository has a fast local fixture.
- Add Lighthouse only with a stable deployed or local target. Propose budgets; do not invent failing thresholds.
- Use the selected package manager's audit or an established scanner. Do not automatically apply forceful dependency upgrades.
- Add visual regression only when baseline storage, review ownership, and CI artifacts are defined.

## Commit Rules

Add commitlint or equivalent only after confirming team convention. Reuse an existing configuration, release process, or changelog convention as evidence. Avoid turning an informal pattern into a blocking rule without approval.
