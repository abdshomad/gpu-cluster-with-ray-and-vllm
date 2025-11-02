# Ray Prometheus Integration Verification

This document describes the integration between Ray's auto-generated Prometheus configuration and our Prometheus/Grafana monitoring stack.

## Integration Overview

Ray generates a complete Prometheus configuration file at `/tmp/ray/session_latest/metrics/prometheus/prometheus.yml` on the head node. This file uses file-based service discovery (`file_sd_configs`) to automatically discover all Ray nodes (head and workers) for metrics scraping.

## Implementation Details

### 1. Shared Volume Setup

A Docker volume (`ray_metrics`) has been created to share Ray's metrics directory between containers:

```yaml
volumes:
  ray_metrics:
    driver: local
```

### 2. Volume Mounts

**Ray Serve Container (`ray-serve`):**
- Mounts `/tmp/ray` to the shared `ray_metrics` volume
- Ray writes service discovery files to `/tmp/ray/prom_metrics_service_discovery.json`
- Ray also generates Prometheus config at `/tmp/ray/session_latest/metrics/prometheus/prometheus.yml`

**Prometheus Container (`gpu-cluster-prometheus`):**
- Mounts the same `ray_metrics` volume at `/tmp/ray:ro` (read-only)
- Can access Ray's service discovery JSON file for automatic target discovery

### 3. Prometheus Configuration

The Prometheus configuration (`docker/prometheus/prometheus.yml`) has been updated to include:

- **Ray Auto-Discovery Job**: Uses `file_sd_configs` to automatically discover all Ray nodes from the service discovery file
  - File: `/tmp/ray/prom_metrics_service_discovery.json`
  - Refresh interval: 10 seconds
  - Automatically discovers head and worker nodes

- **Legacy Ray Head Job**: Kept for backwards compatibility (static target)

- **Prometheus Self-Monitoring**: Scrapes Prometheus's own metrics

### 4. Service Discovery

Ray's service discovery file (`/tmp/ray/prom_metrics_service_discovery.json`) contains:

```json
[
  {
    "labels": {"job": "ray"},
    "targets": ["172.20.0.2:59772", "172.20.0.2:44217", "172.20.0.2:44227"]
  }
]
```

This file is automatically updated by Ray as nodes join/leave the cluster.

## Verification

### Check Service Discovery File Access

```bash
# From Prometheus container
docker exec gpu-cluster-prometheus cat /tmp/ray/prom_metrics_service_discovery.json

# From Ray container
docker exec ray-serve cat /tmp/ray/prom_metrics_service_discovery.json
```

### Check Prometheus Targets

```bash
# Check if Ray targets are discovered and UP
docker exec gpu-cluster-prometheus wget -qO- http://localhost:9090/api/v1/targets | \
  python3 -c "import sys, json; data = json.load(sys.stdin); \
  targets = [t for t in data.get('data', {}).get('activeTargets', []) if 'ray' in t.get('labels', {}).get('job', '').lower()]; \
  print(f'Found {len(targets)} Ray targets:'); \
  [print(f\"  {t.get('labels', {}).get('instance')}: {t.get('health')}\") for t in targets]"
```

### Verify Metrics Collection

```bash
# Check Ray cluster metrics
docker exec gpu-cluster-prometheus wget -qO- 'http://localhost:9090/api/v1/query?query=ray_cluster_active_nodes'

# Check Ray Serve metrics
docker exec gpu-cluster-prometheus wget -qO- 'http://localhost:9090/api/v1/query?query=ray_serve_num_router_requests_total'

# List all available Ray metrics
docker exec gpu-cluster-prometheus wget -qO- http://localhost:9090/api/v1/label/__name__/values | \
  python3 -c "import sys, json; data = json.load(sys.stdin); \
  ray_metrics = [m for m in data.get('data', []) if 'ray' in m.lower()]; \
  print(f'Found {len(ray_metrics)} Ray metrics')"
```

