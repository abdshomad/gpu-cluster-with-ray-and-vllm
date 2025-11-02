# GPU Cluster Platform - vLLM + Ray Serve Docker Deployment

Production-grade Docker container setup for deploying Large Language Models using vLLM inference engine with Ray Serve orchestration.

## Overview

This project provides a complete Docker-based deployment solution for serving LLMs with:
- **vLLM**: High-performance inference engine with PagedAttention
- **Ray Serve**: Production-grade serving framework with autoscaling
- **Nginx**: Reverse proxy for unified API access
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
┌──────▼──────────┐
│  Ray Serve      │ (API: 8000, Dashboard: 8265)
│  + vLLM Engine  │
│  + Ray Dashboard│
│  (GPU-enabled)  │
└─────────────────┘
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

See `.env.example` for all available options.

### Secrets (`.secrets`)

Sensitive credentials go in `.secrets` (gitignored):
- `HUGGINGFACE_TOKEN`: Required for private models on HuggingFace

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
│   └── nginx/
│       └── nginx.conf           # Reverse proxy configuration
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
- View Ray Dashboard for detailed metrics and cluster status

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
