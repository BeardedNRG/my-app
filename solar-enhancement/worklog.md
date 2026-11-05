# Worklog


## 2026-11-03 11:25:12 +10:00 - Solar app house viewer and tariff insight staging
Project key: alphaess-solar
Agent: gpt-codex

Changed paths:
C:\Users\NRG_BIGRIG\Documents\new-chat-2\solar-enhancement\ (public/index.html, preserved public/index.original.html, solar-enhancement.js, solar-enhancement.css, solar-math.js, vendor Three.js assets and license, tests, README.md, package files)

What changed / what it does:
Recovered existing public solar frontend and staged additive 3D GLB viewer and live-field-based energy/tariff insights while retaining chat and endpoint paths. Model stays local; external GLB assets blocked; no inverter controls or fake data. Public app uses access key in query string and local storage; backend source unavailable.

Verification:
pnpm --dir solar-enhancement test: 6 passed, 0 failed; includes actual isolated GLB loader and tariff/unknown/stale checks. node --check enhancement scripts and vm.Script original inline passed. Work browser access disabled; no UI or live API validation.

Unfinished work:
Need actual house photos or model; original server source and deployment access; key/live system connection; browser UI/WebGL testing; model-specific API permissions; deeper app parity and AI optimisation. Changes are local staging and not deployed.

## 2026-11-03 20:56:39 +10:00 - Real front photograph reference
Project key: alphaess-solar
Agent: gpt-codex

Changed paths:
C:\Users\NRG_BIGRIG\Documents\new-chat-2\solar-enhancement\references\ (photo and notes); solar-enhancement\public\index.html; solar-enhancement\public\solar-enhancement.js; solar-enhancement\public\solar-enhancement.css; solar-enhancement\README.md

What changed / what it does:
Preserved user-provided street-level reference outside public web assets and added browser-local photo reference preview. Front elevation observations and uncertainty documented. Did not fabricate roof or solar-panel positions. No house model generated.

Verification:
Source and copied photo SHA256 match. pnpm --dir solar-enhancement test: 6 passed, 0 failed; node --check JavaScript passed; HTML inline syntax and photo control presence checked. Browser automatic review blocked file URL because only HTTP/HTTPS are permitted; no visual UI verification.

Unfinished work:
Real 3D model of house, roof/panel reference, real account key/backend source, deployment, live data and browser UI validation remain outstanding. Current update is local staging only.

## 2026-11-04 05:31:54 +10:00 - Context handoff
Project key: alphaess-solar
Agent: gpt-codex

Changed paths:
C:\Users\NRG_BIGRIG\Documents\new-chat-2\solar-enhancement\HANDOFF.md

What changed / what it does:
Preserves user objective, real front photograph reference, prior concept caveats, local staging and exact next steps. User could find only one real image and should not be asked to find more.

Verification:
Confirmed handoff file exists and reviewed its opening. No application changes in this handoff.

Unfinished work:
House-specific 3D asset, backend/key, live verification, browser testing, integration and deployment remain incomplete; see HANDOFF.md.

## 2026-11-04 08:19:21 +10:00 - House image and 3D tool research
Project key: alphaess-solar
Agent: gpt-codex

Changed paths:
solar-enhancement\references\house-twilight-concept-01.png

What changed / what it does:
Generated a private twilight image concept from the user-provided front photo. Researched Blender camera matching and image-to-3D tools.

Verification:
Reviewed the generated image visually and SHA256 checked the saved copy. No model, plugin installation or app integration was performed.

Unfinished work:
Create and verify an accurate house model; unseen geometry remains unknown. Backend and live app integration remain incomplete.

## 2026-11-04 08:28:09 +10:00 - Portable Blender and house reference scene
Project key: alphaess-solar
Agent: gpt-codex

Changed paths:
solar-enhancement\prepare-house-reference.py; solar-enhancement\tools\.gitignore; solar-enhancement\tools\blender-5.2.3-windows-x64; solar-enhancement\references\house-reference-start.blend

What changed / what it does:
Downloaded the official portable Blender 5.2.3 archive and created a private Blender scene with the house front photo packed as an uncalibrated camera background.

Verification:
Official SHA256 matched; Blender executable Authenticode signature was valid. Blender ran in background and reopened the scene; packed 1459x984 photo and absence of house geometry were verified. Scene creation emitted nonfatal thumbnail and extension cache permission errors.

Unfinished work:
Camera calibration, actual house modelling, rendering and app integration are not complete. No plugin installed. Hidden sides and roof remain estimates.

## 2026-11-04 08:46:46 +10:00 - fSpy setup and persistent workflow
Project key: alphaess-solar
Agent: gpt-codex

Changed paths:
solar-enhancement\AGENTS.md; solar-enhancement\HANDOFF.md; solar-enhancement\Start-house-Blender.cmd; solar-enhancement\Start-house-fSpy.cmd; solar-enhancement\tools\blender-user; solar-enhancement\tools\fspy-app

What changed / what it does:
Added project continuity instructions and installed the official fSpy importer into project-local Blender preferences plus the portable fSpy desktop app. Added launchers and isolated Blender resources; disabled save preview generation to avoid sandbox thumbnail cache denial.

Verification:
Blender 5.2.3 loaded the persisted add-on and imported an official sample camera with packed background. A fresh photo pack and save emitted neither prior cache error. fSpy process remained alive for seven seconds hidden. Official fSpy executable is unsigned; its UI and the launcher scripts were not interactively tested. First sample assertion expected the wrong camera name; corrected assertion passed. Git ignore verification was unavailable because this directory is not a Git repository.

