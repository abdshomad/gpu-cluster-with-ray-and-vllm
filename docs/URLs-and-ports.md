# URLs and Ports Reference

**Important**: When accessing services from outside the Docker host or from a remote machine, replace `localhost` with the actual server IP address. The default server IP shown in examples is `10.10.10.13` (verify with `hostname -I`).

## Service Endpoints

### Ray Serve API (Direct Access)
- **URL**: `http://localhost:8000`
- **Models Endpoint**: `http://localhost:8000/v1/models`
- **Chat Completions**: `http://localhost:8000/v1/chat/completions`
- **Port**: 8000 (configurable via `RAY_API_PORT`)

### Ray Dashboard
- **URL**: `http://localhost:8265`
- **Port**: 8265 (configurable via `RAY_DASHBOARD_PORT`)

### Nginx Reverse Proxy (if running)
- **URL**: `http://localhost` (port 80)
- **Models Endpoint**: `http://localhost/v1/models`
- **Chat Completions**: `http://localhost/v1/chat/completions`
- **Port**: 80 (configurable via `NGINX_HTTP_PORT`)
- **Note**: Nginx proxies requests to Ray Serve backend

### Grafana
- **URL**: `http://localhost:13000` or `http://localhost/grafana` (via Nginx)
- **Port**: 13000 (configurable via `GRAFANA_PORT`)

### Prometheus
- **URL**: `http://localhost:19090` or `http://localhost/prometheus` (via Nginx)
- **Port**: 19090 (configurable via `PROMETHEUS_PORT`)

## Quick Reference

| Service | Direct Port | URL | Via Nginx |
|---------|-------------|-----|-----------|
| Ray Serve API | 8000 | `http://localhost:8000/v1/models` | `http://localhost/v1/models` |
| Ray Dashboard | 8265 | `http://localhost:8265` | `http://localhost/dashboard` |
| Grafana | 13000 | `http://localhost:13000` | `http://localhost/grafana` |
| Prometheus | 19090 | `http://localhost:19090` | `http://localhost/prometheus` |
| Health Check | 8000 | `http://localhost:8000/health` | `http://localhost/health` |

## Testing Multi-Model Deployment

When testing AA001, use these URLs:

1. **List Models**: 
   - `http://localhost:8000/v1/models` (direct)
   - `http://localhost/v1/models` (via Nginx)

2. **Test Inference**:
   ```bash
   curl http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "meta-llama/Llama-3.2-1B-Instruct", "messages": [{"role": "user", "content": "Hello"}]}'
   ```

3. **Ray Dashboard**:
   - `http://localhost:8265` (direct)
   - `http://localhost/dashboard` (via Nginx)

