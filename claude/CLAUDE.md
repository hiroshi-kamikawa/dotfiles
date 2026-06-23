## Language rules
- Conduct all internal reasoning, analysis, and rough drafting
  (the stage where you organize your thoughts) in English.
- Write every final answer presented to the user in natural,
  readable Japanese.
- Do not paste English reasoning directly—reconstruct the content
  as proper Japanese (avoid stiff, literal translation).
- For technical terms, you may add the English in parentheses after
  the Japanese when helpful, e.g. 強化学習 (reinforcement learning).
- Leave no English thinking notes or English sentences in the
  final answer.

Apply these rules to all subsequent responses.

## Key Principles:
1. Agent-First: Delegate to specialized agents for complex work
2. Parallel Execution: Use Task tool with multiple agents when possible
3. Plan Before Execute: Use Plan Mode for complex operations
4. Test-Driven: Write tests before implementation
5. Security-First: Never compromise on security

## Privacy
- Always redact logs; never paste secrets (API keys/tokens/passwords/JWTs)
- Review output before sharing - remove any sensitive data

## Code Style
- No emojis in code, comments, or documentation
- Prefer immutability - never mutate objects or arrays
- Many small files over few large files
- 200-400 lines typical, 800 max per file

## Git
- Conventional commits: feat:, fix:, refactor:, docs:, test:
- Always test locally before committing
- Small, focused commits

## Testing
- TDD: Write tests first
- 80% minimum coverage
- Unit + integration + E2E for critical flows