Unfinished work:
Calibrate the house photo in fSpy, create and visually verify the house model, then integrate with the existing app and real live solar data. Launcher and fSpy interactive operation remain untested.

## 2026-11-04 09:39:13 +10:00 - Solar integration work and user feedback
Project key: alphaess-solar
Agent: gpt-codex

Changed paths:
solar-enhancement\public\index.html; solar-enhancement\public\solar-live.js; solar-enhancement\public\solar-math.js; solar-enhancement\public\solar-enhancement.js; solar-enhancement\public\solar-model-utils.js; solar-enhancement\server; solar-enhancement\tests; solar-enhancement\house-model; solar-enhancement\README.md; solar-enhancement\AGENTS.md; solar-enhancement\HANDOFF.md

What changed / what it does:
Added an isolated read-only AlphaESS API client and improved the staged frontend telemetry handling. House studies were explicitly rejected by the user; preserve them and stop procedural variants. Opened the user supplied AlphaESS portal, which redirected to login.

Verification:
pnpm --dir solar-enhancement test: 14 passed. JavaScript syntax checks passed. Independent review found no new concrete client or model cleanup defects. No real account, browser WebGL or deployed backend verification. fSpy application error window observed; inspection timed out awaiting app approval.

Unfinished work:
User must authenticate in opened portal to determine account access; do not request credentials in chat. Connect verified live telemetry, existing website backend and AI. House visual is rejected and requires realistic reconstruction; do not deploy the draft. App remains unpublished and not complete.

## 2026-11-04 10:41:01 +10:00 - AlphaESS GitHub sources and reusable skills
Project key: alphaess-solar
Agent: gpt-codex

Changed paths:
solar-enhancement\github-reference; solar-enhancement\GITHUB-RESEARCH.md; solar-enhancement\skills-src; C:\Users\NRG_BIGRIG\.codex\skills\alphaess-cloud-data; C:\Users\NRG_BIGRIG\.codex\skills\alphaess-energy-planning; C:\Users\NRG_BIGRIG\.codex\skills\alphaess-local-modbus; solar-enhancement\server\alphaess-client.mjs; solar-enhancement\tests\alphaess-client.test.mjs; solar-enhancement\AGENTS.md; solar-enhancement\HANDOFF.md

What changed / what it does:
Downloaded six public repositories for source reference and catalogued examined alternatives and licences. Created and installed three reusable skills. Extended the isolated read-only AlphaESS client with daily energy and summary requests. Developer portal now appears signed in; credentials were not displayed, copied or saved.

Verification:
All six clones were clean; snapshot commits and licence files checked. All three installed skills passed structural validation, matched reviewed copies by SHA256 and had independent instruction review. Independent client review found no concrete defects; pnpm --dir solar-enhancement test passed 15 tests. No real API call, deployment, inverter action or real-account result was performed.

Unfinished work:
Secure credential configuration and authenticated read-only account test remain; app backend ownership and deployment remain unknown. House models were rejected and a realistic model is still needed.

## 2026-11-04 11:26:23 +10:00 - Direct Claude and Codex conversation
Project key: alphaess-solar
Agent: gpt-codex

Changed paths:
solar-enhancement\claude-channel\my-app

What changed / what it does:
Created an isolated checkout of the existing Claude project and resumed the Claude Code session linked from PR 4. Exchanged three direct messages; Codex initiates each turn and Claude responds in the resumed terminal session. No project changes or secrets were shared in the channel.

Verification:
Claude confirmed that the resumed session opened PR 4 and replied to successive continue calls. The GitHub connector rejected a minimal PR comment with HTTP 403; automatic review rejected an earlier detailed PR message because of nonpublic project information. Whether the terminal exchange synchronizes to the original web session is unverified.

Unfinished work:
The direct session is turn-based and Claude cannot initiate messages in this setup. Claude remained in plan mode. Integration and deployment are unfinished; independent review identified date and solar attribution issues in the staged dashboard adapter that must be resolved before use.

## 2026-11-04 12:33:07 +10:00 - Claude collaboration and frontend fixes
Project key: alphaess-solar
Agent: gpt-codex

Changed paths:
solar-enhancement\claude-channel\shared*; solar-enhancement\server\alphaess-dashboard.mjs; solar-enhancement\public\index.html; solar-enhancement\public\solar-live.js; solar-enhancement\public\solar-enhancement.js; solar-enhancement\tests; solar-enhancement\HANDOFF.md

What changed / what it does:
Exchanged direct messages with Claude, which reviewed limited code-only snapshots. Preserved existing app direction. Hardened staged date and PV-source mapping, frontend labelling and chat recovery, and added a mobile send button.

Verification:
pnpm --dir solar-enhancement test: 26 passed; inline JavaScript syntax and submit control checked. Claude reviewed earlier revisions read-only; an independent agent reviewed chat changes. Claude reached its five-hour usage limit before reviewing the latest revision and reported reset at 3:50 pm Brisbane time. No real account, browser UI, production endpoint or deployment tested.

Unfinished work:
Connect the real AlphaESS account and locate existing deployed backend. Retain original chat functionality, confirm PV and load coverage, handle frontend day rollover, complete realistic house model, browser checks and eventual integration. Claude and Codex can converse only when Codex initiates; web session synchronization unconfirmed.
