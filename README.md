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
│   Nginx Proxy   │ (Port 80/443)
│   (docker/nginx)│
└──────┬──────────┘
       │
       │ Internal Network
       │
┌──────▼──────────┐
│  Ray Serve      │ (Port 8000)
│  + vLLM Engine  │
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
   cd GPU-CLUSTER
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
   - Adjust port mappings if needed

4. **Build and start the services:**
   ```bash
   cd docker
   docker-compose up --build
   ```

5. **Access the services:**
   - **API Endpoint**: `http://localhost/v1` (via Nginx)
   - **Ray Dashboard**: `http://localhost/dashboard` (via Nginx)
   - **Direct Ray API**: `http://localhost:8000/v1`
   - **Direct Dashboard**: `http://localhost:8265`

## Configuration

### Environment Variables (`.env`)

All configuration is done via environment variables in `.env`:

**Model Configuration:**
- `MODEL_ID`: HuggingFace model identifier
- `TENSOR_PARALLEL_SIZE`: Number of GPUs for tensor parallelism
- `ACCELERATOR_TYPE`: GPU type (L4, H100, A100, etc.)

**Scaling Configuration:**
- `MIN_REPLICAS`: Minimum autoscaling replicas (default: 1)
- `MAX_REPLICAS`: Maximum autoscaling replicas (default: 4)
- `TARGET_ONGOING_REQUESTS`: Target concurrent requests per replica (default: 32)

**Port Configuration:**
- `RAY_API_PORT`: Ray Serve API port (default: 8000)
- `RAY_DASHBOARD_PORT`: Ray Dashboard port (default: 8265)
- `NGINX_HTTP_PORT`: Nginx HTTP port (default: 80)
- `NGINX_HTTPS_PORT`: Nginx HTTPS port (default: 443)

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
    base_url="http://localhost/v1",
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
curl http://localhost/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-32B-Instruct",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Directory Structure

```
GPU-CLUSTER/
├── docker/
│   ├── Dockerfile              # Ray Serve container definition
│   ├── docker-compose.yml      # Multi-container orchestration
│   └── nginx/
│       └── nginx.conf           # Reverse proxy configuration
├── src/
│   └── deploy.py               # Ray Serve deployment script
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

### Container Health Checks
- Check Ray Serve: `docker logs ray-serve`
- Check Nginx: `docker logs nginx-proxy`
- View Ray Dashboard for detailed metrics

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

