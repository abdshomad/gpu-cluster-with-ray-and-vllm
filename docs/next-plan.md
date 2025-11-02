# Next Phase Implementation Plan - GPU Cluster Platform Enhancements

## Overview
This document outlines the next phase of development for the GPU Cluster Platform, with **high priority on multi-model and multi-cluster support** to enable users to deploy multiple models and scale across GPU clusters. Additional focus areas include security (PII masking), advanced features, and production hardening based on the vllm-ray-serve-guide.md.

## Plan Format
Each plan item follows the format:
- **ID**: 2 characters + 3 digits (e.g., AB001)
- **Status**: pending | in_progress | completed | cancelled
- **Implemented Date**: YYYY-MM-DD (only when status is completed)

---

## Part 1: High-Priority Infrastructure (Multi-Model & Multi-Cluster Support)

### AA001: Implement Multi-Model Deployment Support
**Status**: pending
**Implemented Date**: 

Enable deployment and management of multiple LLM models simultaneously:
- Extend `deploy.py` to accept multiple MODEL_IDs via configuration
- Configure separate route prefixes per model (e.g., `/v1/models/{model_id}`)
- Support OpenAI-style model selection in API requests
- Implement dynamic model loading/unloading without service restart
- Allow different models with different GPU allocations and autoscaling configs
- Add model metadata endpoint (list all available models)

**Implementation Details**:
- Create `src/models/model_manager.py` for model lifecycle management
- Update `src/deploy.py` to parse multiple MODEL_IDs from environment (comma-separated or JSON)
- Implement model registry to track available models and their configs
- Use multiple LLMConfig objects in `build_openai_app`
- Add model selection middleware to route requests to correct model deployment
- Implement `/v1/models` endpoint returning available models
- Support per-model configuration (tensor_parallel_size, accelerator_type, etc.)
- Add environment variable `MODELS_CONFIG` (JSON) for multi-model setup

**Files to Create/Modify**:
- `src/models/__init__.py`
- `src/models/model_manager.py` (model registry and lifecycle)
- `src/models/model_router.py` (request routing logic)
- `src/deploy.py` (multi-model deployment logic)
- `.env` (add MODELS_CONFIG with example JSON)
- `docs/guides/operator-guides.md` (multi-model deployment guide)

**Example Configuration**:
```json
MODELS_CONFIG='[
  {
    "model_id": "Qwen/Qwen2.5-32B-Instruct",
    "route_prefix": "/v1/models/qwen",
    "tensor_parallel_size": 4,
    "accelerator_type": "L4",
    "min_replicas": 1,
    "max_replicas": 4
  },
  {
    "model_id": "meta-llama/Llama-3-8B-Instruct",
    "route_prefix": "/v1/models/llama",
    "tensor_parallel_size": 2,
    "accelerator_type": "L4",
    "min_replicas": 1,
    "max_replicas": 2
  }
]'
```

---

### AA002: Implement Multi-Node/Multi-Cluster GPU Support
**Status**: pending
**Implemented Date**: 

Enable deployment across multiple GPU nodes and clusters:
- Support Ray cluster connection to external Ray head node
- Implement worker node discovery and management
- Configure model distribution across multiple nodes (pipeline parallelism)
- Add cluster health monitoring and node failure handling
- Support heterogeneous GPU clusters (mixed GPU types)
- Implement automatic load balancing across nodes

**Implementation Details**:
- Add `RAY_HEAD_ADDRESS` environment variable for connecting to existing cluster
- Update `src/deploy.py` to support cluster mode vs. standalone mode
- Implement cluster discovery and node registration
- Add pipeline parallelism configuration with automatic node assignment
- Create `src/cluster/cluster_manager.py` for cluster operations
- Add cluster status endpoint showing all nodes and their GPU resources
- Implement node health checks and automatic reconnection
- Support dynamic worker node addition/removal
- Add GPU resource reservation per model across nodes

**Files to Create/Modify**:
- `src/cluster/__init__.py`
- `src/cluster/cluster_manager.py` (cluster connection and management)
- `src/cluster/node_discovery.py` (worker node discovery)
- `src/deploy.py` (add cluster mode support)
- `.env` (add RAY_HEAD_ADDRESS, RAY_CLUSTER_MODE, etc.)
- `docker/docker-compose.yml` (add support for multi-node deployment)
- `docs/guides/operator-guides.md` (multi-node cluster setup guide)

