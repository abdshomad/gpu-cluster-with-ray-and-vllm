# GPU Cluster Platform - Site Access Guide

This document provides a comprehensive list of all accessible URLs and service endpoints for the GPU Cluster Platform.

## Quick Reference Table

| Service Name | URL (via Nginx) | URL (Direct) | Description |
|--------------|----------------|--------------|-------------|
| Ray Dashboard | `http://localhost:18081/` | `http://localhost:18265` | Ray Serve Dashboard - Cluster monitoring interface |
| Ray API | `http://localhost:18081/v1` | `http://localhost:18000` | OpenAI-compatible API endpoint for LLM inference |
| Grafana | `http://localhost:18081/grafana` | `http://localhost:13000` | Metrics visualization dashboard (requires login) |
| Prometheus | `http://localhost:18081/prometheus` | `http://localhost:19090` | Metrics database and query interface |
| Health Check | `http://localhost:18081/health` | - | Service health check endpoint |
| Ray Metrics | - | `http://localhost:18080/metrics` | Prometheus metrics scraping endpoint |

**Note**: Access via Nginx (recommended) provides unified access and proper routing. Direct access bypasses the proxy.

## Service Access Overview

All services can be accessed either directly via their exposed ports, or through the Nginx reverse proxy. The Nginx proxy provides unified access and proper routing for all services.

---

## Access via Nginx Reverse Proxy

The Nginx reverse proxy runs on **port 18081** and provides unified access to all services.

### Base URL
- **Nginx Proxy**: `http://localhost:18081`

### Available Endpoints

#### 1. Health Check
- **URL**: `http://localhost:18081/health`
- **Description**: Service health check endpoint
- **Status**: Returns `200 OK` when healthy
- **Access**: Public

#### 2. Ray Dashboard (Root)
- **URL**: `http://localhost:18081/`
- **Description**: Ray Serve Dashboard - Main monitoring interface for Ray cluster
- **Features**: 
  - Cluster status and metrics
  - Job monitoring
  - Actor status
  - Serve deployments
- **Status**: Returns Ray Dashboard HTML interface
- **Access**: Public

#### 3. Ray Dashboard (Alternative Path)
- **URL**: `http://localhost:18081/dashboard`
- **Description**: Alternative path to Ray Dashboard (redirects to root)
- **Status**: Same as root path
- **Access**: Public

#### 4. Ray Serve API (OpenAI-Compatible)
- **URL**: `http://localhost:18081/v1`
- **Description**: OpenAI-compatible API endpoint for LLM inference
- **Endpoints**:
  - `GET /v1/models` - List available models
  - `POST /v1/chat/completions` - Chat completions
  - `POST /v1/completions` - Text completions
  - `POST /v1/embeddings` - Generate embeddings
- **Status**: Available when Ray Serve is fully initialized
- **Access**: Public (API access)

#### 5. Grafana Dashboard
- **URL**: `http://localhost:18081/grafana`
- **Description**: Metrics visualization dashboard (via Nginx proxy)
- **Default Credentials**: 
  - Username: `admin`
  - Password: `admin` (or as configured in `GRAFANA_ADMIN_PASSWORD`)
- **Features**: 
  - Pre-configured dashboards for Ray metrics
  - Prometheus data source integration
  - Custom metric visualization
- **Status**: Redirects to Grafana login
- **Access**: Authenticated

#### 6. Prometheus
- **URL**: `http://localhost:18081/prometheus`
- **Description**: Prometheus metrics database and query interface (via Nginx proxy)
- **Features**:
  - Metrics browser
  - Query interface (PromQL)
  - Targets status
  - Alerts configuration
- **Status**: Redirects to Prometheus UI
- **Access**: Public

---

## Direct Service Access

Services can also be accessed directly via their exposed ports, bypassing the Nginx proxy.

### Ray Serve Services

#### 1. Ray Dashboard (Direct)
- **URL**: `http://localhost:18265`
- **Port**: 18265 (mapped from container port 8265)
- **Description**: Direct access to Ray Dashboard
- **Status**: Returns Ray Dashboard interface
- **Access**: Public

#### 2. Ray Serve API (Direct)
- **URL**: `http://localhost:18000`
- **Port**: 18000 (mapped from container port 8000)
- **Description**: Direct access to Ray Serve API
- **Endpoints**: Same as `/v1` via Nginx
- **Status**: Available when Ray Serve is fully initialized
- **Access**: Public (API access)

#### 3. Ray Metrics (Prometheus Scraping)
- **URL**: `http://localhost:18080/metrics`
- **Port**: 18080 (mapped from container port 8080)
- **Description**: Prometheus metrics endpoint for scraping
- **Content-Type**: `text/plain` (Prometheus format)
- **Status**: Always available
- **Access**: Public (metrics scraping)

### Monitoring Services

#### 4. Grafana (Direct)
- **URL**: `http://localhost:13000`
- **Port**: 13000 (mapped from container port 3000)
- **Description**: Direct access to Grafana dashboard
- **Default Credentials**:
  - Username: `admin`
  - Password: `admin` (or as configured in `GRAFANA_ADMIN_PASSWORD`)
