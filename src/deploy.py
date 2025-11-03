#!/usr/bin/env python3
"""
vLLM + Ray Serve Deployment Script
Implements the LLMConfig pattern from vllm-ray-serve-guide.md
Supports both single model (backward compatible) and multi-model deployment.
"""

import os
import json
from typing import List
import ray
from ray import serve
from ray.serve.llm import LLMConfig, build_openai_app
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse

from models.model_manager import ModelManager, ModelConfig, parse_models_config
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


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


def create_llm_config_from_model_config(model_config: ModelConfig, hf_token: str = "") -> LLMConfig:
    """Create an LLMConfig from a ModelConfig object."""
    # Build model_loading_config
    model_loading_config = {
        'model_id': model_config.model_id
    }
    
    # Add model_source if provided
    if model_config.model_source:
        model_loading_config['model_source'] = model_config.model_source
    
    # Note: HuggingFace token is handled via environment variable (HUGGINGFACE_TOKEN)
    # LLMConfig's model_loading_config doesn't accept 'token' field directly
    # vLLM will automatically use HUGGINGFACE_TOKEN env var if needed for gated models
    
    # Map accelerator type (handle None/null)
    accelerator_type = None
    if model_config.accelerator_type:
        accelerator_type_map = {
            "L40": "L4",
            "l40": "L4",
            "l4": "L4",
        }
        accelerator_type = accelerator_type_map.get(model_config.accelerator_type, model_config.accelerator_type)
        
        # Supported accelerator types for Ray Serve LLMConfig
        supported_types = ["L4", "A100", "H100", "T4", "V100", "A10", "A10G"]
        
        if accelerator_type not in supported_types:
            print(f"WARNING: Accelerator type '{accelerator_type}' may not be supported.")
            print(f"Supported types: {', '.join(supported_types)}")
            print(f"Continuing without explicit accelerator_type...")
            accelerator_type = None  # Let Ray auto-detect
    
    # Build engine_kwargs
    engine_kwargs = {
        'tensor_parallel_size': model_config.tensor_parallel_size,
        'max_num_batched_tokens': model_config.max_num_batched_tokens,
        'max_model_len': model_config.max_model_len,
        'max_num_seqs': model_config.max_num_seqs,
        'trust_remote_code': model_config.trust_remote_code,
        'enable_prefix_caching': model_config.enable_prefix_caching,
        # Reduce GPU memory utilization to 0.35 to fit within available free memory
        # With only ~15.76 GiB free, we need very low utilization (0.35 = ~15.5 GiB requirement)
        'gpu_memory_utilization': 0.35,
    }
    
    # Add pipeline_parallel_size if specified
    if model_config.pipeline_parallel_size:
        engine_kwargs['pipeline_parallel_size'] = model_config.pipeline_parallel_size
    
    # Define LLMConfig
    # Build config dict, only adding accelerator_type if specified
    llm_config_params = {
        # 1. Model Loading Configuration
        'model_loading_config': model_loading_config,
        
        # 2. Deployment & Scaling Configuration
        'deployment_config': {
            'autoscaling_config': {
                'min_replicas': model_config.min_replicas,
                'max_replicas': model_config.max_replicas,
                'target_ongoing_requests': model_config.target_ongoing_requests,
            },
            'max_ongoing_requests': model_config.max_ongoing_requests,
        },
        
        # 4. vLLM Engine Keyword Arguments (kwargs)
        'engine_kwargs': engine_kwargs,
    }
    
    # 3. Ray Actor Resource Allocation (only if specified)
    if accelerator_type:
        llm_config_params['accelerator_type'] = accelerator_type
    
    llm_config = LLMConfig(**llm_config_params)
    
    return llm_config