**Configuration Variables**:
- `RAY_CLUSTER_MODE`: "standalone" | "cluster" (default: standalone)
- `RAY_HEAD_ADDRESS`: Address of Ray head node (e.g., "ray://head-node:10001")
- `PIPELINE_PARALLEL_SIZE`: Number of pipeline stages (requires multiple nodes)
- `ENABLE_NODE_AUTODISCOVERY`: Auto-discover worker nodes (default: true)

---

### AA003: Implement Model Routing and Load Balancing
**Status**: pending
**Implemented Date**: 

Create intelligent routing layer for multiple models and clusters:
- Implement round-robin and least-connections load balancing per model
- Add model-specific request queuing and throttling
- Support model affinity (route requests based on user/session)
- Implement request distribution across model replicas
- Add circuit breaker pattern for failed model deployments
- Create unified API gateway supporting all models and clusters

**Implementation Details**:
- Create `src/routing/model_router.py` with load balancing algorithms
- Implement health-based routing (skip unhealthy replicas)
- Add request queuing when all replicas are busy
- Support sticky sessions for conversation continuity
- Implement rate limiting per model (not just per IP)
- Add metrics for routing decisions (latency, errors, throughput)
- Create admin API for manual model routing control

**Files to Create/Modify**:
- `src/routing/__init__.py`
- `src/routing/model_router.py` (routing logic)
- `src/routing/load_balancer.py` (load balancing algorithms)
- `src/routing/circuit_breaker.py` (failure handling)
- Update Nginx config or create Ray Serve routing service
- `docs/guides/operator-guides.md` (routing configuration)

---

### AA004: Add GPU Resource Management and Allocation
**Status**: pending
**Implemented Date**: 

Implement intelligent GPU resource allocation across models and clusters:
- Track GPU utilization per model deployment
- Implement GPU reservation and quota system
- Add resource scheduling (which model gets GPUs when)
- Support GPU sharing (time-slicing) for smaller models
- Add resource pool management (dedicated pools per model/cluster)
- Implement GPU monitoring and alerting for resource exhaustion

**Implementation Details**:
- Create `src/resources/gpu_manager.py` for GPU tracking
- Implement resource reservation API
- Add GPU quota limits per model or user
- Create resource pool configuration system
- Integrate with Ray's resource management
- Add Prometheus metrics for GPU allocation
- Create Grafana dashboard for GPU resource tracking
- Implement automatic scaling based on GPU availability

**Files to Create/Modify**:
- `src/resources/__init__.py`
- `src/resources/gpu_manager.py` (GPU resource tracking)
- `src/resources/resource_scheduler.py` (allocation logic)
- `docker/grafana/provisioning/dashboards/gpu_resources_dashboard.json`
- `.env` (add GPU quota and pool configuration)
- `docs/guides/operator-guides.md` (resource management guide)

---

## Part 2: PII Security Implementation (vllm-ray-serve-guide.md Section 3)

### AB001: Implement Presidio Core Libraries
**Status**: pending
**Implemented Date**: 

Install and configure Microsoft Presidio core libraries in the Ray Serve deployment:
- Add `presidio-analyzer` and `presidio-anonymizer` to `requirements.txt`
- Install spaCy language model (`en_core_web_lg` or similar) for PII detection
- Create initialization utilities for AnalyzerEngine and AnonymizerEngine
- Configure default anonymization operators (replace, mask patterns)

**Implementation Details**:
- Update `requirements.txt` with Presidio packages
- Create `src/pii/__init__.py` module structure
- Implement `src/pii/presidio_setup.py` for engine initialization
- Add environment variables for PII configuration (entities to detect, operators)

**Files to Create/Modify**:
- `requirements.txt` (add presidio packages)
- `src/pii/__init__.py`
- `src/pii/presidio_setup.py`
- `.env` (add PII configuration variables)

---

### AB002: Implement PII Service Deployment (Ray Serve Composition)
**Status**: pending
**Implemented Date**: 

Create the PIIService deployment using Ray Serve Deployment Composition pattern (guide Section 3.3):
- Implement `PIIService` class as a Ray Serve deployment
- Use `DeploymentHandle` to inject vLLM service dependency
- Create `anonymize_prompts()` method to process OpenAI API request messages
- Create `anonymize_response()` method to process LLM output
- Implement async `__call__()` method for request handling

**Implementation Details**:
- Create `src/pii/pii_service.py` with PIIService class
- Parse OpenAI API request format (`messages` array structure)
- Apply Presidio analyzer to each message content
- Forward sanitized requests to vLLM deployment via handle
- Process streaming and non-streaming responses

