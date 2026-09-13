# Troubleshooting

## 1. Qwen becomes extremely slow when HA tools are enabled

### Symptom

Simple questions take tens of seconds.

### Cause

Home Assistant may provide a substantial tool/entity schema. A small local model must ingest and reason over that context before producing a response.

### Fix used in this architecture

```text
conversation.qwen_litellm
Control Home Assistant = OFF
```

Keep HA tool use on larger desktop/cloud agents.

---

## 2. Repeated tokens such as `F F F F...` or `I I I...`

The reference local Ollama host occasionally produced repeated-token/gibberish behaviour.

Direct Ollama calls also failed, proving LiteLLM was not the root cause.

Restarting Ollama restored normal behaviour.

Troubleshooting principle:

> Test the lowest layer directly before blaming the gateway above it.

Do not immediately redesign the whole stack when a backend itself is unhealthy.

---

## 3. Router API says unauthorized

Check:

```bash
source /etc/jarvis-router.env
echo ${#ROUTER_API_KEY}
```

One observed mistake was:

```text
ROUTER_API_KEY:
```

instead of:

```text
ROUTER_API_KEY=
```

Restart `jarvis-router` after changing its environment file:

```bash
systemctl restart jarvis-router
```

---

## 4. Home Assistant File Editor does not show `/config`

The add-on may present `/config` as its visible root.

If `configuration.yaml` and `custom_components` are already at the visible root, create:

```text
custom_components/jarvis_router/
```

there.

Do not create:

```text
config/custom_components/...
```

inside that root.

---

## 5. Windows firewall command says `Access is denied`

`New-NetFirewallRule` requires Administrator PowerShell.

Open PowerShell using **Run as administrator**.

---

## 6. PowerShell multiline firewall command will not execute

PowerShell backticks are line-continuation characters and can be awkward when pasted.

Use the one-line form:

```powershell
New-NetFirewallRule -DisplayName "Jarvis GPU Status" -Direction Inbound -Protocol TCP -LocalPort 8098 -RemoteAddress 192.168.0.121 -Action Allow
```

---

## 7. GPU router sends second desktop request to cloud

If you wrote policy using only free VRAM, the second request sees almost no free VRAM because GPT-OSS is already resident.

Fix:

```text
Check Ollama /api/ps first.
If model is already loaded -> desktop.
Only apply free-VRAM threshold when the model is NOT loaded.
```

---

## 8. Cloud weather answer is too verbose

The route is correct; this is downstream prompt behaviour.

Add instructions to the OpenAI conversation agent, for example:

```text
Keep spoken responses concise and natural.

For weather:
- use Celsius only;
- do not include Fahrenheit;
- omit sunrise/sunset unless asked;
- do not provide an hourly forecast unless asked;
- summarise conditions, temperatures, rain and meaningful wind;
- aim for 1-3 short sentences.
```

---

## 9. Local factual answer sounds abrupt

Do not slow inference merely to make TTS feel less abrupt.

Try downstream prompt wording such as:

```text
For simple factual questions, answer in one natural spoken sentence rather than the shortest possible phrase.
```

TTS speed/voice settings are a separate concern from LLM latency.

---

## 10. Energy question returns cumulative kWh

Example wrong interpretation:

```text
"The energy meter reports 1132.6 kWh so far today."
```

If the exposed entity is a lifetime/cumulative meter, the model is not necessarily able to derive today's delta.

Create a daily helper/entity/script and expose that instead.

---

## 11. HTTP router works for one request but a local response is blank

A transient blank local response was seen during development while other routes still worked.

Suggested troubleshooting order:

1. retry the exact CLI `jarvis-route` call;
2. call the local Home Assistant conversation agent directly;
3. call LiteLLM `qwen-local` directly;
4. call Ollama directly;
5. inspect logs.

This narrows the failing layer.

---

## 12. `chmod` command accidentally includes `tail`

If commands are pasted together without a newline, something like:

```text
chmod +x /usr/local/bin/jarvis-routetail -n 20 ...
```

will fail with a `chmod` option error.

It does not modify the intended script.

Simply run:

```bash
chmod +x /usr/local/bin/jarvis-route
tail -n 20 /var/log/jarvis-router.log
```

as separate commands.

---

## 13. Desktop D route falls back even though machine is on

Check both services independently:

```bash
curl http://192.168.0.50:11434/api/ps
curl http://192.168.0.50:8098/gpu
```

Possible causes:

- Windows is asleep;
- Ollama is not listening on the LAN;
- GPU-status scheduled task is not running;
- firewall is blocking 8098;
- free VRAM is below threshold.

Use the router's `reason=` log field to identify the policy decision.
