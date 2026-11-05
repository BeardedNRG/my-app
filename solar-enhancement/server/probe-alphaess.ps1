# One-time read-only connection check. Values are entered masked, passed to
# the child via a pipe and are not written to a file or command-line argument.
$ErrorActionPreference = 'Stop'
$idPointer = [IntPtr]::Zero
$secretPointer = [IntPtr]::Zero
$probe = $null
try {
    $node = (Get-Command node -ErrorAction Stop).Source
    $scriptPath = Join-Path $PSScriptRoot 'probe-alphaess.mjs'
    if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) { throw 'Probe is unavailable' }
    $idSecure = Read-Host 'Paste the AlphaESS Developer ID' -AsSecureString
    $secretSecure = Read-Host 'Paste the AlphaESS AppSecret' -AsSecureString
    $idPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($idSecure)
    $secretPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secretSecure)
    $idText = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($idPointer)
    $secretText = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($secretPointer)
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $node
    $info.Arguments = '"{0}"' -f $scriptPath
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardInput = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $probe = [Diagnostics.Process]::Start($info)
    $payload = @{ appId = $idText; appSecret = $secretText } | ConvertTo-Json -Compress
    $probe.StandardInput.WriteLine($payload)
    $probe.StandardInput.Close()
    $response = $probe.StandardOutput.ReadToEnd()
    $probe.StandardError.ReadToEnd() | Out-Null
    $probe.WaitForExit()
    # Show only the probe's allowlisted status, count and field-presence flags.
    $result = $response | ConvertFrom-Json -ErrorAction Stop
    if ($result.status -notin @('ok', 'no_power_fields', 'no_systems', 'multiple_systems', 'system_identifier_unavailable', 'power_unavailable', 'connection_failed', 'invalid_input')) { throw 'Invalid probe response' }
    $publicResult = [ordered]@{ status = [string]$result.status }
    if (($result.boundSystemCount -is [int] -or $result.boundSystemCount -is [long]) -and $result.boundSystemCount -ge 0) { $publicResult.boundSystemCount = $result.boundSystemCount }
    if ($result.status -in @('ok', 'no_power_fields')) {
        $publicResult.availablePowerFields = [ordered]@{}
        foreach ($field in @('soc', 'ppv', 'pload', 'pgrid', 'pbat')) { $publicResult.availablePowerFields[$field] = ($result.availablePowerFields.$field -eq $true) }
        $publicResult.measurementTimeVerified = $false
    }
    $publicResult | ConvertTo-Json -Compress -Depth 4
    if ($probe.ExitCode -ne 0) { exit 1 }
} catch {
    Write-Output '{"status":"probe_failed"}'
    exit 1
} finally {
    if ($idPointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($idPointer) }
    if ($secretPointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($secretPointer) }
    if ($idSecure) { $idSecure.Dispose() }
    if ($secretSecure) { $secretSecure.Dispose() }
    if ($probe) { $probe.Dispose() }
    $idText = $null
    $secretText = $null
    $payload = $null
}