**Files to Create/Modify**:
- `src/pii/pii_service.py`
- Update `src/deploy.py` to support PII service composition mode

---

### AB003: Integrate PII Service with vLLM Deployment
**Status**: pending
**Implemented Date**: 

Modify deployment script to support optional PII service composition:
- Add environment variable `ENABLE_PII_MASKING` (default: false)
- When enabled, wrap vLLM deployment with PIIService as ingress
- Configure independent autoscaling for PII service (CPU-based)
- Set route prefix to PII service when enabled

**Implementation Details**:
- Update `src/deploy.py` to detect PII masking flag
- Create vLLM deployment with named handle when PII enabled
- Bind PIIService with injected vLLM handle
- Configure separate autoscaling configs (PII: CPU, vLLM: GPU)
- Document environment variable in `.env.example`

**Files to Create/Modify**:
- `src/deploy.py` (add composition logic)
- `.env` (add ENABLE_PII_MASKING configuration)
- Update documentation

---

### AB004: Implement Bookend Pattern with Deanonymization
**Status**: pending
**Implemented Date**: 

Implement the advanced "bookend" pattern for PII deanonymization (guide Section 3.4):
- Use Presidio's encrypt operator or token-based replacement
- Store PII mapping (original → token) in request-scoped dictionary or Redis
- Perform reverse substitution on LLM response
- Support streaming response deanonymization

**Implementation Details**:
- Implement token generation system (e.g., `PII-{uuid}`)
- Use Presidio's `DeanonymizeEngine` or custom mapping logic
- Handle both streaming and non-streaming response formats
- Consider Redis integration for distributed deployments
- Add performance monitoring for deanonymization latency

**Files to Create/Modify**:
- `src/pii/bookend.py` (deanonymization logic)
- `src/pii/pii_service.py` (integrate bookend pattern)
- Optional: `src/pii/redis_store.py` (for distributed token mapping)

---

### AB005: Add PII Service Performance Monitoring
**Status**: pending
**Implemented Date**: 

Instrument PII service with observability:
- Track PII scanning latency metrics
- Monitor PII detection rates (entities found per request)
- Track deanonymization performance
- Add custom Ray Serve metrics for PII service
- Create Grafana dashboard panels for PII metrics

**Implementation Details**:
- Add Prometheus metrics to PIIService
- Track histogram for `pii_scan_latency_seconds`
- Track counter for `pii_entities_detected_total` by entity type
- Add gauge for `pii_service_queue_depth`
- Create `docker/grafana/provisioning/dashboards/pii_dashboard.json`

**Files to Create/Modify**:
- `src/pii/pii_service.py` (add metrics)
- `docker/grafana/provisioning/dashboards/pii_dashboard.json`

---

## Part 3: Advanced Deployment Features

### AB006: Implement Pipeline Parallelism Support
**Status**: pending
**Implemented Date**: 

Add configuration support for multi-node pipeline parallelism:
- Add `PIPELINE_PARALLEL_SIZE` environment variable (per model in multi-model setup)
- Update `deploy.py` to set `pipeline_parallel_size` in engine_kwargs when > 1
- Document multi-node setup requirements
- Add validation for TP and PP size combinations
- Integrate with AA002 (Multi-Node Support) for automatic node assignment

**Implementation Details**:
- Update `src/deploy.py` LLMConfig to support pipeline_parallel_size per model
- Add environment variable parsing (supports per-model config in MODELS_CONFIG)
- Add validation logic (PP requires multi-node cluster, validate node count)
- Integrate with cluster manager to assign pipeline stages to nodes
- Update documentation with multi-node deployment guide

**Files to Create/Modify**:
- `src/deploy.py` (add PP support, integrate with AA002)
- `.env` (add PIPELINE_PARALLEL_SIZE in MODELS_CONFIG)
- `docs/guides/operator-guides.md` (multi-node setup with pipeline parallelism)

**Note**: This plan works closely with AA002 (Multi-Node Support). Pipeline parallelism requires multiple nodes to be configured first.

---

### AB007: Add SSL/TLS Termination in Nginx
**Status**: pending
**Implemented Date**: 

Implement SSL/TLS termination at Nginx layer:
- Add SSL certificate volume mounting support
- Configure Nginx with SSL server block on port 443
- Support Let's Encrypt certificates (via environment variables)
- Implement HTTP to HTTPS redirect
- Add SSL configuration via environment variables

**Implementation Details**:
- Update `docker/nginx/nginx.conf` with SSL configuration
- Add certificate path environment variables
- Configure SSL ciphers and protocols
- Add HTTP to HTTPS redirect rule
- Document certificate setup process