- **Features**: Full Grafana interface with Ray metrics dashboards
- **Status**: Available
- **Access**: Authenticated

#### 5. Prometheus (Direct)
- **URL**: `http://localhost:19090`
- **Port**: 19090 (mapped from container port 9090)
- **Description**: Direct access to Prometheus web UI
- **Features**:
  - Graph interface
  - Query interface
  - Targets and alerts management
- **Status**: Available
- **Access**: Public

---

## Port Configuration Summary

| Service | Container Port | Host Port | Environment Variable | Access Method |
|---------|---------------|-----------|---------------------|---------------|
| Nginx HTTP | 80 | 18081 | `NGINX_HTTP_PORT` | `http://localhost:18081` |
| Nginx HTTPS | 443 | 18443 | `NGINX_HTTPS_PORT` | `https://localhost:18443` |
| Ray Dashboard | 8265 | 18265 | `RAY_DASHBOARD_PORT` | `http://localhost:18265` |
| Ray Serve API | 8000 | 18000 | `RAY_API_PORT` | `http://localhost:18000` |
| Ray Metrics | 8080 | 18080 | `RAY_METRICS_PORT` | `http://localhost:18080/metrics` |
| Grafana | 3000 | 13000 | `GRAFANA_PORT` | `http://localhost:13000` |
| Prometheus | 9090 | 19090 | `PROMETHEUS_PORT` | `http://localhost:19090` |

---

## Quick Access Reference

### Primary Endpoints (Recommended)

```
Ray Dashboard:     http://localhost:18081/          (via Nginx)
Ray API:           http://localhost:18081/v1        (via Nginx)
Grafana:           http://localhost:18081/grafana    (via Nginx)
Prometheus:        http://localhost:18081/prometheus (via Nginx)
Health Check:      http://localhost:18081/health     (via Nginx)
```

### Direct Access (Alternative)

```
Ray Dashboard:     http://localhost:18265
Ray API:           http://localhost:18000
Grafana:           http://localhost:13000
Prometheus:        http://localhost:19090
Ray Metrics:       http://localhost:18080/metrics
```

---

## Cloudflare Tunnel Access

If you've configured a Cloudflare tunnel, you can access the services via your tunnel domain:

### Recommended Configuration

Point your Cloudflare tunnel to the Nginx proxy port (`18081`):

```yaml
ingress:
  - hostname: your-domain.example.com
    service: http://localhost:18081
```

### Access URLs via Tunnel

```
Ray Dashboard:     https://your-domain.example.com/
Ray API:           https://your-domain.example.com/v1
Grafana:           https://your-domain.example.com/grafana
Prometheus:        https://your-domain.example.com/prometheus
Health Check:      https://your-domain.example.com/health
```

---

## Service Status Verification

### Check All Services

```bash
cd docker
docker compose ps
```

### Test Endpoints

```bash
# Health check
curl http://localhost:18081/health

# Ray Dashboard
curl http://localhost:18081/

# Ray API (when ready)
curl http://localhost:18081/v1/models

# Grafana
curl -I http://localhost:18081/grafana

# Prometheus
curl -I http://localhost:18081/prometheus
```

---

## Authentication & Security

### Public Access (No Authentication Required)
- Ray Dashboard
- Ray API endpoints
- Prometheus UI
- Health check endpoint
- Metrics endpoints

### Authenticated Access (Login Required)
- **Grafana**: Username/Password authentication
  - Default: `admin` / `admin`
  - Configured via `GRAFANA_ADMIN_PASSWORD` in `.env` or `.secrets`

---

## Troubleshooting

### Service Not Accessible

1. **Check if service is running**:
   ```bash
   docker compose ps
   ```

2. **Check service logs**:
   ```bash
   docker compose logs <service-name>
   ```

3. **Verify port mapping**:
   ```bash
   docker compose config | grep ports
   ```

4. **Check port availability**:
   ```bash
   netstat -tlnp | grep <port>
   # or
   ss -tlnp | grep <port>
   ```

### Common Issues

- **Port conflicts**: Check `.env` file for port configurations
- **Service not ready**: Wait for Ray Serve to fully initialize (can take several minutes)
- **502 Bad Gateway**: Service behind proxy is not ready or unreachable
- **Connection refused**: Service is not running or port is not exposed

---

## Notes

- All ports are configurable via the `.env` file in the project root
- The Nginx proxy provides the recommended access method for production use
- Direct access is useful for debugging or when the proxy is not needed
- Ray Serve API may take time to initialize after container startup (model loading)
- Metrics endpoint (port 18080) is primarily for Prometheus scraping, not browser access

---

## See Also

- [Cloudflare Tunnel Setup](./cloudflare-tunnel-setup.md) - Configure Cloudflare tunnel access
- [README.md](../README.md) - General project documentation
- [Configuration Guide](../README.md#configuration) - Environment variable configuration

