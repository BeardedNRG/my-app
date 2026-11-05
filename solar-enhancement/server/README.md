# AlphaESS read client

`alphaess-client.mjs` is a server-only, read-only client based on the [official AlphaESS demo](https://github.com/alphaess-developer/alphacloud_open_api/blob/main/alpha_api_demo.py). It supports listing bound systems, fetching the last power data, daily energy and summary data using signed requests to the fixed vendor API origin. The caller supplies the intended date as `YYYY-MM-DD` in the site's timezone; the client does not guess it. It is not connected to an HTTP route and has not been tested against a real account. No inverter settings can be changed through it.

Credentials must be supplied securely by the server environment; do not place them in frontend code, browser storage, URLs, or logs. The eventual application must authenticate and authorize requests to its own routes before using this client. The system identifier and returned telemetry can be sensitive and should not be logged or exposed beyond the authorized user.

The client returns the vendor's data without guessing units, flow direction, measurement time, or compatibility with the existing app's backend. Validate the actual account's returned data and timestamps before mapping it to the dashboard. Network redirects are rejected to avoid forwarding authentication headers to another origin. Tests use injected fetch and clock functions and never contact the vendor.
