#!/bin/bash
#
# Optional preload helper for the lightweight Ollama LXC.
#
# Purpose:
# - wait until Ollama is responding;
# - load the Qwen model;
# - request an 8192-token context;
# - keep it resident indefinitely.
#
# This was useful for the always-on lightweight tier.
# Do NOT blindly apply the same strategy to a gaming desktop because a
# permanently resident 12+ GB desktop model can consume most of the GPU.

set -e

until curl -sf http://127.0.0.1:11434/api/tags >/dev/null; do
    sleep 1
done

curl -sf \
    -H "Content-Type: application/json" \
    http://127.0.0.1:11434/api/generate \
    -d '{
        "model": "qwen3:4b-instruct-2507-q4_K_M",
        "prompt": "",
        "keep_alive": -1,
        "stream": false,
        "options": {
            "num_ctx": 8192
        }
    }'