**Files to Create/Modify**:
- `docker/nginx/nginx.conf` (add SSL server block)
- `docker/docker-compose.yml` (add certificate volume)
- `.env` (add SSL certificate paths)
- `docs/guides/admin-guides.md` (SSL setup)

---

### AB008: Implement Datadog Integration
**Status**: pending
**Implemented Date**: 

Add Datadog Agent integration following guide Section 2.3.2:
- Create Datadog Agent container in docker-compose
- Configure OpenMetrics endpoint scraping
- Set up pod annotations pattern (if moving to Kubernetes)
- Add Datadog-specific metric tags

**Implementation Details**:
- Add `datadog-agent` service to docker-compose
- Create `docker/datadog/conf.yaml` with Ray integration config
- Configure automatic service discovery for Ray metrics
- Add environment variables for Datadog API key and tags
- Document integration setup

**Files to Create/Modify**:
- `docker/docker-compose.yml` (add Datadog service)
- `docker/datadog/conf.yaml`
- `.secrets` (add DATADOG_API_KEY)
- `docs/prometheus-ray-integration.md` (add Datadog section)

---

## Part 4: Production Hardening

### AB009: Implement Request Rate Limiting
**Status**: pending
**Implemented Date**: 

Add rate limiting at Nginx layer to prevent abuse:
- Configure Nginx rate limiting zones
- Set per-IP request limits (configurable via environment)
- Add rate limit headers to responses
- Implement different limits for API vs dashboard access

**Implementation Details**:
- Update `docker/nginx/nginx.conf` with `limit_req_zone` and `limit_req`
- Add `NGINX_RATE_LIMIT_RPM` and `NGINX_RATE_LIMIT_BURST` env vars
- Configure separate limits for `/v1` API endpoint
- Add rate limit status endpoint
- Document rate limiting behavior

**Files to Create/Modify**:
- `docker/nginx/nginx.conf` (add rate limiting)
- `.env` (add rate limit configuration)
- `docs/guides/admin-guides.md` (rate limiting docs)

---

### AB010: Add Authentication/Authorization Layer
**Status**: pending
**Implemented Date**: 

Implement API authentication for production deployments:
- Add API key authentication middleware
- Support multiple authentication methods (API key, JWT, OAuth2)
- Configure role-based access control (RBAC)
- Add authentication bypass for health checks

**Implementation Details**:
- Create `src/auth/` module with authentication handlers
- Implement API key validation middleware
- Add `AUTH_ENABLED`, `API_KEYS` environment variables
- Update Nginx or Ray Serve layer for auth
- Create authentication documentation

**Files to Create/Modify**:
- `src/auth/__init__.py`
- `src/auth/api_key_auth.py`
- `.secrets` (add API_KEYS)
- `.env` (add AUTH_ENABLED)
- `docs/guides/admin-guides.md` (auth setup)

---

### AB011: Implement Request Logging and Audit Trail
**Status**: pending
**Implemented Date**: 

Add comprehensive request logging for compliance:
- Log all API requests with sanitized PII (if enabled)
- Implement structured logging (JSON format)
- Add request/response correlation IDs
- Configure log rotation and retention
- Export logs to external system (optional: ELK stack)

**Implementation Details**:
- Configure Python logging with structured JSON formatter
- Add correlation ID middleware
- Sanitize logs when PII masking is enabled
- Configure log file rotation via logrotate or Python
- Optional: Add Fluentd/Fluent Bit sidecar for log forwarding

**Files to Create/Modify**:
- `src/logging_config.py`
- `src/middleware/correlation_id.py`
- `docker/docker-compose.yml` (add logging volume)
- `docs/guides/admin-guides.md` (logging config)

---

### AB012: Add Health Check Improvements
**Status**: pending
**Implemented Date**: 

Enhance health check endpoints for better orchestration:
- Add readiness probe endpoint (checks model loaded)
- Add liveness probe endpoint (checks Ray Serve responding)
- Implement startup probe for slow model loading
- Add detailed health status JSON endpoint
- Include dependency health (Prometheus, Grafana connectivity)

**Implementation Details**:
- Create `src/health.py` with comprehensive health checks
- Add `/health/ready`, `/health/live`, `/health/startup` endpoints
- Check vLLM model status, Ray cluster health
- Add dependency connectivity checks
- Update docker-compose healthcheck configs

**Files to Create/Modify**:
- `src/health.py`
- `src/deploy.py` (add health endpoints)
- `docker/docker-compose.yml` (update healthchecks)
- `docker/nginx/nginx.conf` (add health routes)

