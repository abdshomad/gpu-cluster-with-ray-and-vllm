# Cloudflare Tunnel Setup for Ray Dashboard

This guide explains how to properly expose the Ray Serve Dashboard via Cloudflare Tunnel to avoid 502 errors on static assets.

## Problem

When exposing the Ray Dashboard directly via Cloudflare tunnel to port `8265`, static assets (JavaScript, CSS files) may fail with `502 Bad Gateway` errors. This happens because:

1. Cloudflare tunnel may not properly proxy all paths when pointing directly to the Ray Dashboard
2. Static assets are served at paths like `/static/js/main.04f2f7fe.js` and need proper proxying
3. Direct proxying can cause path rewriting issues

## Solution: Use Nginx as Proxy

The recommended approach is to use Nginx as an intermediary proxy, which properly handles all requests including static assets.

### Step 1: Update Your Cloudflare Tunnel Configuration

Point your Cloudflare tunnel to **Nginx port 80** (or your configured `NGINX_HTTP_PORT`) instead of directly to Ray Dashboard port `8265`.

**Cloudflare Tunnel Configuration (`config.yml`):**
```yaml
tunnel: <your-tunnel-id>
credentials-file: /path/to/credentials.json

ingress:
  - hostname: gpu-cluster-dashboard.demoin.id
    service: http://localhost:80
    # Or if you customized the port:
    # service: http://localhost:${NGINX_HTTP_PORT}
  # ... other ingress rules
```

**Or using `cloudflared` command:**
```bash
cloudflared tunnel --url http://localhost:80
```

### Step 2: Restart Nginx Container

After updating the nginx configuration, restart the nginx container to apply changes:

```bash
cd docker
docker compose restart nginx
```

Or if you want to rebuild:
```bash
docker compose up -d --force-recreate nginx
```

### Step 3: Verify Configuration

1. Check that nginx is running:
   ```bash
   docker compose ps nginx
   ```

2. Test the dashboard locally through nginx:
   ```bash
   curl -I http://localhost:80/
   ```

3. Verify static assets are accessible:
   ```bash
   curl -I http://localhost:80/static/js/main.04f2f7fe.js
   ```

## Alternative: Direct Port 8265 (Not Recommended)

If you must expose port `8265` directly via Cloudflare tunnel, ensure your Cloudflare tunnel configuration properly handles all paths:

**Cloudflare Tunnel Configuration:**
```yaml
tunnel: <your-tunnel-id>
credentials-file: /path/to/credentials.json

ingress:
  - hostname: gpu-cluster-dashboard.demoin.id
    service: http://localhost:8265
    originRequest:
      # Ensure all paths are proxied
      noHappyEyeballs: false
      # Increase timeout for large responses
      connectTimeout: 30s
      tcpKeepAlive: 30s
      # Disable compression to avoid issues
      disableChunkedEncoding: false
  # Catch-all rule
  - service: http_status:404
```

However, this approach is less reliable and may still have issues with static assets.

## Troubleshooting

### 502 Bad Gateway on Static Assets

If you still see 502 errors:

1. **Check nginx logs:**
   ```bash
   docker compose logs nginx
   ```

2. **Verify Ray Dashboard is accessible from nginx:**
   ```bash
   docker compose exec nginx wget -O- http://ray-serve:8265/
   ```

3. **Check Cloudflare tunnel logs:**
   ```bash
   cloudflared tunnel info <tunnel-name>
   ```

4. **Verify firewall rules** - Ensure port 80 (or your NGINX_HTTP_PORT) is accessible locally

### Static Assets Loading Slowly

If static assets are loading but very slowly:

1. The nginx configuration includes increased buffer sizes (`proxy_buffer_size`, `proxy_buffers`, etc.)
2. Check your Cloudflare tunnel bandwidth settings
3. Verify your server's network connection

## Configuration Summary

The updated nginx configuration:
- Proxies root path (`/`) to Ray Dashboard at `http://ray-serve:8265/`
- Handles all static assets (`/static/*`) correctly
- Supports WebSocket connections for real-time dashboard updates
- Includes proper headers for proxying
- Uses `^~` modifiers for specific paths (`/v1`, `/dashboard`, etc.) to ensure correct routing

## Access Points

After configuration, your dashboard will be accessible at:
- **Via Cloudflare Tunnel:** `https://gpu-cluster-dashboard.demoin.id/` (or your configured domain)
- **Via Nginx (local):** `http://localhost:80/` or `http://localhost:${NGINX_HTTP_PORT}/`
- **Via Nginx at /dashboard:** `http://localhost:80/dashboard`
- **Direct (local only):** `http://localhost:${RAY_DASHBOARD_PORT}/` (default: 8265)

