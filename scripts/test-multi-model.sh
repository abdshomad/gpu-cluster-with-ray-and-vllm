#!/bin/bash
# Quick test script for multi-model deployment (AA001)
# Tests the /v1/models endpoint and individual model inference

set -e

# Default to Ray Serve direct port (8000) if no argument provided
BASE_URL="${1:-http://localhost:8000}"
API_URL="${BASE_URL}/v1"
MODELS_ENDPOINT="${API_URL}/models"

echo "Using endpoint: ${MODELS_ENDPOINT}"

echo "🧪 Testing Multi-Model Deployment (AA001)"
echo "=========================================="
echo ""

# Test 1: Check if service is running
echo "1️⃣  Checking if service is running..."
if ! curl -s -f "${BASE_URL}/health" > /dev/null 2>&1; then
    echo "   ⚠️  Service health check failed. Is docker-compose running?"
    echo "   Run: cd docker && docker-compose up -d"
    exit 1
fi
echo "   ✅ Service is running"
echo ""

# Test 2: List available models
echo "2️⃣  Listing available models..."
MODELS_RESPONSE=$(curl -s "${MODELS_ENDPOINT}")
if [ $? -ne 0 ]; then
    echo "   ❌ Failed to fetch models list"
    exit 1
fi

MODEL_COUNT=$(echo "$MODELS_RESPONSE" | jq '.data | length' 2>/dev/null || echo "0")
echo "   📊 Found $MODEL_COUNT model(s)"
echo ""

if [ "$MODEL_COUNT" -eq "0" ]; then
    echo "   ⚠️  No models found. Waiting for models to load..."
    echo "   Check logs: docker logs -f ray-serve"
    exit 1
fi

# Display models
echo "   Available models:"
echo "$MODELS_RESPONSE" | jq -r '.data[] | "   - \(.id)"' 2>/dev/null || echo "$MODELS_RESPONSE"
echo ""

# Test 3: Test inference for each model
echo "3️⃣  Testing inference for each model..."
MODEL_IDS=$(echo "$MODELS_RESPONSE" | jq -r '.data[].id' 2>/dev/null)

if [ -z "$MODEL_IDS" ]; then
    echo "   ⚠️  Could not parse model IDs. Showing raw response:"
    echo "$MODELS_RESPONSE"
    exit 1
fi

SUCCESS_COUNT=0
FAIL_COUNT=0

for MODEL_ID in $MODEL_IDS; do
    echo "   Testing: $MODEL_ID"
    RESPONSE=$(curl -s "${API_URL}/chat/completions" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"${MODEL_ID}\",
            \"messages\": [{\"role\": \"user\", \"content\": \"Say hello in one word.\"}],
            \"max_tokens\": 10
        }")
    
    if echo "$RESPONSE" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
        CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content')
        echo "      ✅ Response: $CONTENT"
        ((SUCCESS_COUNT++))
    else
        ERROR=$(echo "$RESPONSE" | jq -r '.error.message // .error.code // "Unknown error"' 2>/dev/null || echo "$RESPONSE")
        echo "      ❌ Error: $ERROR"
        ((FAIL_COUNT++))
    fi
    echo ""
done

# Summary
echo "📊 Test Summary"
echo "==============="
echo "   Total models: $MODEL_COUNT"
echo "   Successful: $SUCCESS_COUNT"
echo "   Failed: $FAIL_COUNT"
echo ""

if [ "$FAIL_COUNT" -eq 0 ]; then
    echo "   🎉 All tests passed!"
    exit 0
else
    echo "   ⚠️  Some tests failed. Check model deployment status."
    exit 1
fi