### Access Prometheus Web UI

- **URL**: http://localhost:19090 (or configured `PROMETHEUS_PORT`)
- **Targets**: http://localhost:19090/targets - Check that all Ray targets show as "UP"
- **Graph**: http://localhost:19090/graph - Query Ray metrics

### Access Grafana Dashboard

- **URL**: http://localhost:13000 (or configured `GRAFANA_PORT`)
- **Login**: admin / admin (or configured `GRAFANA_ADMIN_PASSWORD`)
- Prometheus is automatically configured as a datasource

## Available Metrics

### Ray Core Metrics
- `ray_cluster_active_nodes` - Number of active nodes in the cluster
- `ray_actors` - Number of Ray actors
- `ray_gcs_actors_count` - GCS actor count
- `ray_component_cpu_percentage` - CPU usage by component
- `ray_component_mem_shared_bytes` - Memory usage by component

### Ray Serve Metrics
- `ray_serve_num_router_requests_total` - Total requests received by Serve router
- `ray_serve_num_deployment_replicas` - Current number of active replicas
- `ray_serve_deployment_replica_starts_total` - Number of replica scale-ups

### vLLM Metrics (when model is deployed)
- `vllm:time_to_first_token_seconds` - Time to first token (TTFT)
- `vllm:time_per_output_token_seconds` - Time per output token (TPOT)
- `vllm:gpu_cache_usage_perc` - KV cache utilization (0-1)
- `vllm:num_requests_running` - Number of running requests
- `vllm:num_requests_waiting` - Number of waiting requests

## Troubleshooting

### Issue: Service discovery file not found

**Symptom**: Prometheus logs show "no such file or directory" for `/tmp/ray/prom_metrics_service_discovery.json`

**Solution**:
1. Ensure Ray container is running and has initialized
2. Wait 10-30 seconds after Ray starts for files to be generated
3. Verify volume mount: `docker exec gpu-cluster-prometheus ls -la /tmp/ray/`
4. Recreate containers if volume was added after initial creation:
   ```bash
   docker compose up -d ray-serve prometheus
   ```

### Issue: Targets show as DOWN

**Symptom**: Prometheus targets page shows Ray targets as DOWN

**Solution**:
1. Check if Ray nodes are accessible from Prometheus container:
   ```bash
   docker exec gpu-cluster-prometheus wget -qO- http://172.20.0.2:59772/metrics
   ```
2. Verify network connectivity between containers
3. Check Ray metrics export port is configured correctly
4. Ensure Ray was started with `metrics_export_port` enabled

### Issue: No metrics appearing

**Symptom**: Targets are UP but no metrics are visible

**Solution**:
1. Verify Ray is actually running workloads (metrics only appear when Ray is active)
2. Check Prometheus query: `up{job="ray"}`
3. Verify scrape interval in Prometheus config
4. Check Prometheus logs for scrape errors

## Next Steps

1. **Import Ray Grafana Dashboards**: Ray provides pre-built Grafana dashboards at `/tmp/ray/session_latest/metrics/grafana/`. These can be imported into Grafana.

2. **Create Custom Dashboards**: Build custom dashboards focusing on:
   - vLLM golden signals (TTFT, TPOT, KV Cache Utilization)
   - Ray Serve autoscaling activity
   - GPU resource utilization
   - Request throughput and latency

3. **Set Up Alerts**: Configure Prometheus alerting rules for:
   - High KV cache utilization (>90%)
   - Ray nodes going down
   - High request latency
   - Autoscaler churn

## References

- [Ray Metrics Documentation](https://docs.ray.io/en/latest/cluster/metrics.html)
- [Prometheus File Service Discovery](https://prometheus.io/docs/prometheus/latest/configuration/configuration/#file_sd_config)
- [Ray Grafana Dashboards](https://docs.anyscale.com/monitoring/grafana-dashboards)

