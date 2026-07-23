# Repository agent instructions

## Engineering baseline

- Agents must not fabricate code, behavior, outcomes, or assumptions.
- Every solution must be demonstrably based on working code, verifiable research, and facts from the codebase or runtime observations.
- Work according to KISS (keep it simple), DRY (avoid duplication), and clean code (readable, small, maintainable).
- Apply OWASP principles where relevant (secure defaults, input validation, least privilege) and Shift Left practices (test, lint, and validate early).

## Git handoff

After completing a full implementation update, end the final response with a directly copyable shell block containing the relevant Git commands:

```bash
git add <changed-files>
git commit -m "<concise conventional commit message>"
git push
./.venv/bin/python ./scripts/manage_app.py deploy mm3
```

List only files changed for the completed update. Choose the commit message based on the actual change; do not leave placeholders in the delivered commands.
