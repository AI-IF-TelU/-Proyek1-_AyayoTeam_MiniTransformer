# Mini-Transformer Starter Kit

Starter repository for the Mini-GPT group project. This kit contains the initial project contracts and a **first-pass Kilo Code event logger**. It deliberately does not implement the Transformer model yet.

## First-use sequence (Windows + VS Code + Kilo Code)

1. Extract this folder to a location without spaces if practical, e.g. `C:\Projects\mini-transformer`.
2. Open that folder in VS Code (`File → Open Folder`).
3. Create `.kilo/member.local.json` by copying `.kilo/member.local.example.json`, then set your unique member ID, e.g. `member-01`. This local file is ignored by Git.
4. Ensure Kilo Code is installed and open its panel for this workspace.
5. Start a new Kilo session with the smoke-test prompt below.
6. Check whether files appear under `docs/ai-logs/raw/<member-id>/`.
7. Confirm the raw JSONL contains the unique prompt text and the visible assistant response. If it does not, stop and debug logging before using Kilo for project code.

## Logging smoke-test prompt

> LOGGING SMOKE TEST. Do not edit any files or run commands. Reply exactly: `LOGGER-TEST-2026-01` and explain that this is only a test. This prompt and your response must be recorded by the project logger.

After that session, inspect:

- `docs/ai-logs/raw/<member-id>/<session-id>.jsonl`
- `docs/ai-logs/reports/AI-LOG-<member-id>-<session-id>.md`

The local plugin listens to Kilo events and writes sanitized event payloads. Kilo's event shapes can change, so this starter logger is **not accepted as operational until the smoke test confirms prompt and response capture in your installed version**.

## Git setup

Open a terminal in this folder and run:

```powershell
git init
git add .
git commit -m "chore: bootstrap mini-transformer project"
```

Create an empty GitHub repository named `mini-transformer`, then connect it using the repository URL shown by GitHub:

```powershell
git branch -M main
git remote add origin https://github.com/<YOUR-ORG-OR-USERNAME>/mini-transformer.git
git push -u origin main
```

If the GitHub repository already has a README or license commit, do not blindly overwrite it. Tell the project coordinator so we can reconcile the histories safely.

## Current project rule

Do not begin model implementation until the team has approved the six documents in `docs/` and the Kilo logging smoke test succeeds.
