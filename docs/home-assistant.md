# Home Assistant Integration

## 1. Conversation agents in the reference build

```text
conversation.home_assistant
conversation.openai_conversation
conversation.ollama_conversation_desktop
conversation.ollama_conversation_lxc
conversation.qwen_litellm
conversation.jarvis_router
```

Not every deployment needs all of them.

---

## 2. Downstream instructions belong downstream

The custom Jarvis conversation component does not expose an instruction cog because it is not itself an LLM.

Prompts belong to the actual answer-generating agents:

```text
LOCAL
└── conversation.qwen_litellm
    └── LiteLLM conversation-agent instructions

DESKTOP
└── conversation.ollama_conversation_desktop
    └── Ollama conversation-agent instructions

CLOUD
└── conversation.openai_conversation
    └── OpenAI conversation-agent instructions
```

This is a feature, not a limitation. Each tier can have different behaviour and permissions.

Example prompts are provided in `home-assistant/prompts`.

---

## 3. Entity exposure

Expose only entities the LLM genuinely needs.

Home Assistant tool context can become large quickly.

In the reference deployment, enabling HA control on the small Qwen agent expanded requests from roughly hundreds of tokens to several thousand tokens and caused response times around tens of seconds.

The solution was:

```text
Small Qwen agent:
Control Home Assistant = OFF

Desktop GPT-OSS:
Control Home Assistant = ON

Cloud OpenAI:
Control Home Assistant = ON
```

The small model remains a fast general-knowledge tier.

---

## 4. Derived entities beat raw cumulative sensors

An LLM can only reason over what Home Assistant supplies.

If the only exposed sensor is:

```text
Total imported energy = 1132.6 kWh
```

then the question:

```text
"How much energy did I use today?"
```

may produce a misleading answer because the entity is cumulative.

Home Assistant's Energy dashboard may internally derive daily consumption, but that does not mean the LLM has a convenient entity representing "today".

Prefer explicit entities/helpers such as:

```text
sensor.house_energy_today
sensor.house_energy_yesterday
sensor.solar_energy_today
sensor.solar_energy_yesterday
```

Possible HA mechanisms include:

- Utility Meter;
- template sensors;
- statistics helpers;
- scripts that return a deterministic calculated result.

The wider principle is:

> Use Home Assistant for deterministic home logic; use the LLM for language.

---

## 5. Scripts as voice tools

A useful later evolution is to expose higher-level Home Assistant scripts rather than dozens of raw entities.

Examples:

```text
script.get_energy_summary
script.bedtime
script.prepare_movie_night
script.get_solar_summary
```

The script can:

- calculate values;
- choose correct sensors;
- run deterministic actions;
- enforce safeguards.

The LLM then needs to recognise intent and invoke the appropriate tool rather than reconstruct household logic itself.

---

## 6. Custom component behaviour

`conversation.jarvis_router` does only this:

```text
user text
↓
POST router /route
↓
receive speech
↓
add assistant text to HA chat log
↓
return ConversationResult
```

It deliberately does not call HA tools directly.

The selected downstream HA agent is responsible for tools.

---

## 7. Current Home Assistant API model

The custom component uses the current `ConversationEntity` pattern and implements:

```python
async def _async_handle_message(
    self,
    user_input,
    chat_log,
):
```

It adds the response to Home Assistant's chat log and returns a `ConversationResult`.

This replaced older patterns that directly used `async_process` for custom conversation entities.

---

## 8. Testing agent IDs

A useful template in Developer Tools:

```yaml
action: conversation.process
data:
  agent_id: conversation.jarvis_router
  text: "Who wrote The Hobbit?"
response_variable: response
```

To inspect available conversation entities in a template:

```jinja
{{ states.conversation | map(attribute='entity_id') | list }}
```
