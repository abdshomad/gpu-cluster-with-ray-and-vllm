# GPU Cluster Platform - vLLM + Ray Serve Docker Deployment

Production-grade Docker container setup for deploying Large Language Models using vLLM inference engine with Ray Serve orchestration.

## Overview

This project provides a complete Docker-based deployment solution for serving LLMs with:
- **vLLM**: High-performance inference engine with PagedAttention
- **Ray Serve**: Production-grade serving framework with autoscaling
- **Nginx**: Reverse proxy for unified API access
- **Prometheus**: Metrics collection and storage
- **Grafana**: Metrics visualization and dashboards
- **CheckMK**: Enterprise monitoring with Prometheus integration
- **Environment-based configuration**: All settings via `.env` and `.secrets` files

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ HTTP/HTTPS
       │
┌──────▼──────────┐
│   Nginx Proxy   │ (Host: 80/443, Internal: 80)
│   (docker/nginx)│
└──────┬──────────┘
       │
       │ Internal Network
       │
┌──────▼──────────┐      ┌─────────────┐      ┌─────────────┐
│  Ray Serve      │─────▶│ Prometheus   │─────▶│  CheckMK     │
│  + vLLM Engine  │      │  (Metrics)   │      │  (Monitoring)│
│  + Ray Dashboard│      └─────────────┘      └─────────────┘
│  (GPU-enabled)  │            │                      │
└─────────────────┘            │                      │
                               ▼                      │
                        ┌─────────────┐              │
                        │   Grafana   │──────────────┘
                        │ (Dashboards)│
                        └─────────────┘
```

## Prerequisites

- Docker and Docker Compose installed
- NVIDIA Docker runtime (`nvidia-docker2`) installed
- GPU with CUDA support
- At least 4 GPUs recommended for default configuration

## Quick Start

1. **Clone and navigate to the project directory:**
   ```bash
   git clone https://github.com/abdshomad/gpu-cluster-with-ray-and-vllm.git
   cd gpu-cluster-with-ray-and-vllm
   ```

2. **Set up environment files:**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Create secrets file (required for private models)
   cp .secrets .secrets
   # Edit .secrets and add your HuggingFace token if needed
   ```

3. **Edit `.env` file:**
   - Set your `MODEL_ID` (e.g., `Qwen/Qwen2.5-32B-Instruct`)
   - Configure `TENSOR_PARALLEL_SIZE` to match your GPU count
   - Set `ACCELERATOR_TYPE` to match your GPU (L4, H100, A100, etc.)
     - **Note:** Common variations are automatically mapped (e.g., `L40` → `L4`)
   - Adjust port mappings if needed (defaults use 18000/18265/18080 to avoid conflicts)

4. **Build and start the services:**
   ```bash
   cd docker
   docker compose up --build -d
   ```
   
   > **Note:** The `-d` flag runs containers in detached mode. Remove it to see logs in foreground.
   
   To view logs:
   ```bash
   docker compose logs -f
   ```

5. **Access the services:**
   
   **API Endpoints:**
   - `http://localhost:{NGINX_HTTP_PORT}/v1` (via Nginx, default: `http://localhost:18080/v1`)
   - `http://localhost:{RAY_API_PORT}/v1` (direct Ray Serve, default: `http://localhost:18000/v1`)
   
   **Ray Dashboard:**
   - `http://localhost:{NGINX_HTTP_PORT}/dashboard` (via Nginx, default: `http://localhost:18080/dashboard`)
   - `http://localhost:{RAY_DASHBOARD_PORT}` (direct access, default: `http://localhost:18265`)
   
   **Monitoring & Observability:**
   - **Prometheus:** `http://localhost:{PROMETHEUS_PORT}` (default: `http://localhost:19090`)
     - Via Nginx: `http://localhost:{NGINX_HTTP_PORT}/prometheus`
   - **Grafana:** `http://localhost:{GRAFANA_PORT}` (default: `http://localhost:13000`)
     - Via Nginx: `http://localhost:{NGINX_HTTP_PORT}/grafana`
     - Default credentials: `admin` / `admin` (configurable in `.env`)
   - **CheckMK:** `http://localhost:{CHECKMK_PORT}/monitoring/check_mk/` (default: `http://localhost:15000/monitoring/check_mk/`)
     - Via Nginx: `http://localhost:{NGINX_HTTP_PORT}/checkmk/monitoring/check_mk/`
     - Default credentials: `cmkadmin` / `admin` (configurable in `.env`)
   
   > **Note:** Port numbers depend on your `.env` configuration. Defaults shown assume custom port mappings to avoid conflicts.

