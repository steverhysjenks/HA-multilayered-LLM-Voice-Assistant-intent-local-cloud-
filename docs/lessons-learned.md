# Lessons Learned

## 1. Small models are excellent when their job is small

Qwen 4B was a good fit for:

- classification;
- simple general knowledge;
- low-cost local conversation.

It was a poor fit for ingesting a large Home Assistant tool schema while maintaining voice-grade latency.

Design tasks around model capability rather than expecting every tier to do everything.

---

## 2. Tool context can matter more than model generation speed

The local model itself was not inherently slow.

With a small prompt it responded quickly.

With Home Assistant tool context enabled, the prompt became several thousand tokens and voice latency became unacceptable.

The architecture changed from:

```text
small model + all HA tools
```

to:

```text
small model for routing/general knowledge
larger model for tools
```

This was a major improvement.

---

## 3. A model gateway and an agent router solve different problems

LiteLLM makes backends interchangeable.

Jarvis decides which capability is needed.

Home Assistant supplies the capability-specific context.

Keeping these concerns separate makes the system easier to reason about.

---

## 4. Re-entering Home Assistant is the key integration trick

Instead of trying to transport Home Assistant's tools across model backends, Jarvis selects a Home Assistant agent and calls the Conversation API.

That preserves Home Assistant's own:

- entity exposure;
- tool configuration;
- conversation prompts;
- web-search settings.

---

## 5. Measure resource use on the real desktop workload

BlueStacks runs nearly continuously on the reference desktop.

Therefore "idle desktop" really means:

```text
Windows + BlueStacks + normal background apps
```

Thresholds based on an artificial clean boot would not reflect the actual system.

Measure the environment you really use.

---

## 6. Model residency changes how resource policy must work

This was an important design correction.

Before loading:

```text
free VRAM tells us whether the model can fit
```

After loading:

```text
free VRAM is low because the model already fits
```

Resource policy needs to understand state, not only a threshold.

---

## 7. Test each layer directly

The most effective troubleshooting pattern was:

```text
backend
↓
gateway
↓
HA downstream agent
↓
router CLI
↓
router HTTP API
↓
HA custom component
↓
voice satellite
```

When repeated-token failures happened, direct Ollama tests showed the problem existed below LiteLLM.

This prevented unnecessary changes at higher layers.

---

## 8. Keep routing observable

A log such as:

```text
reason=insufficient_vram
```

is much more useful than merely:

```text
route=CLOUD
```

The system should explain its policy decision.

---

## 9. Voice prompts should optimise for speech, not chat

Cloud models can produce excellent but excessive prose.

TTS-friendly prompts should explicitly constrain:

- sentence count;
- units;
- irrelevant metadata;
- hourly breakdowns;
- repeated values.

---

## 10. Give Home Assistant deterministic derived data

An LLM should not have to infer daily energy use from a lifetime meter when Home Assistant can compute it precisely.

Create purpose-built helpers and scripts.

This improves:

- correctness;
- token use;
- latency;
- explainability.

---

## 11. Back up every working checkpoint

During the build we used checkpoint copies such as:

```text
/usr/local/bin/jarvis-route.classifier-working
/usr/local/bin/jarvis-route.pre-gpu-aware
```

When experimenting with routing, small backups make rollback trivial.

For a Git-managed version, commits/tags should serve the same purpose.

---

## 12. Voice latency is a design constraint

For an interactive voice assistant:

```text
"works eventually"
```

is not enough.

Avoid using timeout increases as the primary fix for model/context mismatch.

Choose faster paths and smaller prompts instead.
