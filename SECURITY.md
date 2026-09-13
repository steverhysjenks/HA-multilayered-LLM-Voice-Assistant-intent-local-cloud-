# Security

## Secrets used by this project

The working deployment uses:

- a LiteLLM master/API key;
- a Home Assistant long-lived access token;
- a Jarvis Router HTTP bearer token;
- an OpenAI API key.

None of these should be committed.

The examples use environment variables or placeholders.

## Recommended file permissions

For the real router environment file:

```bash
chown root:root /etc/jarvis-router.env
chmod 600 /etc/jarvis-router.env
```

## If a key is exposed

Rotate it.

Examples of exposure include:

- pasted into chat;
- committed to Git;
- included in screenshots;
- terminal history copied into an issue;
- shared in logs.

Do not rely on deleting a Git commit as the only mitigation. Treat the credential as compromised and create a new one.

## Network exposure

The reference deployment assumes a trusted private LAN.

Recommended restrictions:

- do not expose port 8098 (GPU status) to the internet;
- restrict the Windows firewall rule for port 8098 to the Jarvis/LiteLLM host;
- do not expose port 8099 (Jarvis API) publicly;
- keep the bearer token requirement on `/route`;
- ideally firewall port 8099 so only Home Assistant can reach it;
- keep Ollama endpoints private unless authentication/reverse-proxy controls are added.

The `/health` endpoint intentionally does not require authentication, but it should still remain LAN-only.
