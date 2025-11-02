#!/usr/bin/env python3
"""
vLLM + Ray Serve Deployment Script
Implements the LLMConfig pattern from vllm-ray-serve-guide.md
"""

import os
from ray import serve
from ray.serve.llm import LLMConfig, build_openai_app


def get_env_or_default(key: str, default: str, type_cast=str):
    """Get environment variable or return default with type casting."""
    value = os.getenv(key, default)
    if type_cast == int:
        return int(value)
    elif type_cast == float:
        return float(value)
    elif type_cast == bool:
        return value.lower() in ('true', '1', 'yes', 'on')
    return value


def main():
    """Main deployment function."""
    print("Initializing vLLM deployment with Ray Serve...")
    
    # Read configuration from environment variables
    # Model Configuration
    model_id = get_env_or_default("MODEL_ID", "Qwen/Qwen2.5-32B-Instruct")
    
    # Deployment & Scaling Configuration
    min_replicas = get_env_or_default("MIN_REPLICAS", "1", int)
    max_replicas = get_env_or_default("MAX_REPLICAS", "4", int)
    target_ongoing_requests = get_env_or_default("TARGET_ONGOING_REQUESTS", "32", int)
    max_ongoing_requests = get_env_or_default("MAX_ONGOING_REQUESTS", "64", int)
    num_replicas = get_env_or_default("NUM_REPLICAS", "1", int)
    
    # GPU Configuration
    accelerator_type = get_env_or_default("ACCELERATOR_TYPE", "L4")
    tensor_parallel_size = get_env_or_default("TENSOR_PARALLEL_SIZE", "4", int)
    
    # vLLM Engine Configuration
    max_num_batched_tokens = get_env_or_default("MAX_NUM_BATCHED_TOKENS", "8192", int)
    max_model_len = get_env_or_default("MAX_MODEL_LEN", "8192", int)
    max_num_seqs = get_env_or_default("MAX_NUM_SEQS", "64", int)
    trust_remote_code = get_env_or_default("TRUST_REMOTE_CODE", "true", bool)
    enable_prefix_caching = get_env_or_default("ENABLE_PREFIX_CACHING", "true", bool)
    
    # Optional: Model source for pre-downloaded models
    model_source = get_env_or_default("MODEL_SOURCE", "")
    
    # Port configuration
    route_prefix = get_env_or_default("ROUTE_PREFIX", "/v1")
    
    # HuggingFace token (from secrets)
    hf_token = os.getenv("HUGGINGFACE_TOKEN", "")
    
    print(f"Model ID: {model_id}")
    print(f"Tensor Parallel Size: {tensor_parallel_size}")
    print(f"Accelerator Type: {accelerator_type}")
    print(f"Replicas: {min_replicas} - {max_replicas}")
    
    # Build model_loading_config
    model_loading_config = {
        'model_id': model_id
    }
    
    # Add model_source if provided
    if model_source:
        model_loading_config['model_source'] = model_source
    
    # Add HuggingFace token if provided
    if hf_token:
        model_loading_config['token'] = hf_token
    
    # Define LLMConfig - the single point of control
    llm_config = LLMConfig(
        # 1. Model Loading Configuration
        model_loading_config=model_loading_config,
        
        # 2. Deployment & Scaling Configuration
        deployment_config={
            'autoscaling_config': {
                'min_replicas': min_replicas,
                'max_replicas': max_replicas,
                'target_ongoing_requests': target_ongoing_requests,
            },
            'max_ongoing_requests': max_ongoing_requests,
        },
        
        # 3. Ray Actor Resource Allocation
        accelerator_type=accelerator_type,
        
        # 4. vLLM Engine Keyword Arguments (kwargs)
        engine_kwargs={
            # Distribute the model across GPUs
            'tensor_parallel_size': tensor_parallel_size,
            
            # vLLM performance tuning
            'max_num_batched_tokens': max_num_batched_tokens,
            'max_model_len': max_model_len,
            'max_num_seqs': max_num_seqs,
            'trust_remote_code': trust_remote_code,
            'enable_prefix_caching': enable_prefix_caching,
        },
    )
    
    # build_openai_app translates the LLMConfig into a deployable FastAPI application
    llm_app = build_openai_app({"llm_configs": [llm_config]})
    
    # serve.run deploys the application to the Ray cluster
    # and exposes it at the specified route prefix
    print(f"Deploying to Ray Serve with route prefix: {route_prefix}")
    serve.run(llm_app, route_prefix=route_prefix)


if __name__ == "__main__":
    main()

