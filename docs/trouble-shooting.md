# Troubleshooting Guide - GPU Cluster Platform (vLLM + Ray Serve)

This document contains all errors encountered during deployment and their solutions.

## Table of Contents

1. [Missing Environment Files](#1-missing-environment-files)
2. [Docker Compose Command Not Found](#2-docker-compose-command-not-found)
3. [Port Conflicts](#3-port-conflicts)
4. [Container Name Conflicts](#4-container-name-conflicts)
5. [UV Installation PATH Issue](#5-uv-installation-path-issue)
6. [Python Packages Not Installing to Virtual Environment](#6-python-packages-not-installing-to-virtual-environment)
7. [UV System Python Flag](#7-uv-system-python-flag)
8. [Python Version Mismatch in Virtual Environment](#8-python-version-mismatch-in-virtual-environment)
9. [LLMConfig Parameter Error: num_replicas](#9-llmconfig-parameter-error-num_replicas)
10. [num_replicas Conflict with Autoscaling](#10-num_replicas-conflict-with-autoscaling)
11. [Accelerator Type Not Recognized](#11-accelerator-type-not-recognized)
12. [Docker Compose Version Attribute Warning](#12-docker-compose-version-attribute-warning)
13. [Ray GPU Resource Allocation Errors](#13-ray-gpu-resource-allocation-errors)
14. [Grafana Dashboard "rayServeDashboard" Not Found Error](#14-grafana-dashboard-rayservedashboard-not-found-error)

---

## 1. Missing Environment Files

### Error Description

```
Error: .env and .secrets files not found
```

When attempting to start Docker Compose services, the required configuration files were missing.

### Cause

The `.env` and `.secrets` files are not tracked in git and need to be created from `.env.example`.

### Solution

```bash
# Create .env file from example
cp .env.example .env

# Create .secrets file (empty, user should add tokens)
echo "# Secrets file for GPU Cluster Platform" > .secrets
echo "HUGGINGFACE_TOKEN=" >> .secrets
```

### Preventive Measures

- Document in README that users must create `.env` and `.secrets` files
- Consider adding a setup script that creates these files automatically

---

## 2. Docker Compose Command Not Found

### Error Description

```
Command 'docker-compose' not found
```

### Cause

Modern Docker installations use `docker compose` (without hyphen) instead of the legacy `docker-compose` command.

### Solution

Use `docker compose` instead of `docker-compose`:

```bash
# Old (legacy)
docker-compose up --build

# New (correct)
docker compose up --build
```

### Preventive Measures

- Always use `docker compose` (v2 syntax) in documentation
- Note that Docker Compose v2 is now the standard

---

## 3. Port Conflicts

### Error Description

```
Error response from daemon: failed to bind host port for 0.0.0.0:8000:172.20.0.2:8000/tcp: address already in use
Conflict. The container name "/nginx-proxy" is already in use
```

### Cause

Default ports (80, 8000, 8265) were already in use by other services running on the host.

### Solution

1. **Update `.env` file with alternative ports:**
   ```bash
   sed -i 's/RAY_API_PORT=8000/RAY_API_PORT=18000/' .env
   sed -i 's/RAY_DASHBOARD_PORT=8265/RAY_DASHBOARD_PORT=18265/' .env
   sed -i 's/NGINX_HTTP_PORT=80/NGINX_HTTP_PORT=18080/' .env
   sed -i 's/NGINX_HTTPS_PORT=443/NGINX_HTTPS_PORT=18443/' .env
   ```

2. **Export environment variables before running docker compose:**
   ```bash
   export $(cat .env | grep -v '^#' | xargs)
   docker compose up -d
   ```

### Preventive Measures

- Check port availability before starting: `lsof -i :PORT`
- Use non-standard ports for development
- Document port requirements clearly

---

## 4. Container Name Conflicts

### Error Description

```
Error response from daemon: Conflict. The container name "/nginx-proxy" is already in use
```

### Cause

Another container was already using the name `nginx-proxy`.

### Solution

Updated `docker-compose.yml` to use a unique container name:

```yaml
# Before
container_name: nginx-proxy

# After
container_name: gpu-cluster-nginx-proxy
```

### Preventive Measures

- Use project-specific container names to avoid conflicts
- Include project identifier in container names

---

## 5. UV Installation PATH Issue

### Error Description

```
/bin/sh: 1: uv: not found
```

During Docker build, the `uv` command was not found even though it was installed.

### Cause

The `uv` installer places the binary in `/root/.local/bin`, but the Dockerfile was looking for it in `/root/.cargo/bin`.

### Solution

Updated `docker/Dockerfile`:

```dockerfile
# Before
ENV PATH="/root/.cargo/bin:$PATH"

# After
ENV PATH="/root/.local/bin:$PATH"
```

### Preventive Measures

- Verify installation paths for tools in Dockerfiles
- Check where installers actually place binaries

---

## 6. Python Packages Not Installing to Virtual Environment

### Error Description

```
ModuleNotFoundError: No module named 'ray'
```

Even after building the Docker image, Python packages were not available at runtime.

### Cause

The `uv pip install --system` flag was installing packages to the system Python instead of the virtual environment.

### Solution

1. **Removed the `--system` flag from Dockerfile:**
   ```dockerfile
   # Before
   RUN uv pip install --system -r requirements.txt
   
   # After
   RUN uv pip install -r requirements.txt
   ```

2. **Removed `UV_SYSTEM_PYTHON=1` environment variable:**
   ```dockerfile
   # Removed this line:
   # ENV UV_SYSTEM_PYTHON=1
   ```

### Preventive Measures

- Never use `--system` flag with `uv pip install` when working with virtual environments
- Verify `VIRTUAL_ENV` is set and active before installing packages
- Check package installation with `uv pip list` after installation

---

## 7. UV System Python Flag

### Error Description

Packages were being installed to system Python (`/usr`) instead of the virtual environment (`/app/.venv`).

### Cause

The `UV_SYSTEM_PYTHON=1` environment variable was set, which forced `uv` to install packages to the system Python.

### Solution

Removed the environment variable from `docker/Dockerfile`:

```dockerfile
# Removed:
# ENV UV_SYSTEM_PYTHON=1
```

### Preventive Measures

- Only set `UV_SYSTEM_PYTHON=1` when intentionally installing system-wide packages
- Verify virtual environment is active: `which python` should point to venv

---

## 8. Python Version Mismatch in Virtual Environment

### Error Description

Virtual environment was created with Python 3.10 instead of Python 3.11, causing version mismatches.

### Cause

When running `uv venv` without specifying the Python version, it defaults to the system default Python (3.10), not the explicitly installed Python 3.11.

### Solution

Explicitly specify Python version when creating the virtual environment:

```dockerfile
# Before
RUN uv venv /app/.venv

# After
RUN uv venv /app/.venv --python 3.11
```

### Preventive Measures

- Always specify Python version explicitly: `uv venv --python 3.11`
- Verify venv Python version: `/app/.venv/bin/python --version`

---

## 9. LLMConfig Parameter Error: num_replicas

### Error Description

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for LLMConfig
num_replicas
  Extra inputs are not permitted [type=extra_forbidden, input_value=1, input_type=int]
```

### Cause

`num_replicas` was passed as a direct parameter to `LLMConfig`, but it's not a valid top-level parameter. It belongs inside `deployment_config`.

### Solution

Moved `num_replicas` into the `deployment_config` dictionary:

```python
# Before
llm_config = LLMConfig(
    deployment_config={
        'autoscaling_config': {...},
        'max_ongoing_requests': 64,
    },
    num_replicas=num_replicas,  # Wrong location
)

# After
llm_config = LLMConfig(
    deployment_config={
        'autoscaling_config': {...},
        'max_ongoing_requests': 64,
        'num_replicas': num_replicas,  # Correct location
    },
)
```

### Preventive Measures

- Check LLMConfig API documentation for correct parameter structure
- Use `inspect` module to check valid fields: `LLMConfig.model_fields.keys()`
- Validate configuration before deployment

---

## 10. num_replicas Conflict with Autoscaling

### Error Description

```
ValueError: Manually setting num_replicas is not allowed when autoscaling_config is provided.
```

### Cause

When `autoscaling_config` is provided, Ray Serve automatically manages replica count. Setting `num_replicas` manually conflicts with autoscaling.

### Solution

Removed `num_replicas` from `deployment_config` when using autoscaling:

```python
# Correct configuration with autoscaling
deployment_config={
    'autoscaling_config': {
        'min_replicas': min_replicas,
        'max_replicas': max_replicas,
        'target_ongoing_requests': target_ongoing_requests,
    },
    'max_ongoing_requests': max_ongoing_requests,
    # Do NOT include 'num_replicas' when autoscaling_config is present
}
```

### Preventive Measures

- Never set both `num_replicas` and `autoscaling_config` simultaneously
- Use `min_replicas` in autoscaling config to set initial replica count
- Document that autoscaling and manual replica configuration are mutually exclusive

---

## 11. Accelerator Type Not Recognized

### Error Description

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for LLMConfig
accelerator_type
  Value error, Unsupported accelerator type: L40 [type=value_error, input_value='L40', input_type=str]
```

### Cause

Ray Serve's `LLMConfig` has a limited set of supported accelerator types. The GPU was detected as `L40`, but Ray only recognizes `L4` (without the zero).

### Solution

Added accelerator type mapping in `src/deploy.py`:

```python
# Map common accelerator type variations to supported types
accelerator_type_raw = get_env_or_default("ACCELERATOR_TYPE", "L4")
accelerator_type_map = {
    "L40": "L4",  # Map L40 to L4 (common typo/misconfiguration)
    "l40": "L4",
    "l4": "L4",
}
accelerator_type = accelerator_type_map.get(accelerator_type_raw, accelerator_type_raw)

# Supported accelerator types for Ray Serve LLMConfig
supported_types = ["L4", "A100", "H100", "T4", "V100", "A10", "A10G"]

if accelerator_type not in supported_types:
    print(f"WARNING: Accelerator type '{accelerator_type}' may not be supported.")
    print(f"Supported types: {', '.join(supported_types)}")
    print(f"Attempting to continue anyway...")
```

**Alternative Solution:**

Update `.env` to use the supported accelerator type:

```bash
# In .env file
ACCELERATOR_TYPE=L4  # Instead of L40
```

### Preventive Measures

- Check Ray's supported accelerator types before configuration
- Add validation and mapping logic for common variations
- Document supported accelerator types in README
- Use `ray.cluster_resources()` to see detected accelerator type

---

## 12. Docker Compose Version Attribute Warning

### Error Description

```
level=warning msg="/path/to/docker-compose.yml: the attribute `version` is obsolete, it will be ignored"
```

### Cause

Docker Compose v2 no longer requires or uses the `version` attribute in `docker-compose.yml` files.

### Solution

Removed the `version` line from `docker-compose.yml`:

```yaml
# Before
version: '3.8'

services:
  ...

# After
services:
  ...
```

### Preventive Measures

- Remove `version` attribute from new docker-compose.yml files
- Docker Compose v2 is now the default and doesn't require version specification

---

## 13. Ray GPU Resource Allocation Errors

### Error Description

```
Error: No available node types can fulfill resource request {'GPU': 1.0, 'CPU': 1.0, 'accelerator_type:L4': 0.001}
```

### Cause

Multiple potential causes:
1. Accelerator type mismatch (L40 vs L4)
2. Ray not detecting GPUs correctly
3. Insufficient GPU resources for tensor parallelism

### Solution

1. **Verify GPU detection:**
   ```bash
   docker exec ray-serve nvidia-smi
   docker exec ray-serve python -c "import ray; ray.init(); print(ray.cluster_resources())"
   ```

2. **Check accelerator type mapping:**
   - Ensure `ACCELERATOR_TYPE` in `.env` matches Ray's detected type
   - Ray detects as `accelerator_type:L40`, but LLMConfig only accepts `L4`
   - Use the mapping solution from Issue #11

3. **Verify tensor parallelism size:**
   - `TENSOR_PARALLEL_SIZE=4` requires 4 GPUs
   - If only 2 GPUs available, reduce to `TENSOR_PARALLEL_SIZE=2`

4. **Check GPU availability:**
   ```bash
   # From host
   nvidia-smi
   
   # Check if GPUs are visible in container
   docker run --rm --gpus all nvidia/cuda:12.4.0-runtime-ubuntu22.04 nvidia-smi
   ```

### Preventive Measures

- Verify GPU count before setting `TENSOR_PARALLEL_SIZE`
- Match accelerator type to Ray's supported types
- Check Ray cluster resources before deployment
- Ensure Docker runtime is configured for GPU access (`runtime: nvidia` in docker-compose.yml)

---

## 14. Grafana Dashboard "rayServeDashboard" Not Found Error

### Error Description

```
ERROR: Failed to load dashboard
dashboards.dashboard.grafana.app "rayServeDashboard" not found
```

When accessing Ray Dashboard's metrics view at `http://localhost:18081/#/serve?...`, the dashboard fails to load with the above error.

### Cause

Ray Dashboard is trying to access Grafana dashboards using Grafana Operator APIs (Kubernetes Custom Resource Definitions), which require a Kubernetes cluster. In a Docker Compose setup, these CRDs don't exist, causing the 404 error.

The Grafana Operator API endpoints (`/apis/dashboard.grafana.app/v1beta1/...`) are designed for Kubernetes environments where dashboards are managed as CRDs.

### Solution

The Ray Serve dashboards have been automatically copied to Grafana's provisioning directory and are available directly in Grafana. You have two options:

**Option 1: Access Grafana Dashboard Directly (Recommended)**

Access the Ray Serve dashboard directly in Grafana:

```bash
# Direct URL (replace port if different)
http://localhost:13000/d/rayServeDashboard

# Or via Nginx proxy (if configured)
http://localhost:18081/grafana/d/rayServeDashboard
```

**Option 2: Import Dashboard Manually**

If the dashboard isn't automatically loaded, you can import it manually:

1. Access Grafana: `http://localhost:13000`
2. Login with credentials (default: `admin` / `admin`)
3. Go to Dashboards → Import
4. Copy the dashboard JSON from the Ray container:
   ```bash
   docker exec ray-serve cat /tmp/ray/session_latest/metrics/grafana/dashboards/serve_grafana_dashboard.json
   ```
5. Paste the JSON and import

**Automatic Dashboard Provisioning**

The setup automatically copies Ray-generated dashboards to Grafana's provisioning directory:
- `docker/grafana/provisioning/dashboards/ray_serve_dashboard.json`
- `docker/grafana/provisioning/dashboards/ray_serve_deployment_dashboard.json`

Grafana will automatically load these dashboards on startup.

### Verification

Verify the dashboard is loaded in Grafana:

```bash
# Check if dashboard exists via API
docker exec gpu-cluster-grafana curl -s -u admin:admin \
  "http://localhost:3000/api/dashboards/uid/rayServeDashboard" | \
  python3 -c "import sys, json; d=json.load(sys.stdin); \
  print('✓ Dashboard found:', d.get('dashboard', {}).get('title', 'N/A'))"
```

### Preventive Measures

- Ray-generated dashboards are automatically copied to Grafana provisioning directory
- Access dashboards directly in Grafana rather than through Ray Dashboard's embedded view
- If deploying on Kubernetes, use Grafana Operator for proper CRD support

---

## General Best Practices

### Environment Variables

1. **Always export environment variables before docker compose:**
   ```bash
   export $(cat .env | grep -v '^#' | xargs)
   docker compose up -d
   ```

2. **Verify environment variables are loaded:**
   ```bash
   docker compose config | grep -E "RAY_API_PORT|NGINX_HTTP_PORT"
   ```

### Docker Build Issues

1. **Use `--no-cache` when dependencies change:**
   ```bash
   docker compose build --no-cache
   ```

2. **Check container logs for runtime errors:**
   ```bash
   docker logs ray-serve
   docker logs gpu-cluster-nginx-proxy
   ```

### Ray Serve Debugging

1. **Check Ray status:**
   ```bash
   docker exec ray-serve ray status
   ```

2. **View Ray dashboard:**
   - Access at `http://localhost:RAY_DASHBOARD_PORT` (default 18265 if using custom ports)

3. **Check resource allocation:**
   ```bash
   docker exec ray-serve python -c "import ray; ray.init(); print(ray.cluster_resources())"
   ```

### Performance Optimization

1. **Increase shared memory size:**
   - Add to `docker-compose.yml`:
     ```yaml
     ray-serve:
       shm_size: '10gb'
     ```
   - Or use `--shm-size=10gb` in docker run

2. **Monitor GPU utilization:**
   ```bash
   watch -n 1 nvidia-smi
   ```

---

## Summary of All Fixes Applied

1. ✅ Created `.env` and `.secrets` files
2. ✅ Changed to `docker compose` (v2 syntax)
3. ✅ Updated ports to avoid conflicts (18080, 18000, 18265, 18443)
4. ✅ Changed nginx container name to `gpu-cluster-nginx-proxy`
5. ✅ Fixed UV PATH from `/root/.cargo/bin` to `/root/.local/bin`
6. ✅ Removed `--system` flag from `uv pip install`
7. ✅ Removed `UV_SYSTEM_PYTHON=1` environment variable
8. ✅ Added `--python 3.11` to `uv venv` command
9. ✅ Moved `num_replicas` to `deployment_config` (then removed it due to autoscaling)
10. ✅ Removed `num_replicas` when using autoscaling
11. ✅ Added accelerator type mapping (L40 → L4)
12. ✅ Removed `version` attribute from docker-compose.yml
13. ✅ Added Ray initialization with dashboard support

---

## Additional Notes

### Current Configuration

- **Ports:**
  - Ray API: 18000 (host) → 8000 (container)
  - Ray Dashboard: 18265 (host) → 8265 (container)
  - Nginx HTTP: 18080 (host) → 80 (container)
  - Nginx HTTPS: 18443 (host) → 443 (container)

- **GPU Configuration:**
  - Tensor Parallel Size: 4 (requires 4 GPUs)
  - Accelerator Type: L4 (mapped from L40)
  - Autoscaling: 1-4 replicas

### Testing the Deployment

Once all errors are resolved, test the deployment:

```bash
# Check services are running
docker ps | grep -E "(ray-serve|gpu-cluster-nginx)"

# Test API endpoint
curl http://localhost:18080/v1/models

# Check Ray dashboard
curl http://localhost:18265

# View logs
docker logs -f ray-serve
```

---

## References

- [Ray Serve Documentation](https://docs.ray.io/en/latest/serve/index.html)
- [vLLM Documentation](https://docs.vllm.ai/)
- [Docker Compose v2 Documentation](https://docs.docker.com/compose/)
- [UV Package Manager](https://github.com/astral-sh/uv)

