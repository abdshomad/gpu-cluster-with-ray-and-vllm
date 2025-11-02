# Docker Container for GPU Cluster Platform (vLLM + Ray Serve)

## Overview
Build a Docker container that packages vLLM with Ray Serve following the production-grade deployment pattern from the guide. The container will use `uv` for Python package management, include Nginx as a reverse proxy, and use `.env` and `.secrets` files for configuration management.

## Implementation Status

✅ **COMPLETED** - This plan has been fully implemented. The following features are now in place:

### Core Infrastructure (Part 1 from guide)
- ✅ Dockerfile with NVIDIA CUDA 12.4.0 runtime, Ubuntu 22.04
- ✅ Python 3.11 environment managed with `uv`
- ✅ Deployment script (`src/deploy.py`) implementing LLMConfig pattern
- ✅ Docker Compose multi-container orchestration
- ✅ Nginx reverse proxy with comprehensive routing
- ✅ Environment variable configuration (`.env` and `.secrets`)
- ✅ Health check endpoints
- ✅ GPU support via NVIDIA Container Toolkit

### Observability Stack (Part 2 from guide)
- ✅ Prometheus metrics collection with file-based service discovery
- ✅ Grafana provisioning (datasource + pre-built dashboards)
- ✅ CheckMK integration configuration files
- ✅ Ray metrics export on port 8080 (configurable)
- ✅ Ray Dashboard accessible via Nginx proxy

### Additional Features
- ✅ Web application (`docker/webapp/index.html`) providing service links
- ✅ Model cache volume mounting support
- ✅ Comprehensive port configuration via environment variables
- ✅ All services accessible through unified Nginx entry point

### Currently Out of Scope (Planned for Next Phase)
- ❌ PII masking with Presidio (Part 3 from guide)
- ❌ Bookend pattern for deanonymization
- ❌ SSL/TLS termination
- ❌ Pipeline parallelism configuration
- ❌ Multi-node Ray cluster support

## Key Components

### 1. Dockerfile Structure
- **Base Image**: NVIDIA CUDA runtime image (12.x) with Ubuntu 22.04
- **Python Environment**: Install `uv` and use it to manage Python packages
- **Dependencies**: Install `ray[serve,llm]>=2.45.0` and `vllm` using `uv pip install`
- **GPU Support**: Configure NVIDIA Container Toolkit compatibility

### 2. Directory Structure
```
GPU-CLUSTER/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx/
│       └── nginx.conf
├── src/
│   └── deploy.py (main deployment script using LLMConfig)
├── requirements.txt (dependencies for uv)
├── .env (configuration settings)
├── .secrets (secrets - gitignored)
├── .dockerignore
└── plan.md
```

### 3. Implementation Details

#### 3.1 Dockerfile (`docker/Dockerfile`)
- Use `nvidia/cuda:12.4.0-runtime-ubuntu22.04` as base
- Install system dependencies (build tools, CUDA libraries)
- Install `uv` from official source
- Create virtual environment using `uv venv`
- Install Python packages via `uv pip install`
- Copy deployment scripts
- Expose Ray Serve port (configurable via env, default 8000) and Ray dashboard port (configurable via env, default 8265)
- Set entrypoint to run deployment script using `uv run python`

#### 3.2 Deployment Script (`src/deploy.py`)
- Implement the LLMConfig pattern from the guide (Section 1.3)
- Read environment variables from `.env` and `.secrets` files (loaded by docker-compose)
- Make model configuration configurable via environment variables:
  - `MODEL_ID` (default: from guide example)
  - `TENSOR_PARALLEL_SIZE` (default: 4)
  - `ACCELERATOR_TYPE` (default: configurable)
  - `MIN_REPLICAS`, `MAX_REPLICAS` for autoscaling
- Use `build_openai_app` to create FastAPI application
- Deploy with `serve.run()` on configurable port from environment

#### 3.3 Dependencies (`requirements.txt`)
- Generate using `uv pip freeze` approach
- Core packages:
  - `ray[serve,llm]>=2.45.0`
  - `vllm`
  - `openai` (for client testing)
  - `python-dotenv` (for loading .env files if needed)

#### 3.4 Docker Compose (`docker/docker-compose.yml`)
- **Multi-container setup**:
  - Ray Serve container (vLLM deployment)
  - Nginx reverse proxy container (routes traffic, SSL termination)
- Configure GPU access via `runtime: nvidia` for Ray container
- **Configurable ports** via `.env` file:
  - Ray API port (default: 8000)
  - Ray dashboard port (default: 8265)
  - Nginx HTTP port (default: 80)
  - Nginx HTTPS port (default: 443)
- Load environment variables from `.env` and `.secrets` files via `env_file` directive
- Mount volumes for model cache (optional)
- Nginx container routes `/v1` to Ray Serve backend
- Internal network for container communication

#### 3.5 Nginx Configuration (`docker/nginx/nginx.conf`)
- Reverse proxy configuration pointing to Ray Serve container
- Use environment variable or docker-compose service name for upstream server
- Set up routing for `/v1` API endpoint and Ray dashboard
- Configure health check endpoints
- Support for SSL/TLS termination (optional, for future)
- Configurable worker processes and client max body size

#### 3.6 Environment Files
- **`.env`**: Configuration settings (model ID, ports, scaling, etc.)
  - All non-sensitive configuration
  - Port mappings
  - Model deployment settings
  - Nginx configuration
- **`.secrets`**: Sensitive data (API keys, tokens, etc.)
  - HuggingFace tokens
  - API keys
  - Other credentials
  - Must be gitignored