def main():
    """Main deployment function."""
    print("Initializing vLLM deployment with Ray Serve...")
    
    # Initialize Ray with dashboard support
    # NOTE: Inside the container, Ray Dashboard always runs on port 8265
    # The host port mapping (RAY_DASHBOARD_PORT) is handled by Docker
    dashboard_port = 8265  # Container internal port (always 8265)
    host_dashboard_port = get_env_or_default("RAY_DASHBOARD_PORT", "8265", int)
    
    # Initialize Ray cluster first
    # IMPORTANT: When starting a NEW Ray cluster, RAY_ADDRESS should NOT be set
    # RAY_ADDRESS is only used when connecting to an EXISTING cluster
    # We'll temporarily unset it to ensure we start a fresh cluster
    ray_address_backup = os.environ.pop("RAY_ADDRESS", None)
    if ray_address_backup:
        print(f"Note: RAY_ADDRESS was set to '{ray_address_backup}', temporarily unsetting to start new cluster")
    
    try:
        # Check if Ray is already initialized
        if not ray.is_initialized():
            print(f"Initializing new Ray cluster with dashboard on port {dashboard_port}...")
            # Bind dashboard to 0.0.0.0 to make it accessible from outside the container
            # Configure Ray temp directory to avoid disk space issues
            import tempfile
            temp_dir = os.getenv("RAY_TEMP_DIR", "/tmp/ray")
            os.makedirs(temp_dir, exist_ok=True)
            
            ray.init(
                dashboard_port=dashboard_port,
                dashboard_host="0.0.0.0",  # Allow access from Docker network
                ignore_reinit_error=True,
                _temp_dir=temp_dir,  # Use configured temp directory
            )
            print(f"Ray cluster initialized with dashboard on port {dashboard_port}")
            # Wait a moment to ensure Ray is fully ready
            import time
            time.sleep(2)
        else:
            print("Ray is already initialized")
    except Exception as e:
        print(f"Warning: Could not explicitly initialize Ray: {e}")
        print("Ray will be auto-initialized by serve.run()")
    
    # Parse model configurations (supports both single and multi-model)
    try:
        model_configs = parse_models_config()
        print(f"Parsed {len(model_configs)} model configuration(s)")
    except Exception as e:
        print(f"ERROR: Failed to parse model configurations: {e}")
        raise
    
    # Initialize model manager
    model_manager = ModelManager()
    
    # HuggingFace token (from secrets)
    hf_token = os.getenv("HUGGINGFACE_TOKEN", "")
    
    # Create LLMConfig objects for each model
    llm_configs: List[LLMConfig] = []
    
    for model_config in model_configs:
        print(f"\nConfiguring model: {model_config.model_id}")
        print(f"  Route Prefix: {model_config.route_prefix or 'default (/v1)'}")
        print(f"  Tensor Parallel Size: {model_config.tensor_parallel_size}")
        print(f"  Accelerator Type: {model_config.accelerator_type}")
        print(f"  Replicas: {model_config.min_replicas} - {model_config.max_replicas}")
        
        # Register model in manager
        model_manager.add_model(model_config)
        
        # Create LLMConfig
        llm_config = create_llm_config_from_model_config(model_config, hf_token)
        llm_configs.append(llm_config)
    
    print(f"\nDeploying {len(llm_configs)} model(s) with Ray Serve...")
    
    # Determine route prefix (use first model's prefix or default)
    route_prefix = model_configs[0].route_prefix if model_configs[0].route_prefix else "/v1"
    
    # Ensure Ray is initialized before calling build_openai_app
    if not ray.is_initialized():
        print("Error: Ray should be initialized at this point")
        raise RuntimeError("Ray cluster must be initialized before calling build_openai_app")
    
    # build_openai_app translates LLMConfigs into a deployable FastAPI application
    # It can handle multiple models automatically and already includes /v1/models
    # IMPORTANT: RAY_ADDRESS should already be unset from above, but ensure it stays unset
    # so build_openai_app uses the current initialized Ray cluster
    print("Building OpenAI app with LLM configs...")
    # Double-check RAY_ADDRESS is not set (it should already be unset from initialization)
    if "RAY_ADDRESS" in os.environ:
        print("Warning: RAY_ADDRESS still set, unsetting for build_openai_app...")
        os.environ.pop("RAY_ADDRESS", None)
    
    llm_app = build_openai_app({"llm_configs": llm_configs})
    
    # After build_openai_app succeeds, we can restore RAY_ADDRESS if it was originally set
    # (but we won't restore it since we're running our own cluster)
    
    # Create a custom app that wraps the OpenAI app and adds our models endpoint
    # Since build_openai_app already provides /v1/models, we'll deploy it as-is
    # and rely on it listing models from llm_configs
    # For custom model metadata, we can enhance later
    
    # Deploy the OpenAI app which handles all routes including /v1/models
    print(f"\nDeploying OpenAI app with route prefix: {route_prefix}")
    print(f"Note: /v1/models endpoint is provided by build_openai_app")
    print(f"      It will list all models from llm_configs")
    
    serve.run(llm_app, route_prefix=route_prefix, name="multi_model_serve")
    
    print(f"\nDeployment complete!")
    print(f"Ray Dashboard available at http://localhost:{host_dashboard_port} (from host)")
    print(f"Available models endpoint: {route_prefix}/models")
    print(f"Models deployed: {', '.join(model_manager.list_model_ids())}")
    print("\nService will continue running...")


if __name__ == "__main__":
    main()

