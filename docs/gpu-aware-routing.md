# GPU-Aware Desktop Routing

## 1. Problem

The desktop model is highly capable but shares a GPU with games and BlueStacks.

The reference desktop:

```text
RTX 5070 Ti
16,303 MB total VRAM
```

Normal desktop + BlueStacks:

```text
Used: ~3.1-3.3 GB
Free: ~12.7-12.8 GB
```

After loading `gpt-oss:20b`:

```text
Used: ~15.7 GB
Free: ~0.3-0.5 GB
Ollama processor: 100% GPU
```

Therefore the model itself adds roughly 12.5 GB of VRAM use.

---

## 2. Why free VRAM is better than GPU utilisation

A game can:

- hold many GB of VRAM;
- show moderate instantaneous GPU utilisation;
- still make loading a 12 GB model undesirable.

For model placement, framebuffer availability is a more direct resource signal than instantaneous GPU utilisation.

GPU utilisation is still useful for observability and future policy.

---

## 3. The critical residency edge case

Never implement only:

```python
if free_vram_mb >= 12000:
    DESKTOP
else:
    CLOUD
```

After GPT-OSS loads, free VRAM is intentionally tiny.

The next request would incorrectly go to cloud.

Correct decision:

```python
if desktop_model_loaded():
    DESKTOP
elif gpu_unreachable():
    CLOUD
elif free_vram_mb >= MIN_FREE_VRAM_MB:
    DESKTOP
else:
    CLOUD
```

---

## 4. Windows GPU telemetry

`windows/gpu-status.ps1` creates:

```text
GET http://<desktop>:8098/gpu
```

Example response:

```json
{
  "used_mb": 3286,
  "total_mb": 16303,
  "free_mb": 12710,
  "gpu_name": "NVIDIA GeForce RTX 5070 Ti",
  "utilisation": 5
}
```

It calls:

```powershell
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu --format=csv,noheader,nounits
```

---

## 5. Windows firewall

Run from **Administrator PowerShell**.

Single-line form avoids PowerShell backtick/paste problems:

```powershell
New-NetFirewallRule -DisplayName "Jarvis GPU Status" -Direction Inbound -Protocol TCP -LocalPort 8098 -RemoteAddress 192.168.0.121 -Action Allow
```

If you see:

```text
Access is denied
```

the shell is not elevated.

---

## 6. Test from the router host

```bash
curl -s http://192.168.0.50:8098/gpu
```

Do not modify routing logic until this works reliably.

---

## 7. Initial threshold

Reference initial threshold:

```python
MIN_FREE_VRAM_MB = 12000
```

This was chosen because:

```text
Normal BlueStacks state: ~12.7 GB free
Model additional footprint: ~12.5 GB
```

This is an operational threshold, not a universal constant.

Tune it for:

- your GPU;
- model quantisation;
- context size;
- game VRAM behaviour;
- whether spill to CPU/system RAM is acceptable.

---

## 8. How model residency is checked

The router queries desktop Ollama:

```text
GET http://192.168.0.50:11434/api/ps
```

It searches the returned models for:

```text
gpt-oss:20b
```

If found, the model is already loaded and is eligible regardless of low free VRAM.

---

## 9. Proving the fallback without launching a game

A useful safe test is to temporarily raise the threshold above total practical free VRAM.

Example:

```bash
sed -i 's/MIN_FREE_VRAM_MB = 12000/MIN_FREE_VRAM_MB = 15000/' /usr/local/bin/jarvis-route
```

With the model stopped:

```powershell
ollama stop gpt-oss:20b
```

Then ask a D question.

Expected:

```text
route=CLOUD
classifier=D
reason=insufficient_vram
```

Restore:

```bash
sed -i 's/MIN_FREE_VRAM_MB = 15000/MIN_FREE_VRAM_MB = 12000/' /usr/local/bin/jarvis-route
```

---

## 10. Future enhancements

Possible additional desktop policy:

```text
Desktop eligible if:
- host reachable;
- Ollama reachable;
- model already resident OR enough free VRAM;
- optional game state allows it;
- optional GPU utilisation below threshold;
- optional user override is enabled.
```

Home Assistant itself could eventually expose:

```text
sensor.jarvis_desktop_free_vram
binary_sensor.jarvis_desktop_llm_available
sensor.jarvis_last_route
sensor.jarvis_last_fallback_reason
```

These are optional observability features, not required for core routing.