---

## Part 5: Developer Experience

### AB013: Create Development/Testing Scripts
**Status**: pending
**Implemented Date**: 

Add developer tooling and test scripts:
- Create script to test OpenAI API compatibility
- Add load testing script with varying request patterns
- Create script to validate PII detection accuracy
- Add deployment validation script (pre-flight checks)
- Create benchmark script for performance testing

**Implementation Details**:
- Create `scripts/test_api.py` for API testing
- Create `scripts/load_test.py` using locust or similar
- Create `scripts/test_pii.py` for PII validation
- Create `scripts/validate_deployment.py` for pre-flight checks
- Document script usage in README

**Files to Create/Modify**:
- `scripts/test_api.py`
- `scripts/load_test.py`
- `scripts/test_pii.py`
- `scripts/validate_deployment.py`
- `README.md` (add scripts section)

---

### AB014: Add Comprehensive Environment Configuration Templates
**Status**: pending
**Implemented Date**: 

Create detailed configuration templates and validation:
- Create `.env.example` with all possible variables documented
- Create `.secrets.example` template (without actual secrets)
- Add configuration validation script
- Document all environment variables with defaults
- Add configuration schema/documentation generator

**Implementation Details**:
- Create `.env.example` with comments explaining each variable
- Create `.secrets.example` with placeholders
- Create `scripts/validate_config.py` for validation
- Update `docs/guides/configurator-guides.md` with all variables
- Add startup config validation in `deploy.py`

**Files to Create/Modify**:
- `.env.example`
- `.secrets.example`
- `scripts/validate_config.py`
- `docs/guides/configurator-guides.md`

---

### AB015: (Merged into AA001)
**Status**: cancelled
**Implemented Date**: 

This plan has been merged into AA001 (Implement Multi-Model Deployment Support) which provides more comprehensive multi-model functionality.

---

## Part 6: Documentation and Guides

### AB016: Create PII Implementation Guide
**Status**: pending
**Implemented Date**: 

Document the PII masking implementation:
- Write step-by-step setup guide for Presidio
- Document bookend pattern architecture
- Create troubleshooting guide for PII service issues
- Add performance tuning recommendations
- Include example API requests with PII masking

**Implementation Details**:
- Create `docs/guides/pii-implementation-guide.md`
- Include architecture diagrams (ASCII or images)
- Document Presidio configuration options
- Add common issues and solutions
- Include performance benchmarks and recommendations

**Files to Create/Modify**:
- `docs/guides/pii-implementation-guide.md`
- Update `README.md` with PII section

---

### AB017: Create Production Deployment Checklist
**Status**: pending
**Implemented Date**: 

Create comprehensive production readiness checklist:
- Security checklist (auth, SSL, secrets management)
- Performance checklist (monitoring, autoscaling, resource limits)
- Compliance checklist (logging, PII handling, audit trail)
- Disaster recovery checklist (backups, failover)
- Monitoring and alerting checklist

**Implementation Details**:
- Create `docs/guides/production-checklist.md`
- Include checkboxes for each item
- Link to relevant configuration guides
- Add severity ratings (critical, important, optional)
- Include validation commands/scripts

**Files to Create/Modify**:
- `docs/guides/production-checklist.md`
- Update main README with checklist link

---

## Summary

**Total Plans**: 20 (4 new high-priority plans added)
**Pending**: 20
**In Progress**: 0
**Completed**: 0
**Cancelled**: 1 (AB015 merged into AA001)

**Priority Focus Areas**:
1. **HIGH PRIORITY - Infrastructure (AA001-AA004)**: Multi-model and multi-cluster support - critical for scalability
2. **Security (AB001-AB005)**: PII masking is critical for production compliance
3. **Production Hardening (AB009-AB012)**: Essential for real-world deployments
4. **Advanced Features (AB006-AB008)**: Enable scaling and enterprise integration
5. **Developer Experience (AB013-AB014)**: Improve maintainability and testing
6. **Documentation (AB016-AB017)**: Ensure knowledge transfer and operations

**New High-Priority Plans**:
- **AA001**: Multi-Model Deployment Support - Users can deploy and manage multiple models simultaneously
- **AA002**: Multi-Node/Multi-Cluster GPU Support - Support for distributed deployments across multiple GPU nodes
- **AA003**: Model Routing and Load Balancing - Intelligent request routing across models and clusters
- **AA004**: GPU Resource Management - Track and allocate GPU resources across models and clusters

