# Installation Guide

This document walks through the reference build from the model layer upward.

---

## 1. Lightweight Ollama host

Reference host:

```text
Debian LXC
192.168.0.39
Ollama port 11434
```

Reference model:

```text
qwen3:4b-instruct-2507-q4_K_M
```

The reference host used Intel iGPU Vulkan acceleration and an 8192-token context window.

Example Ollama systemd environment:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_KEEP_ALIVE=-1"
Environment="OLLAMA_VULKAN=1"
Environment="OLLAMA_IGPU_ENABLE=1"
```

Verify:

```bash
systemctl daemon-reload
systemctl restart ollama
ollama ps
```

For the reference deployment, `ollama ps` showed the Qwen model fully GPU-offloaded and resident.

The optional preload script is in:

```text
scripts/ollama-preload.sh
```

---

## 2. Desktop Ollama

Reference:

```text
Windows desktop
192.168.0.50:11434
NVIDIA RTX 5070 Ti 16 GB
gpt-oss:20b
```

Ensure Ollama is reachable from the LAN.

A typical Windows configuration needs Ollama bound to:

```text
0.0.0.0:11434
```

Test from the LiteLLM host:

```bash
curl http://192.168.0.50:11434/api/tags
```

Reference model measurements:

```text
gpt-oss:20b size: around 12-13 GB
Warm inference: much faster than cold load
Processor: 100% GPU when enough VRAM was available
```

A larger Qwen 30B model was tested but spilled between GPU and CPU on a 16 GB GPU and was too slow for voice use. GPT-OSS 20B was the better practical tier.

---

## 3. Install LiteLLM

Reference installation:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
uv tool install 'litellm[proxy]'
```

Executable:

```text
/root/.local/bin/litellm
```

Copy:

```text
config/litellm/config.yaml.example
```

to:

```text
/etc/litellm/config.yaml
```

and edit the addresses/model IDs.

Copy the service:

```bash
cp systemd/litellm.service /etc/systemd/system/litellm.service
systemctl daemon-reload
systemctl enable --now litellm
```

Verify:

```bash
systemctl status litellm
curl http://127.0.0.1:4000/health
```

---

## 4. Configure LiteLLM aliases

The reference design uses:

```text
qwen-local
llm-desktop
llm-cloud
```

Why aliases matter:

- downstream clients do not need the provider-specific model path;
- models can be replaced without changing every caller;
- troubleshooting can target a stable logical name.

However, remember that this project does not rely on LiteLLM itself to choose L/D/C.

---

## 5. Home Assistant conversation agents

Create and test three agents before installing Jarvis Router.

### Local

Example:

```text
Entity: conversation.qwen_litellm
Backend: Home Assistant LiteLLM integration
Model: qwen-local
Control Home Assistant: OFF
```

This is deliberate.

Enabling HA control caused a much larger tool prompt in the reference deployment and made the small model unsuitable for low-latency voice use.

### Desktop

Example:

```text
Entity: conversation.ollama_conversation_desktop
Backend: Home Assistant Ollama integration
Model: gpt-oss:20b
Control Home Assistant: ON
```

Expose only the entities/actions you actually want it to see.

### Cloud

Example:

```text
Entity: conversation.openai_conversation
Backend: Home Assistant OpenAI integration
Control Home Assistant: ON
Web search: as desired
```

The direct OpenAI HA agent is useful because Home Assistant owns its tool and web-search configuration.

---

## 6. Test every downstream agent directly

Use Developer Tools -> Actions -> `conversation.process`.

Desktop example:

```yaml
action: conversation.process
data:
  agent_id: conversation.ollama_conversation_desktop
  text: "How much solar am I generating now?"
response_variable: response
```

Cloud example:

```yaml
action: conversation.process
data:
  agent_id: conversation.openai_conversation
  text: "How much solar am I generating now?"
response_variable: response
```

Do not build the router until these work.

---

## 7. Router environment

Copy:

```text
config/jarvis-router.env.example
```

to:

```text
/etc/jarvis-router.env
```

Fill in the real values.

Permissions:

```bash
chmod 600 /etc/jarvis-router.env
```

Important syntax:

```bash
ROUTER_API_KEY=value
```

not:

```text
ROUTER_API_KEY: value
```

The colon version is not shell environment syntax.

---

## 8. Install `jarvis-route`

```bash
cp scripts/jarvis-route /usr/local/bin/jarvis-route
chmod +x /usr/local/bin/jarvis-route
```

Test:

```bash
/usr/local/bin/jarvis-route "Who wrote The Hobbit?"
```

Then:

```bash
tail -n 20 /var/log/jarvis-router.log
```

---

## 9. Install Router HTTP API

```bash
cp scripts/jarvis-router-api /usr/local/bin/jarvis-router-api
chmod +x /usr/local/bin/jarvis-router-api
```

Install systemd unit:

```bash
cp systemd/jarvis-router.service /etc/systemd/system/jarvis-router.service
systemctl daemon-reload
systemctl enable --now jarvis-router
```

Verify:

```bash
curl http://127.0.0.1:8099/health
```

Authenticated request:

```bash
source /etc/jarvis-router.env

curl -s http://127.0.0.1:8099/route \
  -H "Authorization: Bearer $ROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text":"Who wrote The Hobbit?"}'
```

Expected shape:

```json
{"speech":"J.R.R. Tolkien wrote The Hobbit."}
```

---

## 10. Install the Home Assistant custom component

Copy:

```text
home-assistant/custom_components/jarvis_router/
```

to the Home Assistant config custom-components directory.

Internal HA path:

```text
/config/custom_components/jarvis_router/
```

If using the Home Assistant File Editor add-on, the visible root may already correspond to `/config`.

In the reference system the user saw:

```text
homeassistant/custom_components
```

rather than a literal `/config` directory. Do not create a nested `config` directory if `configuration.yaml` is already at that File Editor root.

Run:

```bash
ha core check
```

Then restart HA if validation passes.

Add the **Jarvis Router** integration from:

```text
Settings -> Devices & services -> Add integration
```

Router URL:

```text
http://192.168.0.121:8099
```

API key:

```text
the ROUTER_API_KEY stored in /etc/jarvis-router.env
```

Expected conversation entity:

```text
conversation.jarvis_router
```

---

## 11. Test the custom component before voice

```yaml
action: conversation.process
data:
  agent_id: conversation.jarvis_router
  text: "How much solar am I generating now?"
response_variable: response
```

Only after this works should the voice pipeline be changed.

---

## 12. Switch the voice pipeline

Keep:

```text
Prefer handling commands locally = ON
```

Set:

```text
Conversation agent = Jarvis Router
```

Recommended test set:

```text
Who wrote The Hobbit?
How much solar am I generating now?
What will the weather be like tomorrow?
```

Check:

```bash
tail -f /var/log/jarvis-router.log
```

---

## 13. Add GPU-aware routing

Follow:

```text
docs/gpu-aware-routing.md
```

Do this after basic L/D/C routing works.
