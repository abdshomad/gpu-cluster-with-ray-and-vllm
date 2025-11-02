# User Guide - GPU Cluster Platform

This guide is for end users who want to interact with the LLM API service. It covers how to connect to the API, make requests, and use the available features.

## Table of Contents

1. [Quick Start](#quick-start)
2. [API Endpoints](#api-endpoints)
3. [Making Requests](#making-requests)
4. [OpenAI-Compatible Client](#openai-compatible-client)
5. [Using cURL](#using-curl)
6. [Python SDK Example](#python-sdk-example)
7. [Streaming Responses](#streaming-responses)
8. [Error Handling](#error-handling)
9. [API Reference](#api-reference)
10. [Best Practices](#best-practices)

---

## Quick Start

The GPU Cluster Platform provides an OpenAI-compatible API endpoint for LLM inference. You can connect to it using any OpenAI-compatible client library.

**Endpoint URL**: `http://localhost:{NGINX_HTTP_PORT}/v1`

Replace `{NGINX_HTTP_PORT}` with your configured port (default: `18080` if using custom ports, or `80` if using defaults).

**Example**:
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:18080/v1",
    api_key="not-needed"  # API key authentication is optional
)
```

---

## API Endpoints

### Primary Endpoints

- **Chat Completions**: `/v1/chat/completions` - Main endpoint for chat-based interactions
- **Models**: `/v1/models` - List available models
- **Health Check**: `/health` - Service health status

### Access Methods

You can access the API through two paths:

1. **Via Nginx Proxy (Recommended)**: `http://localhost:{NGINX_HTTP_PORT}/v1`
   - Unified access point
   - Load balancing (future)
   - SSL termination (future)

2. **Direct to Ray Serve**: `http://localhost:{RAY_API_PORT}/v1`
   - Direct connection to Ray Serve
   - Default port: `18000` (custom) or `8000` (default)

---

## Making Requests

### Chat Completions Request

The main endpoint accepts chat completion requests following the OpenAI API format:

```python
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-32B-Instruct",  # Model ID from deployment
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ],
    stream=True,  # Enable streaming
    temperature=0.7,
    max_tokens=1000
)
```

### Request Parameters

- **model** (required): The model identifier (as configured in deployment)
- **messages** (required): Array of message objects with `role` and `content`
  - `role`: `"user"`, `"assistant"`, or `"system"`
  - `content`: The message text
- **stream** (optional): Boolean to enable streaming responses (default: `false`)
- **temperature** (optional): Sampling temperature (0-2, default: 1.0)
- **max_tokens** (optional): Maximum tokens to generate (default: model-dependent)
- **top_p** (optional): Nucleus sampling parameter (default: 1.0)
- **frequency_penalty** (optional): Frequency penalty (-2.0 to 2.0, default: 0)
- **presence_penalty** (optional): Presence penalty (-2.0 to 2.0, default: 0)

---

## OpenAI-Compatible Client

### Python Client

The service is fully compatible with the OpenAI Python SDK:

```python
from openai import OpenAI

# Initialize client
client = OpenAI(
    base_url="http://localhost:18080/v1",
    api_key="not-needed"
)

# Make a request
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-32B-Instruct",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing in simple terms."}
    ],
    temperature=0.7,
    max_tokens=500
)

# Access the response
print(response.choices[0].message.content)
```

### JavaScript/TypeScript Client

```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'http://localhost:18080/v1',
  apiKey: 'not-needed',
});

const response = await client.chat.completions.create({
  model: 'Qwen/Qwen2.5-32B-Instruct',
  messages: [
    { role: 'user', content: 'Hello!' }
  ],
});

console.log(response.choices[0].message.content);
```

---

## Using cURL

### Non-Streaming Request

```bash
curl http://localhost:18080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-32B-Instruct",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

### Streaming Request

```bash
curl http://localhost:18080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "model": "Qwen/Qwen2.5-32B-Instruct",
    "messages": [
      {"role": "user", "content": "Tell me a story"}
    ],
    "stream": true
  }'
```

### List Available Models

```bash
curl http://localhost:18080/v1/models
```

### Health Check

```bash
curl http://localhost:18080/health
```

---

## Python SDK Example

### Complete Example Script

```python
#!/usr/bin/env python3
"""
Example script for interacting with the GPU Cluster Platform API
"""

from openai import OpenAI
import sys

def main():
    # Initialize client
    client = OpenAI(
        base_url="http://localhost:18080/v1",
        api_key="not-needed"
    )
    
    # Example 1: Simple non-streaming request
    print("=== Example 1: Simple Request ===")
    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-32B-Instruct",
        messages=[
            {"role": "user", "content": "What is machine learning?"}
        ],
        temperature=0.7,
        max_tokens=200
    )
    print(response.choices[0].message.content)
    print()
    
    # Example 2: Streaming request
    print("=== Example 2: Streaming Request ===")
    stream = client.chat.completions.create(
        model="Qwen/Qwen2.5-32B-Instruct",
        messages=[
            {"role": "user", "content": "Write a haiku about AI"}
        ],
        stream=True
    )
    
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n")
    
    # Example 3: Conversation with context
    print("=== Example 3: Multi-turn Conversation ===")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "My name is Alice."},
    ]
    
    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-32B-Instruct",
        messages=messages,
        temperature=0.7
    )
    
    assistant_message = response.choices[0].message.content
    print(f"Assistant: {assistant_message}")
    
    # Add assistant response and continue conversation
    messages.append({"role": "assistant", "content": assistant_message})
    messages.append({"role": "user", "content": "What's my name?"})
    
    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-32B-Instruct",
        messages=messages
    )
    print(f"Assistant: {response.choices[0].message.content}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

---

## Streaming Responses

Streaming allows you to receive tokens as they are generated, providing a better user experience for longer responses.

### Python Streaming Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:18080/v1",
    api_key="not-needed"
)

print("Sending request to vLLM on Ray Serve...")
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-32B-Instruct",
    messages=[
        {"role": "user", "content": "Explain neural networks in detail."}
    ],
    stream=True
)

print("Response: ", end="", flush=True)
for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print("\nStream complete.")
```

### Handling Streaming Responses

```python
def handle_streaming_response(stream):
    """Process streaming response chunks."""
    full_response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            full_response += content
            # Process chunk (e.g., display to user, save to buffer)
            yield content
    
    return full_response

# Usage
for token in handle_streaming_response(response):
    print(token, end="", flush=True)
```

---

## Error Handling

### Common Error Responses

#### 503 Service Unavailable
The service may be temporarily unavailable due to:
- Model is still loading
- All replicas are at capacity
- Service is restarting

**Solution**: Retry with exponential backoff

```python
import time
from openai import OpenAI

client = OpenAI(base_url="http://localhost:18080/v1", api_key="not-needed")

def make_request_with_retry(messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model="Qwen/Qwen2.5-32B-Instruct",
                messages=messages
            )
        except Exception as e:
            if "503" in str(e) and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Service unavailable, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

response = make_request_with_retry([
    {"role": "user", "content": "Hello!"}
])
```

#### 400 Bad Request
Invalid request parameters or malformed JSON.

**Solution**: Check request format and parameters

#### 404 Not Found
Model not found or endpoint doesn't exist.

**Solution**: Verify model ID matches deployment configuration

### Error Response Format

```json
{
  "error": {
    "message": "Error description",
    "type": "invalid_request_error",
    "code": "model_not_found"
  }
}
```

---

## API Reference

### POST /v1/chat/completions

Create a chat completion.

**Request Body**:
```json
{
  "model": "string (required)",
  "messages": [
    {
      "role": "user|assistant|system",
      "content": "string"
    }
  ],
  "stream": false,
  "temperature": 1.0,
  "max_tokens": null,
  "top_p": 1.0,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0
}
```

**Response** (non-streaming):
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "Qwen/Qwen2.5-32B-Instruct",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Response text..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
```

**Response** (streaming):
Server-Sent Events (SSE) format:
```
data: {"id":"...","choices":[{"delta":{"content":"Hello"}}]}
data: {"id":"...","choices":[{"delta":{"content":" there"}}]}
data: [DONE]
```

### GET /v1/models

List available models.

**Response**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "Qwen/Qwen2.5-32B-Instruct",
      "object": "model",
      "created": 1234567890,
      "owned_by": "vllm"
    }
  ]
}
```

---

## Best Practices

### 1. Connection Management

- Reuse client instances instead of creating new ones for each request
- Use connection pooling for high-throughput scenarios

```python
# Good: Reuse client
client = OpenAI(base_url="http://localhost:18080/v1", api_key="not-needed")
for request in requests:
    response = client.chat.completions.create(...)

