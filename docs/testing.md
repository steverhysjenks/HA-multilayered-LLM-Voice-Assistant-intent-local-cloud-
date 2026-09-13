# Test Plan

Treat routing as a chain of independently testable boundaries.

---

## 1. Lightweight Ollama

```bash
curl http://192.168.0.39:11434/api/tags
```

Direct generation should work before LiteLLM is introduced.

---

## 2. Desktop Ollama

From the router/LiteLLM host:

```bash
curl http://192.168.0.50:11434/api/tags
```

Windows:

```powershell
ollama ps
```

---

## 3. LiteLLM aliases

Test each configured alias directly before Home Assistant.

Example endpoint:

```text
http://127.0.0.1:4000/v1/chat/completions
```

Use the LiteLLM master/virtual key.

---

## 4. Home Assistant downstream agents

### LOCAL

```yaml
action: conversation.process
data:
  agent_id: conversation.qwen_litellm
  text: "Who wrote The Hobbit?"
response_variable: response
```

### DESKTOP

```yaml
action: conversation.process
data:
  agent_id: conversation.ollama_conversation_desktop
  text: "How much solar am I generating now?"
response_variable: response
```

### CLOUD

```yaml
action: conversation.process
data:
  agent_id: conversation.openai_conversation
  text: "What will the weather be like tomorrow?"
response_variable: response
```

---

## 5. CLI router

```bash
/usr/local/bin/jarvis-route "Who wrote The Hobbit?"
/usr/local/bin/jarvis-route "How much solar am I generating now?"
/usr/local/bin/jarvis-route "What will the weather be like tomorrow?"
```

Watch:

```bash
tail -f /var/log/jarvis-router.log
```

Expected:

```text
L -> LOCAL
D -> DESKTOP or CLOUD fallback
C -> CLOUD
```

---

## 6. Router API

Health:

```bash
curl http://127.0.0.1:8099/health
```

Authenticated route:

```bash
source /etc/jarvis-router.env

curl -s http://127.0.0.1:8099/route \
  -H "Authorization: Bearer $ROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text":"How much solar am I generating now?"}'
```

---

## 7. GPU endpoint

Windows local:

```powershell
curl.exe http://127.0.0.1:8098/gpu
```

Router LXC:

```bash
curl -s http://192.168.0.50:8098/gpu
```

---

## 8. GPU route: model unloaded

Windows:

```powershell
ollama stop gpt-oss:20b
ollama ps
```

Router:

```bash
/usr/local/bin/jarvis-route "How much solar am I generating now?"
tail -n 3 /var/log/jarvis-router.log
```

Expected when free VRAM is above threshold:

```text
reason=sufficient_free_vram
model_loaded=no
route=DESKTOP
```

---

## 9. GPU route: model loaded

Immediately ask another D request.

Expected:

```text
reason=model_already_loaded
model_loaded=yes
route=DESKTOP
```

The free-VRAM value may be only a few hundred MB. This is correct.

---

## 10. GPU route: forced fallback

Temporarily set an impossible threshold such as 15000 MB while the model is unloaded.

Expected:

```text
reason=insufficient_vram
route=CLOUD
```

Restore the real threshold immediately afterwards.

---

## 11. HA custom component

```yaml
action: conversation.process
data:
  agent_id: conversation.jarvis_router
  text: "How much solar am I generating now?"
response_variable: response
```

Do not move to real voice until this passes.

---

## 12. Voice tests

With `Prefer handling commands locally` enabled:

```text
"Turn on the kitchen light."
```

Expected: native HA path.

```text
"Who wrote The Hobbit?"
```

Expected: LOCAL.

```text
"How much solar am I generating now?"
```

Expected: DESKTOP if eligible.

```text
"What will the weather be like tomorrow?"
```

Expected: CLOUD unless Home Assistant itself satisfies it before Jarvis.

---

## 13. Useful log commands

Last 20:

```bash
tail -n 20 /var/log/jarvis-router.log
```

Follow live:

```bash
tail -f /var/log/jarvis-router.log
```

Services:

```bash
systemctl status litellm
systemctl status jarvis-router
journalctl -u jarvis-router -f
journalctl -u litellm -f
```
