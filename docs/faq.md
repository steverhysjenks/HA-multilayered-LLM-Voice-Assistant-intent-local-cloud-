# FAQ

## Is LiteLLM the router?

No.

LiteLLM is a model/API gateway.

In this implementation:

```text
Qwen = classifier model
jarvis-route = orchestration logic
LiteLLM = model gateway
Home Assistant = tool/context owner
```

---

## Why not configure LiteLLM to switch between Qwen, desktop and cloud directly?

You can route models inside LiteLLM, but this project's key requirement is not only model selection.

The desktop and cloud routes need their own Home Assistant conversation-agent configuration:

- HA tools;
- exposed entities;
- instructions;
- search features;
- permissions.

Therefore Jarvis chooses an HA agent and calls Home Assistant again.

---

## Does `conversation.qwen_litellm` carry its HA entities into the desktop route?

No.

The local Qwen agent deliberately has HA control disabled.

When Jarvis chooses D, it calls:

```text
conversation.ollama_conversation_desktop
```

Home Assistant then builds a fresh request using the desktop agent's own context/tools.

---

## Why is there no instruction cog beside Jarvis Router in the voice pipeline?

Because Jarvis Router is not the answer-generating LLM.

Configure instructions on:

```text
conversation.qwen_litellm
conversation.ollama_conversation_desktop
conversation.openai_conversation
```

---

## Why keep Home Assistant's `Prefer handling commands locally` option enabled?

Because native commands are faster and deterministic.

An LLM should not be needed to perform:

```text
"Turn off the bedroom light."
```

Native HA intent handling gets first refusal.

---

## Why is Qwen used to classify instead of Python keywords?

Natural-language classification is more flexible than maintaining a large keyword list.

The Python program still owns policy.

For example:

```text
Qwen says D
Python decides whether D means desktop or cloud fallback
```

---

## Why does a D request sometimes go to OpenAI?

Because D means:

```text
"this request needs live Home Assistant context"
```

It does not mean:

```text
"must use desktop"
```

Desktop eligibility is a second decision.

If the desktop cannot safely load GPT-OSS, cloud is an HA-capable fallback.

---

## Why use free VRAM rather than just GPU percentage?

GPU utilisation is instantaneous.

A game may hold lots of VRAM while momentary compute utilisation is low.

Loading a large model depends heavily on memory availability.

---

## Why does the router ignore low free VRAM if GPT-OSS is already loaded?

Because the loaded model itself is what consumed that VRAM.

If Ollama reports the model already resident, it is ready to service the request without needing another 12+ GB allocation.

---

## Why was 12,000 MB selected?

It came from measurement on the reference RTX 5070 Ti system:

```text
Normal Windows + BlueStacks:
~12.7 GB free

GPT-OSS additional use:
~12.5 GB
```

12,000 MB was a reasonable initial operating threshold, not a universal recommendation.

---

## Should GPT-OSS be kept loaded forever?

Not automatically in a gaming desktop.

Keeping it resident removes cold-load latency but consumes almost all 16 GB VRAM.

A future policy could preload it when the desktop is idle and unload it when a game starts.

---

## Why not increase timeouts when the small model is slow?

Because voice UX is latency-sensitive.

If a model needs 40 seconds because of a huge HA tool prompt, increasing the timeout only hides the architectural problem.

Reduce context or route the task to a more suitable model.

---

## Why did a 30B desktop model perform worse than GPT-OSS 20B?

On the reference 16 GB GPU, the larger model did not fit cleanly and split work between GPU and CPU.

The 20B model fit sufficiently to run 100% GPU and was much faster for voice.

---

## Why does Home Assistant know today's energy in the Energy dashboard but the LLM may not?

The Energy dashboard can derive values internally from long-term statistics/cumulative sensors.

The conversation agent sees exposed tools/entities, not necessarily a convenient precomputed `today` entity.

Create explicit daily helpers/scripts for reliable voice questions.

---

## Can HA scripts make this better?

Yes.

Scripts let Home Assistant own deterministic household logic while the LLM handles language.

Good examples:

```text
Get today's energy summary
Get yesterday's solar generation
Run bedtime routine
Prepare movie night
```

---

## Does the custom component expose HA tools?

No.

It only forwards text to Jarvis and returns speech.

The downstream Home Assistant conversation agent supplies tools.

---

## Can I add more routes later?

Yes.

Keep the classifier output small and explicit, then map new labels to policy.

For example:

```text
L = local
D = home
C = cloud/current
X = coding
M = memory/RAG
```

Do not add complexity until there is a concrete use case.

---

## Where are routing decisions logged?

```text
/var/log/jarvis-router.log
```

Useful command:

```bash
tail -f /var/log/jarvis-router.log
```

---

## Should secrets be placed directly in Python files?

No.

Keep them in:

```text
/etc/jarvis-router.env
```

with mode `600`.

Never commit that file.
