# Run this script from an Administrator PowerShell.
#
# Adjust $RouterIp if your Jarvis/LiteLLM host is different.

$RouterIp = "192.168.0.121"
$TaskName = "Jarvis GPU Status"
$ScriptPath = "C:\Jarvis\gpu-status.ps1"

# Restrict inbound access to the Jarvis/LiteLLM host.
#
# If a rule with this exact display name already exists, remove/update it
# manually rather than creating many duplicates.
New-NetFirewallRule `
    -DisplayName "Jarvis GPU Status" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 8098 `
    -RemoteAddress $RouterIp `
    -Action Allow

# Create a startup task that runs hidden as SYSTEM.
schtasks /Create `
    /TN $TaskName `
    /TR "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File $ScriptPath" `
    /SC ONSTART `
    /RU SYSTEM `
    /RL HIGHEST `
    /F

# Start immediately so a reboot is not required for testing.
schtasks /Run /TN $TaskName

Write-Host ""
Write-Host "Created and started '$TaskName'."
Write-Host "Test locally with:"
Write-Host "  curl.exe http://127.0.0.1:8098/gpu"
