"""
Model Manager for Multi-Model Deployment Support

This module handles parsing, managing, and tracking multiple LLM model configurations.
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class ModelConfig:
    """Configuration for a single model deployment."""
    model_id: str
    route_prefix: Optional[str] = None
    tensor_parallel_size: int = 4
    accelerator_type: str = "L4"
    min_replicas: int = 1
    max_replicas: int = 4
    target_ongoing_requests: int = 32
    max_ongoing_requests: int = 64
    max_num_batched_tokens: int = 8192
    max_model_len: int = 8192
    max_num_seqs: int = 64
    trust_remote_code: bool = True
    enable_prefix_caching: bool = True
    model_source: Optional[str] = None
    pipeline_parallel_size: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = asdict(self)
        return {k: v for k, v in result.items() if v is not None}


class ModelManager:
    """Manages multiple model configurations and their lifecycle."""
    
    def __init__(self):
        self.models: Dict[str, ModelConfig] = {}
        self.model_registry: Dict[str, Dict[str, Any]] = {}
    
    def add_model(self, config: ModelConfig):
        """Add a model configuration to the registry."""
        # Use route_prefix as key, or model_id if route_prefix not specified
        key = config.route_prefix or f"/v1/models/{config.model_id.split('/')[-1].lower()}"
        self.models[key] = config
        
        # Register model metadata
        self.model_registry[config.model_id] = {
            "id": config.model_id,
            "object": "model",
            "created": None,  # Could track creation time
            "owned_by": "ray-serve",
            "route_prefix": key,
            "config": config.to_dict()
        }
    
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """Get model configuration by model ID."""
        for config in self.models.values():
            if config.model_id == model_id:
                return config
        return None
    
    def get_all_models(self) -> List[Dict[str, Any]]:
        """Get metadata for all registered models."""
        return list(self.model_registry.values())
    
    def get_model_by_prefix(self, route_prefix: str) -> Optional[ModelConfig]:
        """Get model configuration by route prefix."""
        return self.models.get(route_prefix)
    
    def list_model_ids(self) -> List[str]:
        """List all model IDs."""
        return [config.model_id for config in self.models.values()]


def parse_models_config(env_key: str = "MODELS_CONFIG") -> List[ModelConfig]:
    """
    Parse MODELS_CONFIG environment variable (JSON format) or fall back to single MODEL_ID.
    
    Returns a list of ModelConfig objects.
    """
    models_config_str = os.getenv(env_key, "")
    
    # If MODELS_CONFIG is provided, parse it
    if models_config_str:
        try:
            models_data = json.loads(models_config_str)
            if not isinstance(models_data, list):
                raise ValueError("MODELS_CONFIG must be a JSON array")
            
            configs = []
            for model_data in models_data:
                config = ModelConfig(
                    model_id=model_data.get("model_id"),
                    route_prefix=model_data.get("route_prefix"),
                    tensor_parallel_size=model_data.get("tensor_parallel_size", 4),
                    accelerator_type=model_data.get("accelerator_type", "L4"),
                    min_replicas=model_data.get("min_replicas", 1),
                    max_replicas=model_data.get("max_replicas", 4),
                    target_ongoing_requests=model_data.get("target_ongoing_requests", 32),
                    max_ongoing_requests=model_data.get("max_ongoing_requests", 64),
                    max_num_batched_tokens=model_data.get("max_num_batched_tokens", 8192),
                    max_model_len=model_data.get("max_model_len", 8192),
                    max_num_seqs=model_data.get("max_num_seqs", 64),
                    trust_remote_code=model_data.get("trust_remote_code", True),
                    enable_prefix_caching=model_data.get("enable_prefix_caching", True),
                    model_source=model_data.get("model_source"),
                    pipeline_parallel_size=model_data.get("pipeline_parallel_size"),
                )
                if not config.model_id:
                    raise ValueError("model_id is required in MODELS_CONFIG")
                configs.append(config)
            
            return configs
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse MODELS_CONFIG as JSON: {e}")
    
    # Fall back to single MODEL_ID for backward compatibility
    model_id = os.getenv("MODEL_ID", "Qwen/Qwen2.5-32B-Instruct")
    
    # Map accelerator type
    accelerator_type_raw = os.getenv("ACCELERATOR_TYPE", "L4")
    accelerator_type_map = {
        "L40": "L4",
        "l40": "L4",
        "l4": "L4",
    }
    accelerator_type = accelerator_type_map.get(accelerator_type_raw, accelerator_type_raw)
    
    # Create single model config from environment variables
    config = ModelConfig(
        model_id=model_id,
        route_prefix=os.getenv("ROUTE_PREFIX", "/v1"),
        tensor_parallel_size=int(os.getenv("TENSOR_PARALLEL_SIZE", "4")),
        accelerator_type=accelerator_type,
        min_replicas=int(os.getenv("MIN_REPLICAS", "1")),
        max_replicas=int(os.getenv("MAX_REPLICAS", "4")),
        target_ongoing_requests=int(os.getenv("TARGET_ONGOING_REQUESTS", "32")),
        max_ongoing_requests=int(os.getenv("MAX_ONGOING_REQUESTS", "64")),
        max_num_batched_tokens=int(os.getenv("MAX_NUM_BATCHED_TOKENS", "8192")),
        max_model_len=int(os.getenv("MAX_MODEL_LEN", "8192")),
        max_num_seqs=int(os.getenv("MAX_NUM_SEQS", "64")),
        trust_remote_code=os.getenv("TRUST_REMOTE_CODE", "true").lower() in ('true', '1', 'yes', 'on'),
        enable_prefix_caching=os.getenv("ENABLE_PREFIX_CACHING", "true").lower() in ('true', '1', 'yes', 'on'),
        model_source=os.getenv("MODEL_SOURCE") or None,
    )
    
    return [config]

