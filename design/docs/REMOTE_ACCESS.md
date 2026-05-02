# Remote Access via Tailscale

Share SpaceCDF running on your laptop with remote collaborators.
Tailscale creates a private encrypted network — no open ports, no
public URLs, no firewall changes needed.

## Setup (one-time, ~5 minutes)

### On your laptop (the host)

1. **Install Tailscale:**
   ```bash
   # macOS
   brew install tailscale
   # Or download from https://tailscale.com/download/mac
   ```

2. **Start Tailscale and log in:**
   ```bash
   # Start the daemon
   sudo tailscaled &

   # Log in (opens browser for auth)
   tailscale up
   ```
   This gives your laptop a Tailscale IP (e.g. `100.x.y.z`).

3. **Check your Tailscale IP:**
   ```bash
   tailscale ip -4
   # Output: 100.x.y.z
   ```

4. **Start SpaceCDF bound to all interfaces:**
   ```bash
   cd SpaceCDF
   source .venv/bin/activate

   # Backend — bind to 0.0.0.0 so Tailscale can reach it
   uvicorn spacecdf_server.app:app --host 0.0.0.0 --port 8000 &

   # Frontend — bind to 0.0.0.0
   cd frontend && npm run dev -- --host 0.0.0.0 &
   ```

### On collaborator's machine (the client)

1. **Install Tailscale:**
   ```bash
   # macOS
   brew install tailscale

   # Windows — download from https://tailscale.com/download/windows
   # Linux — https://tailscale.com/download/linux
   ```

2. **Start and join the same Tailscale network:**
   ```bash
   sudo tailscaled &
   tailscale up
   ```
   Log in with the SAME Tailscale account (or use Tailscale sharing
   to invite them to your network).

3. **Open SpaceCDF in browser:**
   ```
   http://100.x.y.z:5173
   ```
   Replace `100.x.y.z` with the host's Tailscale IP.

That's it. No firewall rules, no VPN configuration, no port forwarding.

## Tailscale pricing

- **Free tier (Personal):** Up to 100 devices, 3 users. Plenty for
  a small team doing CDF sessions.
- **Starter:** $5/user/month for teams.
- No bandwidth limits on any tier.

## Alternative: Tailscale Funnel (no client install needed)

If collaborators can't install Tailscale, you can use Tailscale Funnel
to create a public HTTPS URL:

```bash
tailscale funnel 5173
# Output: https://your-machine.tail12345.ts.net/
```

This gives a public URL that anyone can access — no install needed on
their side. Good for demos. Disable when not in use.

## Security notes

- Tailscale traffic is end-to-end encrypted (WireGuard).
- Only devices on your Tailscale network can connect.
- The SpaceCDF API key (if set) stays on YOUR laptop in .env.
- Collaborators' API keys (if they use AI features) stay in THEIR
  browser localStorage — never sent to your server for storage.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection refused" | Check SpaceCDF is bound to 0.0.0.0, not 127.0.0.1 |
| Can't see Tailscale IP | Run `tailscale status` to check connection |
| Slow performance | Tailscale uses direct connections when possible; if relayed, check network |
| CORS errors | Backend CORS config allows all origins by default — should work |
