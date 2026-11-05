# Solar app handoff — 4 November 2026

## Objective

Improve Dave's existing AlphaESS solar app with its real system data, a 3D representation of his own house, and useful solar/battery savings and income guidance. Preserve the existing app and AI chat; don't replace it with a generic dashboard.

## House reference

- The user provided one real street-level front view, saved privately as `references/house-front-reference.png`. It is outside `public/` and ignored by Git. Use it as the primary reference.
- Six earlier images were approximate concepts and contradict each other. They are secondary guides, not proof of the house layout.
- This is the only real image the user could find. **Do not ask him to search for more.** Use the visible front; clearly mark the unseen sides, roof geometry, and solar panel placement as estimates until verified.
- No house-specific 3D model has been made yet. The current GLB viewer is real, but an isolated generic GLB test is not proof of a finished house model.

## Existing work

- Claude and Codex established direct, turn-based communication by resuming the Claude Code session linked to PR #4 from the isolated `claude-channel/my-app` checkout. Codex initiates each exchange; Claude replies. PR commenting was blocked by integration permissions, and synchronization back to Claude's original web session is unverified. Restricted code-only snapshots under `claude-channel/shared*` were read by Claude; no credentials or house photographs were shared. The owner wants one existing web app, with the Home Assistant design as inspiration rather than a migration requirement. Claude hit a five-hour usage limit on 4 November; the CLI reported a reset at 3:50 pm Brisbane time.
- The staged server adapter withholds mismatched daily dates and requests that cross site midnight, and does not present AlphaESS-only PV as the whole-system total unless completeness is independently verified. The staged frontend can display the separately labelled AlphaESS PV value. The adapter remains unwired, and frontend expiry at site midnight after a response still requires handling. Claude identified that the original app requires `/api/live` and `/api/chat`; the deployed backend and AI chat implementation remain unavailable.
- Following Claude's review, chat now rejects missing keys and malformed replies, recovers from timeouts, and preserves a successful reply if speech fails. Nonzero readings with unknown flow direction are labelled unconfirmed. These changes are tested with local mocks; Claude was unable to review the latest revision due to its usage limit, and real browser/live verification is outstanding.
- User rejected the procedural 3D house studies as far worse than the earlier concept renders. Preserve `house-model/` but do not deploy or present these studies as an acceptable visual result. A realistic model/scene is still needed.
- A read-only AlphaESS client at `server/alphaess-client.mjs` supports listing systems, latest power, summary and daily energy endpoints with mocked tests. It is not wired to the existing app or tested against a real account; the website backend source, account access and deployment ownership are still unknown.
- Six source repositories were cloned under `github-reference/` and reviewed as references; `GITHUB-RESEARCH.md` records commits, licences and additional projects. Three validated skills were installed as `alphaess-cloud-data`, `alphaess-energy-planning` and `alphaess-local-modbus`. The vendor example lacks a licence file and PowerSync is PolyForm Noncommercial; do not assume code-reuse rights.
- The existing frontend's live panel was hardened against invalid, stale-looking and out-of-order responses, and model-loading cleanup was improved. The full suite most recently passed 14 tests in isolation. The deployed site remains unchanged; browser/WebGL and real account verification remain outstanding.
- A later inspection found an `fSpy.exe - Application Error` window after the previous hidden launch check. Do not treat that process-survival check as proof that fSpy works interactively. Inspecting the window through computer use timed out awaiting app approval, so the error cause remains unknown.

- Portable Blender 5.2.3 and the official fSpy Blender importer 1.0.3 are set up under the ignored `tools/` directory. The importer persists in the project-local Blender preferences and successfully imported an official sample with a camera and packed background. `Start-house-Blender.cmd` launches this isolated setup. `Start-house-fSpy.cmd` launches the official desktop app, which remained running in a short hidden process check; its UI operation and camera calibration remain unverified. The official fSpy Windows executable is unsigned.
- The Blender extension cache warning was addressed with project-local user resources. Save preview images are disabled in the isolated Blender settings to avoid the sandbox-denied Windows thumbnail cache; packing and saving a new photo scene completed without those earlier errors.
- The private `references/house-reference-start.blend` contains the packed front photo as an **uncalibrated** camera background, with no model geometry. Photo reference is not a finished house model.
- The user's instruction to keep moving is recorded in `AGENTS.md`; continue authorized work until a meaningful outcome or genuine blocker rather than stopping after a plan.

- Staged frontend: `public/index.html`, with the recovered original preserved as `public/index.original.html`.
- Existing `/api/live` and `/api/chat` paths and chat UI were retained. The linked production app was observed reporting `missing key`. Its backend source and deployment configuration were not found, and the staging copy is **not deployed**.
- Added a local GLB viewer, local reference-photo picker, three available daily energy fields, flat-rate cost and export-credit estimates, and conservative rules based on fresh data. The rules are not AI forecasting. No inverter settings are changed automatically.
- `pnpm --dir solar-enhancement test` most recently reported 26 passed; JavaScript syntax checks passed. Browser/WebGL and live API tests are not complete. The browser's automatic URL policy rejected `file:` previews; do not bypass that rejection with an alternate browser or workaround.

## Next work

1. Build a house-specific 3D asset using the front photo as the anchor; be explicit about estimates and verify the actual model and viewer before claiming completion. Do not substitute an unrelated house or pretend a 2D concept is a completed model.
2. Locate the actual app backend and deployment source, then verify its real AlphaESS integration, credentials, returned fields, and sign conventions. Protect keys; the inherited frontend puts its key in a query string and browser storage.
3. Connect verified data and improve the app's functions and energy recommendations. Do not imply automatic device controls, reliable earnings, or live data exist before testing.
4. Preserve user work and obtain required authorization before sending the private reference to an external service or publishing changes. Keep the reference photo out of public deployment assets unless explicitly authorized.

Project worklog: `D:\Obsidian Vault\agent-memory\projects\alphaess-solar\worklog.md`. Follow the workspace instructions and the task-specific model routing plan in `../MODEL-ROUTING-PLAN.md`. Do not expose secrets or the user's precise address in logs.
