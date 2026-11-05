# AlphaESS Solar enhancement

This folder stages an additive update to the **existing** `alphaess-solar.vercel.app` frontend. `public/index.original.html` is the recovered public page; `public/index.html` retains its live readings, expandable details, voice/chat UI and existing `/api/live` and `/api/chat` calls, and adds the house viewer and energy insights.

## What is here

- A real Three.js GLB viewer. Choose a self-contained `.glb` of the actual house; drag to orbit, pinch/scroll to zoom. The file is read locally and is not uploaded; external asset URLs embedded in the model are blocked. The model is not persisted across reloads.
- A locally selected front photo can be displayed beside the viewer as a reference. It stays in the tab and is not uploaded. The provided real front photo is stored separately in `references/`, outside the public web directory, and ignored by Git.
- Today's generated, imported and exported energy from fields already used by the app. Missing data displays `--`; estimates are withheld when the app has not received a recent response. The underlying measurement time is not verified.
- Import cost and export credit estimates from user-entered flat rates and reported kWh. These omit daily supply charges, changing rates, taxes and other billing rules. Rates are stored in this browser.
- Simple guidance based on an unambiguous grid-direction label and a recent response. A recent response does not prove the underlying measurement is current; the guidance says so. These are not AI forecasts. The existing AI chat remains unchanged.
- No inverter, battery, or tariff settings are changed automatically.

## Actual status and limitations

- **Not deployed.** The linked production site remains unchanged. Its server-side source and deployment configuration were not found. This staging copy does not include the `/api/live` or `/api/chat` backend; copying it to a different origin by itself will not connect the system.
- The production page was observed reporting `missing key`. Live AlphaESS values and API permissions have not been verified in this session. The public app currently sends its access key in a query string and keeps it in browser storage; this inherited behavior is not a recommended security design and was not silently changed here because the backend contract is unavailable.
- A real street-level front photo was supplied after the initial concept images. It shows the front only; the roof, current solar array, sides and rear remain unverified. No model of the house has yet been made.
- A real 3D scene loaded from a test GLB passed an isolated loader test. The UI and WebGL viewer have not been browser-tested: the browser URL policy rejected opening the local file. No development server was started, per workspace instructions.
- Full AlphaCloud feature parity, live rate schedules, forecasts, optimised scheduling, verified device controls, and deployment remain unimplemented. AlphaESS's official API examples need to be checked against the user's account and actual device capabilities before implementing those operations.

## Checks

Run `pnpm --dir solar-enhancement test` from the workspace root. Tests cover tariff calculations, missing data and response age handling, the live panel's response/failure behavior, a self-contained GLB parse, and external asset URL rejection. These are not a browser, live API or measurement-freshness test.

Three.js 0.180.0 is bundled under `public/vendor/`; its MIT license is included there.
