# AA001: Multi-Model Deployment - Testing Guide

## Quick Test with 3 Small Models

For quick testing, we've prepared a configuration with 3 small models from different organizations:

1. **Meta**: `meta-llama/Llama-3.2-1B-Instruct` (1B parameters)
2. **DeepSeek**: `deepseek-ai/DeepSeek-R1-1.5B` (1.5B parameters)  
3. **Qwen**: `Qwen/Qwen2.5-1.5B-Instruct` (1.5B parameters)

**See `docs/test-multi-model.md` for detailed testing instructions.**

**Quick Start:**
```bash
# Use the test configuration
cat docker/test-models-config.env >> .env

# Start services
cd docker && docker-compose up -d ray-serve

# Wait for models to load, then test
./scripts/test-multi-model.sh
```

## Implementation Summary

AA001 has been implemented with the following features:

1. ✅ **Model Manager Module** (`src/models/model_manager.py`)
   - Parses MODELS_CONFIG JSON from environment
   - Falls back to single MODEL_ID (backward compatible)
   - Tracks model configurations and metadata

2. ✅ **Updated Deployment Script** (`src/deploy.py`)
   - Supports both single and multi-model configurations
   - Creates LLMConfig for each model
   - Deploys all models via build_openai_app

3. ✅ **Model Registry**
   - Tracks all deployed models
   - Provides metadata for /v1/models endpoint

## Configuration

### Multi-Model Configuration (New)

Set `MODELS_CONFIG` environment variable with JSON array:

```bash
MODELS_CONFIG='[
  {
    "model_id": "Qwen/Qwen2.5-32B-Instruct",
    "route_prefix": "/v1",
    "tensor_parallel_size": 4,
    "accelerator_type": "L4",
    "min_replicas": 1,
    "max_replicas": 4
  },
  {
    "model_id": "meta-llama/Llama-3-8B-Instruct",
    "route_prefix": "/v1",
    "tensor_parallel_size": 2,
    "accelerator_type": "L4",
    "min_replicas": 1,
    "max_replicas": 2
  }
]'
```

### Single Model Configuration (Backward Compatible)

If `MODELS_CONFIG` is not set, use individual environment variables:
- `MODEL_ID`
- `TENSOR_PARALLEL_SIZE`
- `ACCELERATOR_TYPE`
- etc.

## Testing

### 1. Start Services

```bash
cd docker
docker-compose up -d
```

### 2. Check Models Endpoint

**Via Browser (with correct ports):**
- **Direct Ray Serve**: `http://localhost:8000/v1/models` ✅ (port 8000 - recommended)
- **Via Nginx proxy**: `http://localhost/v1/models` (port 80, if nginx is running)

**Via curl:**
```bash
# Direct Ray Serve endpoint (port 8000)
curl http://localhost:8000/v1/models

# Or via Nginx proxy (port 80)
curl http://localhost/v1/models
```

**Expected Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "Qwen/Qwen2.5-32B-Instruct",
      "object": "model",
      "created": null,
      "owned_by": "ray-serve",
      ...
    },
    {
      "id": "meta-llama/Llama-3-8B-Instruct",
      "object": "model",
      ...
    }
  ]
}
```

### 3. Test Model Inference

Use any model from the list:

```bash
curl http://localhost/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-32B-Instruct",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### 4. Verify in Ray Dashboard

- Navigate to: `http://localhost:8265` (Ray Dashboard) or `http://localhost/dashboard` (via Nginx)
- Check "Serve Applications" tab
- Should see `multi_model_serve` deployment
- Check "Actors" tab to see model deployments

## Files Modified/Created

- ✅ `src/models/__init__.py` - Module initialization
- ✅ `src/models/model_manager.py` - Model management and parsing
- ✅ `src/deploy.py` - Updated for multi-model support
- ✅ `requirements.txt` - Added fastapi

## Next Steps

After verifying AA001 works:
- Mark AA001 as completed in next-plan.md
- Proceed with AA002 (Multi-Node/Multi-Cluster Support)

