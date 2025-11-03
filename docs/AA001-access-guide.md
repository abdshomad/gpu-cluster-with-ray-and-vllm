# AA001 Access Guide - Using Server IP

## Important: Docker Container Access

When Ray Serve runs inside a Docker container, you must use the **server's actual IP address** (not `localhost`) when accessing from:
- Another machine on the network
- A browser on a different device
- Remote API clients

## Finding Your Server IP

```bash
hostname -I | awk '{print $1}'
```

**Example Output**: `10.10.10.13`

## Access URLs

### From Docker Host (localhost works)
- Models API: `http://localhost:18000/v1/models`
- Ray Dashboard: `http://localhost:18265`

### From Remote Machine (use server IP)
- Models API: `http://10.10.10.13:18000/v1/models`
- Ray Dashboard: `http://10.10.10.13:18265`

Replace `10.10.10.13` with your actual server IP address.

## Testing Multi-Model Deployment

### 1. Check Models Endpoint

```bash
# From Docker host
curl http://localhost:18000/v1/models

# From remote machine (replace with your server IP)
curl http://10.10.10.13:18000/v1/models
```

### 2. Test in Browser

- **From Docker host**: Navigate to `http://localhost:18000/v1/models`
- **From remote machine**: Navigate to `http://<SERVER_IP>:18000/v1/models`

### 3. Expected Response

```json
{
  "object": "list",
  "data": [
    {
      "id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
      "object": "model",
      "created": null,
      "owned_by": "ray-serve"
    }
  ]
}
```

## Firewall Considerations

If you cannot access the service, check:

1. **Port is exposed**: Verify Docker port mapping
   ```bash
   docker ps | grep ray-serve
   # Should show: 0.0.0.0:18000->8000/tcp
   ```

2. **Firewall rules**: Ensure ports 18000 and 18265 are open
   ```bash
   sudo ufw allow 18000/tcp
   sudo ufw allow 18265/tcp
   ```

3. **Network connectivity**: Test from client machine
   ```bash
   telnet <SERVER_IP> 18000
   ```

## Verification

To verify AA001 implementation is working:

1. **Check logs**:
   ```bash
   docker logs ray-serve | grep "Parsed"
   # Should show: "Parsed 1 model configuration(s)" or more
   ```

2. **Test endpoint**:
   ```bash
   curl http://<SERVER_IP>:18000/v1/models | python3 -m json.tool
   ```

3. **Check Ray Dashboard**:
   - Open `http://<SERVER_IP>:18265` in browser
   - Navigate to "Serve" → "Applications"
   - Verify your model(s) are listed

## Quick Reference

| Service | Port | URL (replace <SERVER_IP>) |
|---------|------|---------------------------|
| Models API | 18000 | `http://<SERVER_IP>:18000/v1/models` |
| Ray Dashboard | 18265 | `http://<SERVER_IP>:18265` |
| Health Check | 18000 | `http://<SERVER_IP>:18000/health` |