## Configuration

### Environment Variables (`.env`)

All configuration is done via environment variables in `.env`:

**Model Configuration:**
- `MODEL_ID`: HuggingFace model identifier
- `TENSOR_PARALLEL_SIZE`: Number of GPUs for tensor parallelism
- `ACCELERATOR_TYPE`: GPU type (L4, H100, A100, etc.)
  - Supported types: L4, A100, H100, T4, V100, A10, A10G
  - Common variations are auto-mapped (e.g., `L40` → `L4`)

**Scaling Configuration:**
- `MIN_REPLICAS`: Minimum autoscaling replicas (default: 1)
- `MAX_REPLICAS`: Maximum autoscaling replicas (default: 4)
- `TARGET_ONGOING_REQUESTS`: Target concurrent requests per replica (default: 32)

**Port Configuration:**
- `RAY_API_PORT`: Host port for Ray Serve API (default: 8000, recommended: 18000 to avoid conflicts)
- `RAY_DASHBOARD_PORT`: Host port for Ray Dashboard (default: 8265, recommended: 18265 to avoid conflicts)
  - **Note:** The dashboard runs on port 8265 inside the container; this setting maps it to the host
- `NGINX_HTTP_PORT`: Nginx HTTP port on host (default: 80, recommended: 18080 to avoid conflicts)
- `NGINX_HTTPS_PORT`: Nginx HTTPS port on host (default: 443)
- `PROMETHEUS_PORT`: Prometheus web UI port on host (default: 19090)
- `GRAFANA_PORT`: Grafana web UI port on host (default: 13000)
- `CHECKMK_PORT`: CheckMK web UI port on host (default: 15000)
- `CHECKMK_AGENT_PORT`: CheckMK agent receiver port on host (default: 6556)

See `.env.example` for all available options.

### Secrets (`.secrets`)

Sensitive credentials go in `.secrets` (gitignored):
- `HUGGINGFACE_TOKEN`: Required for private models on HuggingFace
- `GRAFANA_PASSWORD`: Grafana admin password (default: `admin`)
- `CHECKMK_PASSWORD`: CheckMK admin password (default: `admin`)

## Usage

### Testing the API

Once the services are running, test with an OpenAI-compatible client:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:{NGINX_HTTP_PORT}/v1",  # Replace with your port, e.g., 18080
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-32B-Instruct",  # Your MODEL_ID
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Using cURL