# Bad: Create new client for each request
for request in requests:
    client = OpenAI(base_url="http://localhost:18080/v1", api_key="not-needed")
    response = client.chat.completions.create(...)
```

### 2. Error Handling

- Always implement retry logic for transient errors
- Use exponential backoff for rate limiting and service unavailability
- Log errors for debugging

### 3. Streaming

- Use streaming for better user experience with long responses
- Handle connection drops gracefully
- Buffer tokens if needed for processing

### 4. Token Management

- Monitor token usage for cost/rate limit management
- Set appropriate `max_tokens` to prevent runaway generation
- Use `usage` field in responses to track consumption

### 5. Request Batching

- Batch multiple requests when possible (if supported)
- Avoid sending many small requests in quick succession

### 6. Timeout Configuration

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:18080/v1",
    api_key="not-needed",
    timeout=60.0  # Set appropriate timeout
)
```

### 7. Model Selection

- Always specify the exact model ID used in deployment
- Check available models via `/v1/models` endpoint

### 8. Security

- When deployed in production, use HTTPS endpoints
- Implement proper authentication if required
- Never expose API endpoints publicly without authentication

---

## Troubleshooting

### Connection Refused

**Symptom**: `Connection refused` or `Connection timeout`

**Solutions**:
1. Verify the service is running: `curl http://localhost:18080/health`
2. Check port configuration matches `.env` file
3. Verify firewall settings allow connections

### Slow Responses

**Possible Causes**:
- High load on the service
- Large input prompts
- Model complexity

**Solutions**:
1. Monitor service metrics (if available)
2. Reduce input size or `max_tokens`
3. Contact operator to check service health

### Model Not Found

**Symptom**: `404` or `model_not_found` error

**Solutions**:
1. Check available models: `curl http://localhost:18080/v1/models`
2. Verify model ID matches deployment configuration
3. Ensure model has finished loading (check service logs)

---

## Additional Resources

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference) - Compatible API reference
- [Ray Serve Documentation](https://docs.ray.io/en/latest/serve/index.html) - Underlying serving framework
- [vLLM Documentation](https://docs.vllm.ai/) - Inference engine details

---

## Support

For issues or questions:
1. Check the [Troubleshooting Guide](../trouble-shooting.md)
2. Review service logs (contact operator)
3. Check Ray Dashboard for service status

