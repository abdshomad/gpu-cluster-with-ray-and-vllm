# Configurator Guide - GPU Cluster Platform

This guide is for configurators responsible for configuring and tuning the GPU Cluster Platform. It covers all configuration options, environment variables, and tuning parameters.

## Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Environment Variables](#environment-variables)
3. [Model Configuration](#model-configuration)
4. [Scaling Configuration](#scaling-configuration)
5. [vLLM Engine Configuration](#vllm-engine-configuration)
6. [Network Configuration](#network-configuration)
7. [Monitoring Configuration](#monitoring-configuration)
8. [Performance Tuning](#performance-tuning)
9. [Configuration Examples](#configuration-examples)
10. [Configuration Validation](#configuration-validation)
11. [Advanced Configuration](#advanced-configuration)

---

## Configuration Overview

The GPU Cluster Platform uses environment variables for configuration, loaded from:

- **`.env`**: Non-sensitive configuration (tracked in git)
- **`.secrets`**: Sensitive data like API keys (gitignored)

All configuration is loaded via Docker Compose's `env_file` directive.

### Configuration File Location

```bash
# Main configuration
.env

# Secrets (create from template)
.secrets
```

### Configuration Reload

Most configuration changes require service restart:

```bash
# After editing .env
docker compose restart ray-serve

# After editing .secrets
docker compose restart ray-serve
```

---

## Environment Variables

### Complete Reference

#### Model Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_ID` | `Qwen/Qwen2.5-32B-Instruct` | HuggingFace model identifier |
| `MODEL_SOURCE` | (empty) | Local path for pre-downloaded models |
| `TENSOR_PARALLEL_SIZE` | `4` | Number of GPUs for tensor parallelism |
| `ACCELERATOR_TYPE` | `L4` | GPU type (L4, A100, H100, T4, V100, A10, A10G) |

#### Scaling Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MIN_REPLICAS` | `1` | Minimum autoscaling replicas |
| `MAX_REPLICAS` | `4` | Maximum autoscaling replicas |
| `TARGET_ONGOING_REQUESTS` | `32` | Target concurrent requests per replica |
| `MAX_ONGOING_REQUESTS` | `64` | Maximum concurrent requests per replica |

#### Port Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `RAY_API_PORT` | `18000` | Host port for Ray Serve API |
| `RAY_DASHBOARD_PORT` | `18265` | Host port for Ray Dashboard |
| `NGINX_HTTP_PORT` | `18080` | Nginx HTTP port on host |
| `NGINX_HTTPS_PORT` | `18443` | Nginx HTTPS port on host |

#### Ray Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `RAY_METRICS_EXPORT_PORT` | `8080` | Prometheus metrics export port |
| `ROUTE_PREFIX` | `/v1` | API route prefix |

#### vLLM Engine Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_NUM_BATCHED_TOKENS` | `8192` | Maximum batched tokens |
| `MAX_MODEL_LEN` | `8192` | Maximum model context length |
| `MAX_NUM_SEQS` | `64` | Maximum concurrent sequences |
| `TRUST_REMOTE_CODE` | `true` | Trust remote code in model |
| `ENABLE_PREFIX_CACHING` | `true` | Enable prefix caching |

#### Secrets

| Variable | Required | Description |
|----------|----------|-------------|
| `HUGGINGFACE_TOKEN` | Conditional | HuggingFace API token (required for private models) |

---

## Model Configuration

### Selecting a Model

#### Public Models

```bash
# In .env
MODEL_ID=Qwen/Qwen2.5-32B-Instruct
```

Common model options:
- `Qwen/Qwen2.5-32B-Instruct`
- `meta-llama/Llama-2-70b-chat-hf`
- `mistralai/Mistral-7B-Instruct-v0.2`

#### Private Models

```bash
# In .env
MODEL_ID=your-org/private-model-name

# In .secrets
HUGGINGFACE_TOKEN=hf_your_token_here
```

### Using Pre-downloaded Models

For faster startup or offline deployment:

```bash
# Download model first
huggingface-cli download Qwen/Qwen2.5-32B-Instruct --local-dir /path/to/models/Qwen2.5-32B-Instruct

# Configure in .env
MODEL_SOURCE=/path/to/models/Qwen2.5-32B-Instruct
```

**Note**: Model source path must be accessible inside container (use volume mount if needed).

### Tensor Parallelism

Tensor parallelism distributes model across multiple GPUs:

```bash
# 4 GPUs (default)
TENSOR_PARALLEL_SIZE=4

# 2 GPUs
TENSOR_PARALLEL_SIZE=2

# 8 GPUs
TENSOR_PARALLEL_SIZE=8
```

**Requirements**:
- `TENSOR_PARALLEL_SIZE` must not exceed available GPUs
- More GPUs = lower latency, higher throughput
- Fewer GPUs = lower resource usage

### Accelerator Type

Specify GPU type for resource allocation:

```bash
# L4 GPU (default)
ACCELERATOR_TYPE=L4

# Other supported types
ACCELERATOR_TYPE=A100
ACCELERATOR_TYPE=H100
ACCELERATOR_TYPE=T4
ACCELERATOR_TYPE=V100
ACCELERATOR_TYPE=A10
ACCELERATOR_TYPE=A10G
```

**Supported Types**: L4, A100, H100, T4, V100, A10, A10G

**Note**: Common variations are auto-mapped (e.g., `L40` → `L4`).

---

## Scaling Configuration

### Autoscaling

Autoscaling dynamically adjusts replicas based on load:

```bash
# Minimum replicas (always running)
MIN_REPLICAS=1

# Maximum replicas (scale up limit)
MAX_REPLICAS=4

# Target concurrent requests per replica
TARGET_ONGOING_REQUESTS=32

# Maximum concurrent requests per replica
MAX_ONGOING_REQUESTS=64
```

### How Autoscaling Works

1. **Target**: Ray Serve maintains `TARGET_ONGOING_REQUESTS` per replica
2. **Scale Up**: If average requests per replica > target, add replicas
3. **Scale Down**: If average requests per replica < target, remove replicas
4. **Bounds**: Replicas stay between `MIN_REPLICAS` and `MAX_REPLICAS`

### Tuning Autoscaling

**For Higher Throughput**:
```bash
TARGET_ONGOING_REQUESTS=64  # More requests per replica
MAX_REPLICAS=8              # Allow more replicas
```

**For Lower Latency**:
```bash
TARGET_ONGOING_REQUESTS=16  # Fewer requests per replica
MIN_REPLICAS=2              # Always have multiple replicas
```

**For Cost Optimization**:
```bash
TARGET_ONGOING_REQUESTS=64  # Maximize replica utilization
MAX_REPLICAS=2              # Limit resource usage
```

### Fixed Replicas (No Autoscaling)

If autoscaling is not desired, set min = max:

```bash
MIN_REPLICAS=2
MAX_REPLICAS=2
TARGET_ONGOING_REQUESTS=32
```

---

## vLLM Engine Configuration

### Performance Tuning Parameters

#### Batch Size Configuration

```bash
# Maximum batched tokens (affects throughput)
MAX_NUM_BATCHED_TOKENS=8192

# Maximum concurrent sequences
MAX_NUM_SEQS=64
```

**Higher values**:
- ✅ Higher throughput
- ❌ Higher memory usage
- ❌ Potential OOM errors

**Lower values**:
- ✅ Lower memory usage
- ❌ Lower throughput
- ✅ More stable

#### Context Length

```bash
# Maximum model context length
MAX_MODEL_LEN=8192
```

**Adjust based on**:
- Model's native context length
- Typical prompt length
- Available GPU memory

#### Prefix Caching

```bash
# Enable prefix caching for better performance
ENABLE_PREFIX_CACHING=true
```

**Benefits**:
- Faster responses for repeated prompts
- Lower GPU memory usage for cached prefixes

**Trade-offs**:
- Slight memory overhead for cache

#### Remote Code Trust

```bash
# Trust remote code in model (required for some models)
TRUST_REMOTE_CODE=true
```

**Security Note**: Only enable for trusted models.

### Memory Optimization

For models that don't fit:

```bash
# Reduce context length
MAX_MODEL_LEN=4096

# Reduce batch size
MAX_NUM_BATCHED_TOKENS=4096
MAX_NUM_SEQS=32
```

### Throughput Optimization

For maximum throughput:

```bash
# Increase batch capacity
MAX_NUM_BATCHED_TOKENS=16384
MAX_NUM_SEQS=128

# Enable prefix caching
ENABLE_PREFIX_CACHING=true
```

---

## Network Configuration

### Port Configuration

Configure ports to avoid conflicts:

```bash
# Ray Serve API
RAY_API_PORT=18000

# Ray Dashboard
RAY_DASHBOARD_PORT=18265

# Nginx HTTP
NGINX_HTTP_PORT=18080

# Nginx HTTPS
NGINX_HTTPS_PORT=18443
```

### Port Mapping

Container internal ports (fixed):
- Ray API: `8000` (always)
- Ray Dashboard: `8265` (always)
- Nginx: `80` (HTTP), `443` (HTTPS)

Host ports are configurable via environment variables.

### Route Prefix

```bash
# API route prefix
ROUTE_PREFIX=/v1

# Alternative prefixes
ROUTE_PREFIX=/api/v1
ROUTE_PREFIX=/llm
```

---

## Monitoring Configuration

### Prometheus Metrics

```bash
# Prometheus metrics export port (container internal)
RAY_METRICS_EXPORT_PORT=8080
```

This port is used by Prometheus to scrape Ray metrics. The port is internal to the container; no host mapping needed.

### Monitoring Stack Ports

If using the included Prometheus/Grafana stack:

```bash
# Prometheus (configure in docker-compose.yml)
PROMETHEUS_PORT=19090

# Grafana (configure in docker-compose.yml)
GRAFANA_PORT=13000
```

---

## Performance Tuning

### GPU Memory Considerations

**Formula**: GPU Memory Required ≈ Model Size × Tensor Parallel Size

Example:
- 32B parameter model ≈ 64GB
- With `TENSOR_PARALLEL_SIZE=4`: ~16GB per GPU
- Add overhead: Ensure 20-24GB GPU memory available

### Recommended Configurations

#### High Performance (High Throughput)

```bash
# .env
MODEL_ID=Qwen/Qwen2.5-32B-Instruct
TENSOR_PARALLEL_SIZE=4
ACCELERATOR_TYPE=L4
MIN_REPLICAS=2
MAX_REPLICAS=8
TARGET_ONGOING_REQUESTS=64
MAX_NUM_BATCHED_TOKENS=16384
MAX_NUM_SEQS=128
ENABLE_PREFIX_CACHING=true
```

#### Balanced

```bash
# .env (default)
MODEL_ID=Qwen/Qwen2.5-32B-Instruct
TENSOR_PARALLEL_SIZE=4
ACCELERATOR_TYPE=L4
MIN_REPLICAS=1
MAX_REPLICAS=4
TARGET_ONGOING_REQUESTS=32
MAX_NUM_BATCHED_TOKENS=8192
MAX_NUM_SEQS=64
ENABLE_PREFIX_CACHING=true
```

#### Cost Optimized

```bash
# .env
MODEL_ID=Qwen/Qwen2.5-32B-Instruct
TENSOR_PARALLEL_SIZE=2  # Fewer GPUs
ACCELERATOR_TYPE=L4
MIN_REPLICAS=1
MAX_REPLICAS=2  # Lower max replicas
TARGET_ONGOING_REQUESTS=64  # Higher per-replica utilization
MAX_NUM_BATCHED_TOKENS=4096  # Lower batch size
MAX_NUM_SEQS=32
ENABLE_PREFIX_CACHING=true
```

### Tuning Checklist

- [ ] GPU memory usage: `nvidia-smi`
- [ ] KV cache utilization: Monitor in Grafana
- [ ] Request latency: Track P95 latency
- [ ] Throughput: Monitor requests per second
- [ ] Error rate: Track errors
- [ ] Autoscaling behavior: Verify scaling up/down

---

## Configuration Examples

### Example 1: Production Deployment

```bash
# .env
MODEL_ID=Qwen/Qwen2.5-32B-Instruct
TENSOR_PARALLEL_SIZE=4
ACCELERATOR_TYPE=L4

MIN_REPLICAS=2
MAX_REPLICAS=8
TARGET_ONGOING_REQUESTS=32
MAX_ONGOING_REQUESTS=64

RAY_API_PORT=8000
RAY_DASHBOARD_PORT=8265
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443

RAY_METRICS_EXPORT_PORT=8080
ROUTE_PREFIX=/v1

MAX_NUM_BATCHED_TOKENS=8192
MAX_MODEL_LEN=8192
MAX_NUM_SEQS=64
TRUST_REMOTE_CODE=true
ENABLE_PREFIX_CACHING=true
```

```bash
# .secrets
HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Example 2: Development/Testing

```bash
# .env
MODEL_ID=Qwen/Qwen2.5-32B-Instruct
TENSOR_PARALLEL_SIZE=2
ACCELERATOR_TYPE=L4

MIN_REPLICAS=1
MAX_REPLICAS=2
TARGET_ONGOING_REQUESTS=16
MAX_ONGOING_REQUESTS=32

RAY_API_PORT=18000
RAY_DASHBOARD_PORT=18265
NGINX_HTTP_PORT=18080

MAX_NUM_BATCHED_TOKENS=4096
MAX_MODEL_LEN=4096
MAX_NUM_SEQS=32
```

### Example 3: Large Model (70B+)

```bash
# .env
MODEL_ID=meta-llama/Llama-2-70b-chat-hf
TENSOR_PARALLEL_SIZE=8  # More GPUs for large model
ACCELERATOR_TYPE=A100

MIN_REPLICAS=1
MAX_REPLICAS=4
TARGET_ONGOING_REQUESTS=16  # Lower for large models
MAX_ONGOING_REQUESTS=32

MAX_NUM_BATCHED_TOKENS=4096  # Lower batch size
MAX_MODEL_LEN=4096
MAX_NUM_SEQS=16  # Fewer concurrent sequences
```

---

## Configuration Validation

### Validation Script

```bash
#!/bin/bash
# validate_config.sh

source .env

# Check required variables
if [ -z "$MODEL_ID" ]; then
    echo "ERROR: MODEL_ID not set"
    exit 1
fi

# Check port conflicts
check_port() {
    if lsof -i :$1 > /dev/null 2>&1; then
        echo "WARNING: Port $1 is already in use"
    fi
}

check_port $RAY_API_PORT
check_port $RAY_DASHBOARD_PORT
check_port $NGINX_HTTP_PORT

# Check GPU count vs tensor parallel size
GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
if [ "$TENSOR_PARALLEL_SIZE" -gt "$GPU_COUNT" ]; then
    echo "ERROR: TENSOR_PARALLEL_SIZE ($TENSOR_PARALLEL_SIZE) exceeds available GPUs ($GPU_COUNT)"
    exit 1
fi

# Check accelerator type
SUPPORTED_TYPES="L4 A100 H100 T4 V100 A10 A10G"
if ! echo "$SUPPORTED_TYPES" | grep -q "$ACCELERATOR_TYPE"; then
    echo "WARNING: ACCELERATOR_TYPE $ACCELERATOR_TYPE may not be supported"
fi

echo "Configuration validation passed"
```

### Docker Compose Validation

```bash
# Validate docker-compose.yml
docker compose config

# Check environment variable substitution
docker compose config | grep -E "RAY_API_PORT|MODEL_ID"
```

### Runtime Validation

After deployment, verify configuration:

```bash
# Check Ray cluster resources
docker exec ray-serve python -c "import ray; ray.init(); print(ray.cluster_resources())"

# Verify model deployment
curl http://localhost:18080/v1/models

# Check Ray Dashboard
curl http://localhost:18265
```

---

## Advanced Configuration

### Multi-Node Configuration

For multi-node deployments:

```bash
# .env
RAY_HEAD_HOST=192.168.1.100  # Head node IP
```

**Note**: Additional Ray cluster setup required beyond `.env` configuration.

### Custom vLLM Arguments

To add custom vLLM arguments, modify `src/deploy.py`:

```python
engine_kwargs={
    'tensor_parallel_size': tensor_parallel_size,
    'max_num_batched_tokens': max_num_batched_tokens,
    # Add custom arguments
    'gpu_memory_utilization': 0.9,
    'swap_space': 4,
}
```

### Environment Variable Overrides

Override environment variables at runtime:

```bash
# Override via docker-compose
RAY_API_PORT=19000 docker compose up -d

# Or export before compose
export MODEL_ID=custom-model
docker compose up -d
```

---

## Best Practices

### 1. Configuration Management

- **Version Control**: Commit `.env` to git (not `.secrets`)
- **Documentation**: Document all custom configurations
- **Backup**: Backup configuration before changes
- **Testing**: Test changes in staging first

### 2. Performance Tuning

- **Measure First**: Establish baseline metrics
- **Change One Thing**: Make incremental changes
- **Monitor Impact**: Track metrics after changes
- **Document Results**: Record what works

### 3. Security

- **Never Commit Secrets**: Verify `.secrets` is gitignored
- **Rotate Secrets**: Change tokens periodically
- **Minimize Permissions**: Use least privilege
- **Audit Configuration**: Review config regularly

### 4. Troubleshooting

- **Log Changes**: Document all config changes
- **Rollback Plan**: Keep previous config backed up
- **Test Incrementally**: Make small changes
- **Verify After Changes**: Test after each change

---

## Additional Resources

- [vLLM Ray Serve Guide](../vllm-ray-serve-guide.md) - Technical deployment details
- [Troubleshooting Guide](../trouble-shooting.md) - Configuration-related issues
- [Ray Serve Documentation](https://docs.ray.io/en/latest/serve/index.html)
- [vLLM Documentation](https://docs.vllm.ai/)

---

## Support

For configuration issues:
1. Check [Troubleshooting Guide](../trouble-shooting.md)
2. Validate configuration with validation script
3. Review service logs after changes
4. Check Ray Dashboard for deployment status

