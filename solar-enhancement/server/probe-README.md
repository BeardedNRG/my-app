# Private AlphaESS connection probe

This is a one-shot, read-only account check. It calls AlphaESS `getEssList` and, only when exactly one system is bound, `getLastPowerData`. It reports the system count and whether known numeric power fields are present; it does not print system identifiers, raw measurements, AppID, AppSecret or vendor error details. It does not verify the time of the measurement. It does not connect the app, save credentials, perform settings writes or keep polling.

Run locally in PowerShell with Node.js available:

```powershell
& 'C:\Users\NRG_BIGRIG\Documents\new-chat-2\solar-enhancement\server\probe-alphaess.ps1'
```

Paste the Developer ID and AppSecret **at the two masked prompts**, not into the command, a chat message, or a file. The wrapper passes them to the probe through the child process's standard input; the JavaScript entrypoint refuses direct terminal input and command-line arguments. The credentials temporarily exist in the two local processes' memory; ordinary JavaScript and PowerShell strings cannot be reliably zeroed. The script does not write the credentials to disk or pass them to a shell command. The requests go only to the AlphaESS endpoint fixed in `alphaess-client.mjs`.

`ok` means the vendor returned one system and at least one supported numeric field. `no_power_fields`, `no_systems`, `multiple_systems`, `system_identifier_unavailable`, `power_unavailable` and `connection_failed` mean further investigation is needed. It deliberately does not guess which system to use when multiple are bound. A fresh HTTP response is not proof of a fresh inverter measurement.

The probe is covered by local tests using injected fake clients. It has not been run with a real account in this project; network access, account binding and field availability remain unverified.
