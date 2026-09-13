# Jarvis desktop GPU telemetry service
#
# Exposes:
#   GET http://<desktop-ip>:8098/gpu
#
# The Jarvis router uses this ONLY when the desktop model is not already
# resident and it needs to decide whether there is enough free VRAM to load it.
#
# Security:
# - keep this on the private LAN;
# - create a Windows firewall rule restricted to the router/LiteLLM host;
# - do not expose port 8098 to the internet.
#
# Requirement:
# - NVIDIA driver / nvidia-smi available in PATH.

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://+:8098/")
$listener.Start()

Write-Host "Jarvis GPU status server listening on port 8098"

while ($listener.IsListening) {

    $context = $listener.GetContext()
    $request = $context.Request
    $response = $context.Response

    try {

        if ($request.Url.AbsolutePath -eq "/gpu") {

            # Query fields as bare numeric values so the router does not need
            # to parse "MiB" or percent signs.
            $raw = & nvidia-smi `
                --query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu `
                --format=csv,noheader,nounits

            $parts = $raw.Split(",")

            $data = @{
                gpu_name    = $parts[0].Trim()
                total_mb    = [int]$parts[1].Trim()
                used_mb     = [int]$parts[2].Trim()
                free_mb     = [int]$parts[3].Trim()
                utilisation = [int]$parts[4].Trim()
            }

            $json = $data | ConvertTo-Json -Compress
            $buffer = [System.Text.Encoding]::UTF8.GetBytes($json)

            $response.StatusCode = 200
            $response.ContentType = "application/json"
            $response.ContentLength64 = $buffer.Length
            $response.OutputStream.Write(
                $buffer,
                0,
                $buffer.Length
            )

        }
        else {

            $response.StatusCode = 404

        }

    }
    catch {

        $errorJson = @{
            error = $_.Exception.Message
        } | ConvertTo-Json -Compress

        $buffer = [System.Text.Encoding]::UTF8.GetBytes($errorJson)

        $response.StatusCode = 500
        $response.ContentType = "application/json"
        $response.ContentLength64 = $buffer.Length
        $response.OutputStream.Write(
            $buffer,
            0,
            $buffer.Length
        )
    }

    $response.Close()
}
