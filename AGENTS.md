# Repository agent instructions

## Engineering baseline

- Agents must not fabricate code, behavior, outcomes, or assumptions.
- Every solution must be demonstrably based on working code, verifiable research, and facts from the codebase or runtime observations.
- Never assume cause or runtime state: verify first with logs, traces, reproducible commands, and code-path inspection.
- Work according to KISS (keep it simple), DRY (avoid duplication), and clean code (readable, small, maintainable).
- Apply OWASP principles where relevant (secure defaults, input validation, least privilege) and Shift Left practices (test, lint, and validate early).
- Quick fixes/workarounds are not accepted as final fixes. If used for diagnosis, replace them with a structural root-cause fix before completion.
- Always follow fail-fast and root-cause solving: never hide defects with hardcoded defaults, silent fallbacks, or quick patches.
- Do not assume causes or runtime behavior; verify with concrete evidence first (logs, reproducible commands, and code-path inspection).
- Temporary diagnostics are allowed, but production fixes must remove the real cause and not rely on workaround-style masking.
- Do not run `git commit` or `git push` without explicit user approval.
- Do not inspect secrets files such as `.env`, `.secrets`, `.my.cnf`, private keys, tokens, or credentials.

## Git handoff

After completing a full implementation update, end the final response with a directly copyable shell block containing the relevant Git commands:

```bash
git add <changed-files>
git commit -m "<concise conventional commit message>"
git push
./.venv/bin/python ./scripts/manage_app.py deploy mm3
```

List only files changed for the completed update. Choose the commit message based on the actual change; do not leave placeholders in the delivered commands.
