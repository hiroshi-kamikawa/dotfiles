---
name: hk-skill-creator
description: Create or update portable AI agent skills for both Codex and Claude under the user's dotfiles skills directory. Use when the user asks to design, scaffold, implement, revise, or validate a cross-platform skill with English agent artifacts and Japanese human documentation stored under `$HOME/dotfiles/skills`.
---

# HK Skill Creator

Create maintainable, platform-neutral skills under `$HOME/dotfiles/skills`. Make each skill usable by both Codex and Claude. Write agent-facing artifacts in English and the human-facing `README.md` in Japanese.

## Resolve the Destination

1. Resolve the user's home directory from the environment rather than embedding an account name.
2. Set the only skills root to `$HOME/dotfiles/skills`.
3. Create or update the skill only at `$HOME/dotfiles/skills/<skill-name>`.
4. Express the location as `$HOME/dotfiles/skills` in portable instructions; never embed a username or machine-specific absolute path.
5. Do not use the current repository, current working directory, `$CODEX_HOME/skills`, `~/.claude/skills`, or any other global skill directory as the destination.

If `$HOME` cannot be resolved or `$HOME/dotfiles` cannot be identified safely, stop and ask the user for the home or dotfiles location. Create the `skills` directory under the confirmed dotfiles directory when it does not yet exist.

## Authoring Requirements

- Write `SKILL.md`, YAML metadata, scripts, references, assets containing text, comments, examples, and UI metadata entirely in English.
- Add a Japanese `README.md` to every skill as an intentional convention of this dotfiles repository. This repository-specific exception to the usual minimal-skill guidance preserves human review context without making the README an agent execution resource. Explain what the skill is, how to use it effectively, and the implementation background and decisions. Do not reference the README from `SKILL.md` or require an agent to read it during execution.
- Prefix every skill name with `hk-`, including the folder name and the frontmatter `name`. Never create an unprefixed skill.
- After the required `hk-` prefix, use lowercase letters, digits, and hyphens. Keep the complete name under 64 characters and prefer a short verb-led phrase.
- Make the folder name exactly match the frontmatter `name`.
- Include only `name` and `description` in the `SKILL.md` frontmatter.
- Put both capability and trigger conditions in `description`.
- Use imperative instructions in the body and keep the skill concise.
- Add only resources that directly support repeated execution. Do not add changelogs, installation guides, or placeholder resources. Treat the required `README.md` as human documentation rather than an execution resource.
- Keep all essential behavior in `SKILL.md` and its referenced resources so neither Codex nor Claude depends on vendor-specific metadata.
- Use platform-neutral terms such as "agent," "model," and "available tools" unless a platform-specific distinction is necessary.
- Avoid instructions that assume only Codex commands, Claude commands, one vendor's directory layout, or one vendor's tool names.
- Add platform-specific metadata only when supported by repository conventions. Treat it as an optional adapter, keep it in English, and never make it the sole source of behavior.
- When creating `agents/openai.yaml`, include English `display_name`, `short_description`, and `default_prompt`, and make the default prompt explicitly mention `$<skill-name>`.
- Keep `short_description` between 25 and 64 characters. Quote every string value in `agents/openai.yaml` and do not add optional interface fields unless the user provides the required values or repository conventions require them.

The conversation with the user may use their preferred language. Agent-facing skill artifacts must still be English, while `README.md` must be Japanese.

## Workflow

1. Inspect relevant repository conventions and any existing skill with the same name.
2. Clarify only requirements that materially affect behavior and cannot be inferred safely.
3. Resolve the directory containing this `SKILL.md` as `<skill-root>`. Run `python3 "<skill-root>/scripts/manage_skill.py" normalize-name "<requested-name>"` to normalize the name and add `hk-` exactly once. Use this resolved path for every subsequent `manage_skill.py` command; never assume the current working directory is the skill directory.
4. Identify realistic trigger phrases and the reusable workflow the skill must encode.
5. For a new skill, run `python3 "<skill-root>/scripts/manage_skill.py" create "<requested-name>" --description "<English description>"`. Skip creation when updating an existing skill. Use `--dry-run` when the destination must be checked without writing.
6. Replace all generated placeholders and implement the smallest useful set of instructions and resources.
7. Create or update `README.md` in Japanese. Cover the skill's purpose, effective usage, and the background and decisions behind its implementation.
8. Review the instructions from both a Codex and Claude perspective. Replace unsupported product assumptions with capability-based instructions or document a necessary conditional branch.
9. Test every executable resource with a representative invocation.
10. Run `python3 "<skill-root>/scripts/manage_skill.py" validate "<skill-name>"`. Then run each platform validator that is locally available, such as Codex's `quick_validate.py`; treat a missing validator or dependency as unavailable and report it separately rather than claiming it passed. Fix every validation error and review every warning.
11. Inspect the final tree for unfinished template markers, placeholder text, non-English agent artifacts, machine-specific paths, unnecessary vendor coupling, and missing or inadequate Japanese README content.
12. Report the created or updated files and validation result to the user.

## Safety

- Preserve unrelated files and user changes in the repository.
- Do not overwrite an existing skill blindly. Inspect it first and edit only what the request requires.
- Do not create files outside `$HOME/dotfiles/skills/<skill-name>` unless the user separately requests other work.

## Script Scope

Use `scripts/manage_skill.py` for deterministic operations: destination resolution, name normalization, minimal scaffolding, and structural validation. Keep semantic work in the agent workflow: understanding the request, writing useful instructions, deciding which resources are warranted, and reviewing cross-platform behavior.
