# Quick Start: Browser Testing for Multi-Model Deployment

## Current Status

**⚠️ Services need to be started first!**

The browser check shows:
- ❌ Ray Serve (port 8000) - Not running (404 on /v1/models)
- ❌ Ray Dashboard (port 8265) - Connection refused

## Steps to Start Services

### 1. Prepare Configuration

```bash
cd /home/aiserver/LABS/GPU-CLUSTER/gpu-cluster-with-ray-and-vllm

# Option A: Use test configuration with 3 small models
cat docker/test-models-config.env >> .env

# Option B: Or manually set MODELS_CONFIG in .env
```

### 2. Start Docker Compose

```bash
cd docker
docker-compose up -d ray-serve
```

### 3. Monitor Model Loading

Watch the logs to see models loading:
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

**⏱️ Wait 2-5 minutes** for models to download and load (first time only).

### 4. Test in Browser

Once models are loaded, test these URLs:

#### ✅ Models Endpoint
- **URL**: `http://localhost:8000/v1/models`
- **Expected**: JSON response with list of 3 models

#### ✅ Ray Dashboard
- **URL**: `http://localhost:8265`
- **Expected**: Ray Dashboard interface showing deployments

#### ✅ Test Individual Models
- Use the model IDs from `/v1/models` endpoint

### 5. Verify Response

**Expected JSON from `/v1/models`:**
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

## Troubleshooting

### Service Not Starting?
```bash
# Check if GPU is available
nvidia-smi

# Check docker-compose logs
cd docker
docker-compose logs ray-serve
```

### Models Not Loading?
- Check GPU memory: `nvidia-smi`
- Verify HuggingFace access (may need token in `.secrets`)
- Check logs for errors: `docker logs ray-serve`

### Still Getting 404?
- Wait longer for models to load (can take 5+ minutes)
- Check if route prefix is correct
- Verify MODELS_CONFIG JSON is valid

