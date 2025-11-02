# CheckMK Prometheus Service Definitions for vLLM on Ray Serve
# 
# This file defines PromQL queries that CheckMK will execute against Prometheus
# to create services for monitoring vLLM metrics.
#
# Reference: docs/vllm-ray-serve-guide.md Section 2.3.1 and Table 2.1
#
# Format: Each service definition follows the pattern:
# check_parameters["<service_name>"] = {
#     "promql_query": "<PromQL query>",
#     "service_name": "<display name>",
#     "metric_name": "<metric label>",
# }

# Critical vLLM Observability Metrics (Golden Signals)

# 1. Time to First Token (TTFT) - User-Perceived Latency
# Alert on p95 > 2s (as per guide recommendation)
check_parameters["vllm_ttft_p95"] = {
    "promql_query": "histogram_quantile(0.95, vllm:time_to_first_token_seconds{job=\"ray\"})",
    "service_name": "vLLM Time to First Token (p95)",
    "metric_name": "ttft_p95_seconds",
    "unit": "s",
    "levels": (2.0, 5.0),  # Warning at 2s, Critical at 5s
}

check_parameters["vllm_ttft_p50"] = {
    "promql_query": "histogram_quantile(0.50, vllm:time_to_first_token_seconds{job=\"ray\"})",
    "service_name": "vLLM Time to First Token (p50)",
    "metric_name": "ttft_p50_seconds",
    "unit": "s",
}

# 2. Time Per Output Token (TPOT) - Generation Speed
check_parameters["vllm_tpot_avg"] = {
    "promql_query": "avg(vllm:time_per_output_token_seconds{job=\"ray\"})",
    "service_name": "vLLM Time Per Output Token",
    "metric_name": "tpot_seconds",
    "unit": "s",
}

check_parameters["vllm_tpot_p95"] = {
    "promql_query": "histogram_quantile(0.95, vllm:time_per_output_token_seconds{job=\"ray\"})",
    "service_name": "vLLM Time Per Output Token (p95)",
    "metric_name": "tpot_p95_seconds",
    "unit": "s",
}

# 3. KV Cache Utilization - Primary Bottleneck
# Autoscale on > 0.8 (as per guide recommendation)
# This is the most critical metric for load and autoscaling
check_parameters["vllm_kv_cache_usage"] = {
    "promql_query": "avg(vllm:gpu_cache_usage_perc{job=\"ray\"}) * 100",
    "service_name": "vLLM KV Cache Utilization",
    "metric_name": "kv_cache_usage_percent",
    "unit": "%",
    "levels": (80.0, 95.0),  # Warning at 80%, Critical at 95%
}

# 4. Request States - Engine Load Indicators
check_parameters["vllm_requests_running"] = {
    "promql_query": "sum(vllm:num_requests_running{job=\"ray\"})",
    "service_name": "vLLM Requests Running",
    "metric_name": "requests_running",
    "unit": "count",
}

check_parameters["vllm_requests_waiting"] = {
    "promql_query": "sum(vllm:num_requests_waiting{job=\"ray\"})",
    "service_name": "vLLM Requests Waiting",
    "metric_name": "requests_waiting",
    "unit": "count",
    "levels": (1.0, 10.0),  # Warning if > 0 (saturated), Critical if > 10
}

# 5. Token Usage - Cost/Usage Analysis
check_parameters["vllm_prompt_tokens_total"] = {
    "promql_query": "sum(rate(vllm:prompt_tokens_total{job=\"ray\"}[5m]))",
    "service_name": "vLLM Prompt Tokens/sec",
    "metric_name": "prompt_tokens_per_second",
    "unit": "1/s",
}

check_parameters["vllm_generation_tokens_total"] = {
    "promql_query": "sum(rate(vllm:generation_tokens_total{job=\"ray\"}[5m]))",
    "service_name": "vLLM Generation Tokens/sec",
    "metric_name": "generation_tokens_per_second",
    "unit": "1/s",
}

# Ray Serve Metrics - Deployment Health

# 6. Processing Latency - End-to-End Latency
# Alert on p95 > 5s (as per guide recommendation)
check_parameters["ray_serve_latency_p95"] = {
    "promql_query": "histogram_quantile(0.95, serve_deployment_processing_latency_ms{job=\"ray\"} / 1000)",
    "service_name": "Ray Serve Processing Latency (p95)",
    "metric_name": "serve_latency_p95_seconds",
    "unit": "s",
    "levels": (5.0, 10.0),  # Warning at 5s, Critical at 10s
}

# 7. Request Throughput - RPS
check_parameters["ray_serve_requests_total"] = {
    "promql_query": "sum(rate(serve_num_router_requests_total{job=\"ray\"}[5m]))",
    "service_name": "Ray Serve Requests/sec",
    "metric_name": "serve_requests_per_second",
    "unit": "1/s",
}

# 8. Replica Management - Autoscaler Activity
check_parameters["ray_serve_replicas"] = {
    "promql_query": "sum(serve_num_deployment_replicas{job=\"ray\"})",
    "service_name": "Ray Serve Active Replicas",
    "metric_name": "serve_active_replicas",
    "unit": "count",
}

check_parameters["ray_serve_replica_starts"] = {
    "promql_query": "sum(rate(serve_deployment_replica_starts_total{job=\"ray\"}[5m]))",
    "service_name": "Ray Serve Replica Starts/sec",
    "metric_name": "replica_starts_per_second",
    "unit": "1/s",
    "comment": "Monitor for autoscaler activity/churn",
}

