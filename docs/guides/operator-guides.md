# Operator Guide - GPU Cluster Platform

This guide is for operators responsible for monitoring, maintaining, and troubleshooting the GPU Cluster Platform in production.

## Table of Contents

1. [Monitoring Overview](#monitoring-overview)
2. [Ray Dashboard](#ray-dashboard)
3. [Prometheus Metrics](#prometheus-metrics)
4. [Grafana Dashboards](#grafana-dashboards)
5. [Key Metrics](#key-metrics)
6. [Alerting](#alerting)
7. [Log Management](#log-management)
8. [Performance Monitoring](#performance-monitoring)
9. [Health Checks](#health-checks)
10. [Incident Response](#incident-response)
11. [Capacity Planning](#capacity-planning)
12. [Troubleshooting Procedures](#troubleshooting-procedures)

---

## Monitoring Overview

The GPU Cluster Platform provides multiple monitoring interfaces:

- **Ray Dashboard**: Real-time cluster and deployment status
- **Prometheus**: Time-series metrics collection
- **Grafana**: Visualization and alerting dashboards
- **Container Logs**: Application and service logs

### Access Points

- **Ray Dashboard**: `http://localhost:{RAY_DASHBOARD_PORT}` (default: `18265`)
- **Prometheus**: `http://localhost:19090`
- **Grafana**: `http://localhost:13000`
- **Nginx Proxy**: `http://localhost:{NGINX_HTTP_PORT}/dashboard` (Ray Dashboard via proxy)

---

## Ray Dashboard

### Accessing the Dashboard

```bash
# Direct access
http://localhost:18265

# Via Nginx proxy (if configured)
http://localhost:18080/dashboard
```

### Key Views

1. **Overview**: Cluster status, node count, resource usage
2. **Actors**: Ray actors and their status
3. **Jobs**: Running jobs and their progress
4. **Metrics**: Built-in metrics visualization
5. **Serve**: Ray Serve deployments and replicas
6. **Logs**: Real-time log viewing

### Monitoring Serve Deployments

Navigate to **Serve** tab to view:
- Deployment status and health
- Number of replicas (current vs. configured)
- Request throughput
- Autoscaling activity
- Replica health

### Using the Log Viewer

1. Navigate to **Logs** tab
2. Select component (serve, actor, etc.)
3. Filter by severity (INFO, WARNING, ERROR)
4. Search logs in real-time

---

## Prometheus Metrics

### Accessing Prometheus

```bash
# Web UI
http://localhost:19090

# API endpoint
http://localhost:19090/api/v1/query
```

### Service Discovery

Ray automatically generates a service discovery file at `/tmp/ray/prom_metrics_service_discovery.json`. Prometheus uses this to discover all Ray nodes.

**Verify Service Discovery**:
```bash
# Check service discovery file
docker exec gpu-cluster-prometheus cat /tmp/ray/prom_metrics_service_discovery.json

# Verify targets are UP
curl http://localhost:19090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="ray")'
```

### Querying Metrics

#### Ray Core Metrics

```promql
# Cluster active nodes
ray_cluster_active_nodes

# CPU usage by component
ray_component_cpu_percentage

# Memory usage
ray_component_mem_shared_bytes
```

#### Ray Serve Metrics

```promql
# Total requests
ray_serve_num_router_requests_total

# Current replicas
ray_serve_num_deployment_replicas

# Processing latency
serve_deployment_processing_latency_ms

# Replica starts (autoscaling activity)
ray_serve_deployment_replica_starts_total
```

#### vLLM Metrics

```promql
# Time to first token (TTFT)
vllm:time_to_first_token_seconds

# Time per output token (TPOT)
vllm:time_per_output_token_seconds

# KV cache utilization (CRITICAL)
vllm:gpu_cache_usage_perc

# Request states
vllm:num_requests_running
vllm:num_requests_waiting

# Token counts
vllm:prompt_tokens_total
vllm:generation_tokens_total
```

### Useful Queries

```bash
# Request rate (requests per second)
rate(ray_serve_num_router_requests_total[5m])

# Average latency (p95)
histogram_quantile(0.95, serve_deployment_processing_latency_ms)

# KV cache utilization (average across replicas)
avg(vllm:gpu_cache_usage_perc)

# Waiting requests (alert if > 0)
vllm:num_requests_waiting
```

---

## Grafana Dashboards

### Accessing Grafana

```bash
# Web UI
http://localhost:13000

# Default credentials
Username: admin
Password: admin (change on first login)
```

### Pre-configured Dashboards

The platform includes pre-configured dashboards:

1. **Ray Serve Dashboard**: `http://localhost:13000/d/rayServeDashboard`
   - Deployment metrics
   - Request throughput
   - Latency percentiles
   - Replica status

2. **Ray Serve Deployment Dashboard**: Deployment-specific metrics

3. **Default Grafana Dashboard**: General system metrics

### Dashboard Access

**Via Grafana UI**:
1. Login to Grafana
2. Navigate to **Dashboards**
3. Browse available dashboards

**Direct URL**:
```
http://localhost:13000/d/rayServeDashboard
```

### Creating Custom Dashboards

1. Go to **Dashboards** → **New Dashboard**
2. Add panels with Prometheus queries
3. Configure alerts (optional)
4. Save dashboard

**Example Panel** (KV Cache Utilization):
```promql
avg(vllm:gpu_cache_usage_perc) * 100
```

---

## Key Metrics

### Golden Signals

Monitor these four signals for service health:

#### 1. Latency

**Time to First Token (TTFT)**
```promql
# Average TTFT
avg(vllm:time_to_first_token_seconds)

# P95 TTFT
histogram_quantile(0.95, vllm:time_to_first_token_seconds)

# Alert threshold: P95 > 2 seconds
```

**Processing Latency**
```promql
# End-to-end latency
histogram_quantile(0.95, serve_deployment_processing_latency_ms)
```

#### 2. Traffic

**Request Rate**
```promql
# Requests per second
rate(ray_serve_num_router_requests_total[5m])
```

**Concurrent Requests**
```promql
# Running requests
vllm:num_requests_running

# Waiting requests
vllm:num_requests_waiting
```

#### 3. Errors

```promql
# Error rate (if available)
rate(ray_serve_num_router_requests_errors_total[5m])
```

#### 4. Saturation

**KV Cache Utilization** (Most Critical)
```promql
# Average KV cache usage
avg(vllm:gpu_cache_usage_perc)

# Alert threshold: > 0.8 (80%)
```

**GPU Memory**
```bash
# Check via nvidia-smi
nvidia-smi
```

### Performance Metrics

#### Throughput

```promql
# Requests per second
rate(ray_serve_num_router_requests_total[5m])

# Tokens per second
rate(vllm:generation_tokens_total[5m])
```

#### Resource Utilization

```promql
# CPU usage
ray_component_cpu_percentage

# Memory usage
ray_component_mem_shared_bytes

# Replica count
ray_serve_num_deployment_replicas
```

#### Autoscaling Activity

```promql
# Replica starts (scale-ups)
rate(ray_serve_deployment_replica_starts_total[5m])

# Current replicas
ray_serve_num_deployment_replicas
```

---

## Alerting

### Critical Alerts

Configure alerts for these conditions:

#### 1. KV Cache Saturation
```yaml
# Alert when KV cache > 80%
expr: avg(vllm:gpu_cache_usage_perc) > 0.8
for: 5m
severity: critical
```

#### 2. Waiting Requests
```yaml
# Alert when requests are queued
expr: vllm:num_requests_waiting > 0
for: 2m
severity: warning
```

#### 3. High Latency
```yaml
# Alert on P95 latency > 5s
expr: histogram_quantile(0.95, serve_deployment_processing_latency_ms) > 5000
for: 5m
severity: warning
```

#### 4. Service Down
```yaml
# Alert when Ray nodes are down
expr: up{job="ray"} == 0
for: 1m
severity: critical
```

#### 5. Replica Failures
```yaml
# Alert on replica failures
expr: rate(ray_serve_deployment_replica_failures_total[5m]) > 0
severity: critical
```

### Configuring Alerts in Grafana

1. Go to **Alerting** → **Alert Rules**
2. Create new rule
3. Define PromQL expression
4. Set threshold and duration
5. Configure notification channels

### Alert Response

1. **Acknowledge alert**: Log incident
2. **Investigate**: Check logs, metrics, dashboard
3. **Mitigate**: Apply fixes (scale up, restart, etc.)
4. **Document**: Record resolution steps

---

## Log Management

### Accessing Logs

#### Docker Logs

```bash
# Ray Serve logs
docker logs ray-serve
docker logs -f ray-serve  # Follow

# Nginx logs
docker logs gpu-cluster-nginx-proxy

# All services
docker compose logs
docker compose logs -f
```

#### Ray Dashboard Logs

1. Navigate to **Logs** tab in Ray Dashboard
2. Filter by component
3. Search logs

### Log Levels

- **INFO**: Normal operations
- **WARNING**: Potential issues
- **ERROR**: Errors requiring attention
- **CRITICAL**: Service-affecting issues

### Log Analysis

```bash
# Search for errors
docker logs ray-serve | grep -i error

# Count errors
docker logs ray-serve | grep -i error | wc -l

# Extract specific time range
docker logs ray-serve --since 1h

# Export logs
docker logs ray-serve > ray-serve-$(date +%Y%m%d).log
```

### Common Log Patterns

**Model Loading**:
```
Loading model Qwen/Qwen2.5-32B-Instruct...
Model loaded successfully
```

**Autoscaling**:
```
Scaling up deployment: adding replica
Replica started successfully
```

**Errors**:
```
ERROR: GPU allocation failed
ERROR: Model loading timeout
ERROR: Out of memory
```

---

## Performance Monitoring

### Regular Checks

#### Daily

- [ ] Check Ray Dashboard for cluster health
- [ ] Review Grafana dashboards for trends
- [ ] Check error logs
- [ ] Verify autoscaling behavior

#### Weekly

- [ ] Analyze performance trends
- [ ] Review resource utilization
- [ ] Check for capacity issues
- [ ] Review alert history

### Performance Baseline

Establish baseline metrics:
- Average request latency (P50, P95, P99)
- Request throughput (RPS)
- KV cache utilization
- GPU utilization
- Error rate

### Performance Degradation

**Symptoms**:
- Increasing latency
- High KV cache utilization
- Requests queuing
- High error rate

**Investigation**:
1. Check KV cache utilization
2. Review recent configuration changes
3. Check for resource constraints
4. Review autoscaling behavior
5. Analyze request patterns

---

## Health Checks

### Automated Health Checks

```bash
# API health
curl http://localhost:18080/health

# Ray cluster status
docker exec ray-serve ray status

# GPU availability
docker exec ray-serve nvidia-smi

# Prometheus targets
curl http://localhost:19090/api/v1/targets | jq '.data.activeTargets[] | select(.health != "up")'
```

### Manual Health Check Script

```bash
#!/bin/bash
# health_check.sh

echo "=== Health Check ==="

# API
echo -n "API: "
if curl -s http://localhost:18080/v1/models > /dev/null; then
    echo "✓ OK"
else
    echo "✗ FAILED"
fi

# Ray Dashboard
echo -n "Ray Dashboard: "
if curl -s http://localhost:18265 > /dev/null; then
    echo "✓ OK"
else
    echo "✗ FAILED"
fi

# Prometheus
echo -n "Prometheus: "
if curl -s http://localhost:19090/-/healthy > /dev/null; then
    echo "✓ OK"
else
    echo "✗ FAILED"
fi

# GPU
echo -n "GPU: "
if docker exec ray-serve nvidia-smi > /dev/null 2>&1; then
    echo "✓ OK"
else
    echo "✗ FAILED"
fi

# Ray Cluster
echo -n "Ray Cluster: "
if docker exec ray-serve ray status > /dev/null 2>&1; then
    echo "✓ OK"
else
    echo "✗ FAILED"
fi
```

---

## Incident Response

### Incident Classification

- **Critical**: Service down, data loss
- **High**: Service degradation, high error rate
- **Medium**: Performance issues, warnings
- **Low**: Minor issues, informational

### Response Procedure

1. **Detect**: Alert, monitoring, user report
2. **Assess**: Determine severity and impact
3. **Mitigate**: Apply quick fixes to restore service
4. **Resolve**: Implement permanent fix
5. **Document**: Post-incident review

### Common Incidents

#### Service Unavailable

**Symptoms**: 503 errors, service down

**Response**:
1. Check container status: `docker compose ps`
2. Check logs: `docker compose logs ray-serve`
3. Restart service: `docker compose restart ray-serve`
4. Verify recovery: `curl http://localhost:18080/v1/models`

#### High Latency

**Symptoms**: Slow responses, high P95 latency

**Response**:
1. Check KV cache utilization
2. Check waiting requests
3. Review autoscaling configuration
4. Consider scaling up replicas

#### GPU Errors

**Symptoms**: GPU allocation failures

**Response**:
1. Check GPU availability: `nvidia-smi`
2. Verify GPU access in container
3. Check tensor parallel size matches GPU count
4. Restart service if needed

#### Out of Memory

**Symptoms**: OOM errors, model loading failures

**Response**:
1. Check GPU memory: `nvidia-smi`
2. Reduce tensor parallel size
3. Reduce max model length
4. Reduce batch size

---

## Capacity Planning

### Resource Tracking

Monitor these metrics for capacity planning:

- Request rate trends
- KV cache utilization
- Replica count
- GPU utilization
- Memory usage

### Scaling Decisions

**Scale Up When**:
- KV cache > 80% consistently
- Waiting requests > 0
- Latency increasing
- Throughput maxed out

**Scale Down When**:
- Low utilization (< 20%)
- No waiting requests
- Excess replicas idle

### Capacity Limits

- **GPU Memory**: Model size × tensor_parallel_size
- **System Memory**: Ray overhead + model caching
- **Network**: Request throughput limits
- **Storage**: Model storage and logs

---

## Troubleshooting Procedures

### Service Won't Start

```bash
# 1. Check logs
docker compose logs ray-serve

# 2. Verify configuration
docker compose config

# 3. Check ports
lsof -i :18080

# 4. Verify GPU
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.4.0-runtime-ubuntu22.04 nvidia-smi
```

### Slow Performance

```bash
# 1. Check KV cache
# Query: avg(vllm:gpu_cache_usage_perc)

# 2. Check waiting requests
# Query: vllm:num_requests_waiting

# 3. Check latency
# Query: histogram_quantile(0.95, serve_deployment_processing_latency_ms)

# 4. Check GPU utilization
nvidia-smi

# 5. Check replica count
# Query: ray_serve_num_deployment_replicas
```

### Metrics Not Appearing

```bash
# 1. Verify Prometheus targets
curl http://localhost:19090/api/v1/targets

# 2. Check service discovery
docker exec gpu-cluster-prometheus cat /tmp/ray/prom_metrics_service_discovery.json

# 3. Verify metrics export port
docker exec ray-serve curl http://localhost:8080/metrics
```

---

## Additional Resources

- [Prometheus Ray Integration](../prometheus-ray-integration.md) - Metrics integration details
- [Troubleshooting Guide](../trouble-shooting.md) - Common issues and solutions
- [Ray Documentation](https://docs.ray.io/en/latest/cluster/metrics.html) - Ray metrics
- [vLLM Metrics](https://docs.vllm.ai/en/latest/design/metrics.html) - vLLM metrics

---

## Support

For issues:
1. Check [Troubleshooting Guide](../trouble-shooting.md)
2. Review relevant metrics in Grafana
3. Check Ray Dashboard for cluster status
4. Review container logs

