- Do not preserve backward compatibility. Remove obsolete paths instead of adding compatibility layers, fallbacks, or migrations.
- Choose the simplest implementation that fully meets the current requirements. Avoid speculative abstractions, configuration, and indirection.
- Grow the system in layers. Start from the smallest version that works end to end, and add each new capability on top of a product that already works. Never trade a working product for unfinished complexity.
- Keep components modular and concerns clearly separated.
- Prefer established, well-maintained libraries when they reduce overall complexity or improve reliability. Do not reimplement common functionality without a clear reason.
- Lean on the dependencies already in the project before writing your own implementation or adding packages. Do not assume a library lacks a capability without checking its documentation and types.
- Make architectural decisions for the long term. Do not accept a stopgap that only works for now and is meant to be replaced later.

## Subagent policy

For long-running or multi-step tasks, aggressively use subagents to keep
the primary thread context small.

Delegate:
- codebase exploration
- independent investigations
- test execution and failure analysis
- log analysis
- documentation/API research
- large-file reading

Subagents should return concise summaries with evidence and file references.
Do not copy raw logs, large command outputs, or exploration transcripts back
into the primary thread.

Parallelize independent read-heavy tasks whenever possible.
Keep architectural decisions, coordinated edits, and final verification in
the primary thread.

## Personal technology direction

The canonical handbook is:

- Local: `/Users/shoirhi/Documents/Codex/engineering-handbook/technology/stack-direction.md`
- GitHub: `https://github.com/hiroshi-kamikawa/engineering-handbook`

Read the canonical handbook before making material architecture, dependency,
infrastructure, authentication, data, or CI/CD decisions.

- Default to Cloudflare Workers, Astro, React, shadcn/ui, and Hono. Use EmDash
  when customer-managed content is required.
- Default to D1 for relational data, R2 for files, KV for eventually consistent
  cache/configuration, and Durable Objects only for coordination that requires
  them.
- Use Cloudflare Access for internal applications. Use a managed authentication
  service for customer-facing SaaS; never build password authentication.
- Customer repositories, Cloudflare accounts, data, and third-party service
  contracts must be customer-owned and independently handoff-ready.
- Supervised Codex work may push directly to `main` after local verification.
  Unattended Codex work must use an isolated branch and pull request.
- Cloudflare Workers Builds is the only production deployment path and must run
  lint, type checks, tests, and the production build before deployment.
- Do not introduce parallel frameworks, duplicate API paths, compatibility
  layers, or speculative abstractions without a demonstrated requirement.