```bash
# Via Nginx (replace {NGINX_HTTP_PORT} with your configured port, e.g., 18080)
curl http://localhost:{NGINX_HTTP_PORT}/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-32B-Instruct",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Direct to Ray Serve (replace {RAY_API_PORT} with your configured port, e.g., 18000)
curl http://localhost:{RAY_API_PORT}/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-32B-Instruct",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Directory Structure

```
gpu-cluster-with-ray-and-vllm/
├── docker/
│   ├── Dockerfile              # Ray Serve container definition
│   ├── docker-compose.yml      # Multi-container orchestration
│   ├── nginx/
│   │   └── nginx.conf           # Reverse proxy configuration
│   ├── prometheus/
│   │   └── prometheus.yml       # Prometheus scraping configuration
│   ├── grafana/
│   │   └── provisioning/        # Grafana dashboards and datasources
│   └── checkmk/
│       ├── configuration/       # CheckMK Prometheus agent config
│       └── prometheus_services/ # vLLM service definitions
├── src/
│   └── deploy.py               # Ray Serve deployment script
├── docs/
│   ├── plan.md                  # Implementation plan
│   └── vllm-ray-serve-guide.md  # Comprehensive deployment guide
├── requirements.txt            # Python dependencies
├── .env.example                # Configuration template
├── .secrets                    # Secrets (gitignored)
└── README.md                   # This file
```

## Building

To build the Docker image manually:

```bash
docker build -f docker/Dockerfile -t gpu-cluster-ray-serve .
```

## Troubleshooting

### GPU Not Detected
- Ensure `nvidia-docker2` is installed
- Check GPU availability: `nvidia-smi`
- Verify Docker runtime: `docker info | grep -i runtime`

### Port Conflicts
- Edit `.env` to change port mappings
- Ensure ports are not in use: `lsof -i :8000`

### Model Loading Issues
- Check GPU memory: Ensure sufficient VRAM for model
- Verify `TENSOR_PARALLEL_SIZE` doesn't exceed available GPUs
- For private models, ensure `HUGGINGFACE_TOKEN` is set in `.secrets`

### Dashboard Access Issues

If you cannot access the dashboard:

1. **Verify containers are running:**
   ```bash
   docker compose -f docker/docker-compose.yml ps
   ```

2. **Check Ray Dashboard is bound correctly:**
   ```bash
   docker logs ray-serve | grep -i "dashboard"
   ```
   Should show: `Started a local Ray instance. View the dashboard at...`

3. **Test direct access:**
   ```bash
   curl http://localhost:{RAY_DASHBOARD_PORT}
   # or
   curl http://localhost:18265  # if using default mapping
   ```

4. **Test via Nginx:**
   ```bash
   curl http://localhost:{NGINX_HTTP_PORT}/dashboard
   # or
   curl http://localhost:18080/dashboard  # if using default mapping
   ```

5. **Check nginx logs for proxy errors:**
   ```bash
   docker logs gpu-cluster-nginx-proxy
   ```

### Container Health Checks
- Check Ray Serve: `docker logs ray-serve`
- Check Nginx: `docker logs gpu-cluster-nginx-proxy`
- Check Prometheus: `docker logs gpu-cluster-prometheus`
- Check Grafana: `docker logs gpu-cluster-grafana`
- Check CheckMK: `docker logs gpu-cluster-checkmk`
- View Ray Dashboard for detailed metrics and cluster status

## Monitoring & Observability

This deployment includes a comprehensive monitoring stack:

### Prometheus
- Collects metrics from Ray Serve and vLLM
- Exposes metrics at `/metrics` endpoint
- Accessible at `http://localhost:{PROMETHEUS_PORT}` or via Nginx at `/prometheus`

### Grafana
- Pre-configured dashboards for Ray and vLLM metrics
- Automatically provisioned on startup
- Accessible at `http://localhost:{GRAFANA_PORT}` or via Nginx at `/grafana`

### CheckMK
- Enterprise-grade monitoring with Prometheus integration
- Monitors critical vLLM metrics (TTFT, TPOT, KV Cache Utilization)
- Uses Prometheus special agent to query metrics
- Pre-configured service definitions for vLLM Golden Signals
- Accessible at `http://localhost:{CHECKMK_PORT}/monitoring/check_mk/` or via Nginx at `/checkmk`

**CheckMK Setup:**
After starting the services, configure CheckMK via the web UI:
1. Create a new host representing the Prometheus data source
2. Configure the Prometheus special agent pointing to `http://prometheus:9090`
3. Enable service creation using PromQL queries
4. Import services from the pre-configured definitions

For detailed setup instructions, see `docker/checkmk/README.md`.

**Critical Metrics Monitored:**
- **vLLM Time to First Token (TTFT)** - Alert on p95 > 2s
- **vLLM Time Per Output Token (TPOT)** - Generation speed
- **vLLM KV Cache Utilization** - Primary bottleneck, alert on > 80%
- **vLLM Request States** - Running and waiting requests
- **Ray Serve Processing Latency** - Alert on p95 > 5s
- **Ray Serve Throughput** - Requests per second (RPS)
- **Ray Serve Replica Management** - Autoscaler activity

See `docs/vllm-ray-serve-guide.md` Table 2.1 for complete metrics reference.

## Development

Following `AGENTS.md` guidelines:
- Use `uv` for Python package management
- All Python execution via `uv run python`

## References

- [vLLM Ray Serve Guide](./docs/vllm-ray-serve-guide.md): Comprehensive deployment guide
- [Ray Serve Documentation](https://docs.ray.io/en/latest/serve/index.html)
- [vLLM Documentation](https://docs.vllm.ai/)

## License

See project license file.
