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