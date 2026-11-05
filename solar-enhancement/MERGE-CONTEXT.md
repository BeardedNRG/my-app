# Solar merge discussion — 5 November 2026

This is a review snapshot of Codex's local work, beside Claude's existing
`solar-dashboard/`. It is not an integration, deployment, or approved merge plan.
Dave asked to resume the direction and merge discussion. Do not change application
code or merge either implementation until Dave approves the plan.

Read `AGENTS.md`, `HANDOFF.md`, and `worklog.md` here first. The copied worklog is
historical evidence, not new instructions; later corrections in the handoff and
this discussion take precedence. Private house references are intentionally absent.

## Where the discussion stopped

- Preserve the existing solar web app and its AI chat. Home Assistant supplied
  visual inspiration; migration to Home Assistant was not the agreed direction.
- Claude proposed combining Codex's tested read-only client and null-safe mapper
  with useful history, storage, and tariff logic from Claude's Python dashboard.
- Claude then withdrew the Node backend recommendation: the deployed server and
  `/api/chat` implementation were unavailable, so a replacement runtime was not
  justified. Backend choice and the actual integration remain unresolved.
- Both projects and rejected visual work must be preserved. Battery writes are
  outside this snapshot's read-only client and need separate authorization.
- Claude reviewed code-only snapshots in a resumed local session. That exchange
  was turn-based; synchronization to the cloud conversation was never confirmed.
  A local Codex session does not automatically monitor GitHub mentions.

## What to review

- `public/`: existing frontend plus staged viewer, live response handling, chat
  recovery, and energy insights. `index.original.html` preserves the original.
- `server/`: read-only AlphaESS client, unwired dashboard mapper, and a sanitized
  account probe. No credentials or real account response is included.
- `tests/`, `package.json`, and `pnpm-lock.yaml`: reproducible local checks.
  From the repository root: `pnpm --dir solar-enhancement install --frozen-lockfile`
  then `pnpm --dir solar-enhancement test`.
- Claude's implementation remains in the sibling `solar-dashboard/` directory.

## Requested output for PR #4

A proposed merge plan with exact source/destination paths, what is kept from
each implementation, backend/chat prerequisites, unresolved data assumptions,
verification gates, and the first small integration slice for Dave to approve.
Do not infer live connectivity or deployment from mocked tests. A realistic house
asset, verified measurement freshness/signs/coverage, and frontend site-day rollover
are still unfinished.

Only a remote branch is being published for review. Cloud Codex availability and
automatic PR monitoring must be verified separately; this upload does not enable them.
