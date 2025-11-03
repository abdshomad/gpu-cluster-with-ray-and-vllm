# Testing Multi-Model Deployment (AA001)

## Quick Start with 3 Small Test Models

This guide shows how to test the multi-model deployment with 3 small models from different organizations:
- **Meta**: Llama-3.2-1B-Instruct
- **DeepSeek**: DeepSeek-R1-1.5B  
- **Qwen**: Qwen2.5-1.5B-Instruct

## Configuration

A test configuration file is available at `docker/test-models-config.env` that includes all three models.

## Option 1: Use Test Configuration File

1. **Copy test config to .env** (or merge with your existing .env):
```bash
cd docker
cat ../docker/test-models-config.env >> ../.env
```

2. **Or use it directly with docker-compose**:
```bash
cd docker
docker-compose --env-file ../docker/test-models-config.env up -d
```

## Option 2: Set Environment Variable Directly

Add this to your `.env` file:

```bash
MODELS_CONFIG='[
  {
    "model_id": "meta-llama/Llama-3.2-1B-Instruct",
    "tensor_parallel_size": 1,
    "accelerator_type": "L4",
    "min_replicas": 1,
    "max_replicas": 2
  },
  {
    "model_id": "deepseek-ai/DeepSeek-R1-1.5B",
    "tensor_parallel_size": 1,
    "accelerator_type": "L4",
    "min_replicas": 1,
    "max_replicas": 2
  },
  {
    "model_id": "Qwen/Qwen2.5-1.5B-Instruct",
    "tensor_parallel_size": 1,
    "accelerator_type": "L4",
    "min_replicas": 1,
    "max_replicas": 2
  }
]'
```

## Testing Steps

### 1. Start Services

```bash
cd docker
docker-compose up -d ray-serve
```

### 2. Wait for Models to Load

Monitor the logs to see all 3 models loading:
```bash
docker logs -f ray-serve
```

Look for:
```
Parsed 3 model configuration(s)
Configuring model: meta-llama/Llama-3.2-1B-Instruct
Configuring model: deepseek-ai/DeepSeek-R1-1.5B
Configuring model: Qwen/Qwen2.5-1.5B-Instruct
Deploying 3 model(s) with Ray Serve...
```

### 3. Test Models Endpoint

**Via Browser (with ports):**
- **Direct Ray Serve**: `http://localhost:8000/v1/models` (port 8000)
- **Via Nginx proxy**: `http://localhost/v1/models` (port 80, if nginx is running)

**Via curl:**
```bash
# Direct Ray Serve endpoint
curl http://localhost:8000/v1/models | jq

# Or via Nginx proxy
curl http://localhost/v1/models | jq
```

**Expected Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "meta-llama/Llama-3.2-1B-Instruct",
      "object": "model",
      "owned_by": "ray-serve"
    },
    {
      "id": "deepseek-ai/DeepSeek-R1-1.5B",
      "object": "model",
      "owned_by": "ray-serve"
    },
    {
      "id": "Qwen/Qwen2.5-1.5B-Instruct",
      "object": "model",
      "owned_by": "ray-serve"
    }
  ]
}
```

### 4. Test Each Model

**Test Meta Llama:**
```bash
curl http://localhost/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.2-1B-Instruct",
    "messages": [{"role": "user", "content": "Hello! What is 2+2?"}],
    "max_tokens": 50
  }' | jq
```

**Test DeepSeek:**
```bash
curl http://localhost/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-R1-1.5B",
    "messages": [{"role": "user", "content": "Hello! What is 2+2?"}],
    "max_tokens": 50
  }' | jq
```

**Test Qwen:**
```bash
curl http://localhost/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "messages": [{"role": "user", "content": "Hello! What is 2+2?"}],
    "max_tokens": 50
  }' | jq
```

### 5. Verify in Ray Dashboard

- Navigate to: `http://localhost:8265` (Ray Dashboard) or `http://localhost/dashboard` (via Nginx)
- Go to "Serve Applications" tab
- Should see `multi_model_serve` with 3 model deployments
- Check "Actors" tab to see all 3 model actors running

## Model Details

| Model | Organization | Size | Parameters |
|-------|-------------|------|------------|
| Llama-3.2-1B-Instruct | Meta | 1B | ~2GB |
| DeepSeek-R1-1.5B | DeepSeek | 1.5B | ~3GB |
| Qwen2.5-1.5B-Instruct | Alibaba (Qwen) | 1.5B | ~3GB |

**Total VRAM Required:** ~8GB (with tensor_parallel_size=1 per model)

## Troubleshooting

1. **Models not loading**: Check GPU availability and VRAM
2. **Endpoint returns 404**: Wait for models to finish loading
3. **Model selection fails**: Verify model ID matches exactly (case-sensitive)

## Notes

- All models use `tensor_parallel_size=1` for testing (single GPU per model)
- Models are configured for minimal resource usage
- For production, increase `tensor_parallel_size` and `max_replicas` as needed