## Implementation Steps

1. **Create directory structure**
   - Create `docker/` directory for Docker-related files
   - Create `docker/nginx/` for Nginx configuration
   - Create `src/` directory for deployment scripts

2. **Generate requirements.txt**
   - Use `uv pip freeze` approach, but manually specify core dependencies first

3. **Write Dockerfile**
   - Multi-stage build (optional): base image with dependencies, final image with code
   - Install `uv` and create virtual environment
   - Install packages via `uv pip install -r requirements.txt`
   - Copy deployment scripts and set working directory
   - Configure entrypoint to use `uv run python`

4. **Implement deployment script (`src/deploy.py`)**
   - Import Ray Serve and LLMConfig modules
   - Read configuration from environment variables (loaded from `.env` and `.secrets` by docker-compose)
   - Build LLMConfig with configurable parameters
   - Use `build_openai_app` to create FastAPI app
   - Deploy with `serve.run()` on configurable port (from env)

5. **Create Nginx configuration (`docker/nginx/nginx.conf`)**
   - Configure reverse proxy to Ray Serve backend
   - Use docker-compose service name for upstream server address
   - Set up routing for `/v1` API endpoint
   - Configure health checks
   - Make settings configurable via environment variables

6. **Create Docker Compose (`docker/docker-compose.yml`)**
   - Define Ray Serve service with GPU support
   - Define Nginx service (no GPU required)
   - Load `.env` and `.secrets` files via `env_file` directive
   - Configure port mappings (all configurable via `.env`)
   - Set up internal network between containers
   - Configure volume mounts for model cache (optional)
   - Set up dependency: Nginx depends on Ray Serve being ready

7. **Create environment files**
   - **`.env`**: Non-sensitive configuration (ports, model settings, scaling)
     - Include example values with comments
     - Document all available variables
   - **`.secrets`**: Sensitive data (API keys, tokens)
     - Include template with placeholder values
     - Add `.secrets` to `.gitignore`

8. **Create .dockerignore**
   - Exclude unnecessary files (.git, __pycache__, etc.)
   - Exclude `.secrets` file (security)
   - Exclude virtual environments

## Configuration Points

### Environment Variables (`.env` file)
**Ray Serve / vLLM Settings:**
- `MODEL_ID`: HuggingFace model identifier (e.g., `Qwen/Qwen2.5-32B-Instruct`)
- `TENSOR_PARALLEL_SIZE`: Number of GPUs for tensor parallelism (default: 4)
- `ACCELERATOR_TYPE`: GPU type (e.g., `L4`, `H100`, `A100`)
- `MIN_REPLICAS`: Minimum autoscaling replicas (default: 1)
- `MAX_REPLICAS`: Maximum autoscaling replicas (default: 4)
- `TARGET_ONGOING_REQUESTS`: Target concurrent requests per replica (default: 32)
- `RAY_HEAD_HOST`: Ray head node address (for multi-node setups)

**Port Configuration:**
- `RAY_API_PORT`: Ray Serve API port (default: 8000)
- `RAY_DASHBOARD_PORT`: Ray Dashboard port (default: 8265)
- `NGINX_HTTP_PORT`: Nginx HTTP port (default: 80)
- `NGINX_HTTPS_PORT`: Nginx HTTPS port (default: 443)

**Nginx Settings:**
- `NGINX_WORKER_PROCESSES`: Number of worker processes (default: auto)
- `NGINX_CLIENT_MAX_BODY_SIZE`: Max request body size (default: 100m)

### Secrets (`.secrets` file - gitignored)
- `HUGGINGFACE_TOKEN`: HuggingFace API token (for private models)
- `OPENAI_API_KEY`: API key for OpenAI-compatible endpoint (optional)
- Any other sensitive credentials

## Testing Considerations

- Container should be buildable and runnable with GPU access
- Verify Ray Serve dashboard is accessible through Nginx proxy
- Test OpenAI-compatible API endpoint through Nginx
- Validate model loading and inference
- Test port configuration via `.env` file
- Verify secrets are loaded correctly from `.secrets` file

## Notes

- ✅ All implementation follows AGENTS.md instructions: Python execution via `uv run`
- ✅ Base deployment implements Section 1.3 pattern (LLMConfig + build_openai_app)
- ✅ Observability (Part 2) is **IMPLEMENTED** - Prometheus, Grafana, CheckMK all configured
- ⚠️ PII masking (Part 3) remains **NOT IMPLEMENTED** - planned for next phase (see next-plan.md)
- ⚠️ Container assumes single-node deployment; multi-node requires additional configuration
- ✅ **Security**: `.secrets` file is gitignored and never committed
- ⚠️ **Nginx**: SSL/TLS termination not yet implemented (planned for future)
- ✅ All ports configurable via `.env` for flexibility in different deployment environments
- ✅ Nginx provides unified entry point for all services

## Files Implemented

- `docker/Dockerfile` - Complete Docker image with uv and Python dependencies
- `docker/docker-compose.yml` - Multi-service orchestration (Ray, Prometheus, Grafana, CheckMK, Nginx)
- `docker/nginx/nginx.conf` - Comprehensive reverse proxy configuration
- `docker/prometheus/prometheus.yml` - Metrics scraping with file-based service discovery
- `docker/grafana/provisioning/` - Automated datasource and dashboard provisioning
- `docker/checkmk/configuration/` - CheckMK Prometheus integration config
- `docker/webapp/index.html` - Service links web application
- `src/deploy.py` - Full LLMConfig-based deployment implementation
- `requirements.txt` - Python dependencies managed with uv

