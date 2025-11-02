# CheckMK Configuration for vLLM on Ray Serve

This directory contains CheckMK configuration files for integrating Prometheus metrics from the vLLM/Ray Serve deployment.

## Overview

CheckMK uses its **Prometheus special agent** to query Prometheus and create services based on PromQL queries. This integration pattern is documented in `docs/vllm-ray-serve-guide.md` Section 2.3.1.

## Configuration Files

### `configuration/prometheus_config.yaml`

Defines the Prometheus connection settings:
- Prometheus server URL
- Scrape intervals
- Service discovery mode
- Default labels and filters

### `prometheus_services/vllm_services.mk`

Defines the Prometheus services that CheckMK will create. Each service corresponds to a critical vLLM or Ray Serve metric from Table 2.1 in the guide:

**Critical vLLM Metrics (Golden Signals):**
1. **TTFT (Time to First Token)** - User-perceived latency
   - p50 and p95 percentiles
   - Alert on p95 > 2s

2. **TPOT (Time Per Output Token)** - Generation speed
   - Average and p95 percentiles

3. **KV Cache Utilization** - Primary bottleneck
   - Most critical metric for load and autoscaling
   - Alert on > 80% (autoscale threshold)

4. **Request States** - Engine load indicators
   - Running and waiting requests
   - Alert if waiting > 0 (engine saturated)

5. **Token Usage** - Cost/usage analysis
   - Prompt and generation tokens per second

**Ray Serve Metrics:**
6. **Processing Latency** - End-to-end latency
   - Alert on p95 > 5s

7. **Request Throughput** - Requests per second (RPS)

8. **Replica Management** - Autoscaler activity
   - Active replicas count
   - Replica starts rate (churn monitoring)

## Setup Instructions

### 1. Initial Configuration (via CheckMK Web UI)

After starting the CheckMK container:

1. **Access CheckMK Web UI:**
   - URL: `http://localhost:{CHECKMK_PORT}/monitoring/check_mk/` (default: 15000)
   - Default credentials: `cmkadmin` / `admin` (or as configured in `.env`)

2. **Create a Prometheus Host:**
   - Navigate to: `Setup` > `Hosts` > `Add host`
   - Host name: `prometheus-ray-cluster`
   - IP address: `prometheus` (Docker service name)
   - Tags: Add `prometheus` tag

3. **Configure Prometheus Special Agent:**
   - Navigate to: `Setup` > `Agents` > `VM, cloud, container`
   - Create a new rule: "Prometheus Special Agent"
   - Configure:
     - **Prometheus URL:** `http://prometheus:9090`
     - **Service creation:** Select "Service creation using PromQL queries"
     - **Import services from:** `/omd/sites/monitoring/etc/checkmk/multisite.d/wato/prometheus_services/vllm_services.mk`

4. **Apply Changes:**
   - Click "Activate affected" to activate the new configuration

### 2. Alternative: Direct File Configuration

The configuration files in this directory are mounted into the CheckMK container. You can also manually copy them to the appropriate locations within CheckMK if needed.

## Service Definitions Format

Each service in `vllm_services.mk` follows this pattern:

```python
check_parameters["<service_id>"] = {
    "promql_query": "<PromQL query>",
    "service_name": "<Display Name>",
    "metric_name": "<Metric Label>",
    "unit": "<Unit>",
    "levels": (warning, critical),  # Optional thresholds
}
```

## Alerting Recommendations

Based on the guide, recommended alert thresholds:

- **vLLM KV Cache Utilization:** Warning at 80%, Critical at 95%
- **vLLM TTFT (p95):** Warning at 2s, Critical at 5s
- **Ray Serve Latency (p95):** Warning at 5s, Critical at 10s
- **vLLM Requests Waiting:** Warning if > 0, Critical if > 10

## Integration with Existing Services

CheckMK is integrated with:
- **Prometheus:** CheckMK queries metrics from Prometheus via PromQL
- **Nginx:** CheckMK web UI is proxied at `/checkmk` path
- **Docker Compose:** Service dependencies ensure proper startup order

## Troubleshooting

### CheckMK Not Starting

- Check logs: `docker logs gpu-cluster-checkmk`
- Verify Prometheus is accessible: `docker exec gpu-cluster-checkmk curl http://prometheus:9090/api/v1/query?query=up`
- CheckMK initialization can take 2-3 minutes on first start

### Services Not Appearing

- Verify Prometheus is returning metrics: Query Prometheus directly
- Check CheckMK discovery: Navigate to `Setup` > `Services` > `Services of host`
- Verify PromQL queries are valid: Test queries in Prometheus UI

### Metrics Missing

- Ensure Ray Serve is emitting metrics on `/metrics` endpoint
- Verify Prometheus is scraping Ray metrics (check Prometheus targets)
- Check job labels match (should be `job="ray"` or `job="ray-head"`)

## References

- [CheckMK Prometheus Integration Docs](https://docs.checkmk.com/latest/en/monitoring_prometheus.html)
- [vLLM Ray Serve Guide - CheckMK Integration](docs/vllm-ray-serve-guide.md#231-checkmk-integration)
- [vLLM Ray Serve Guide - Metrics Table](docs/vllm-ray-serve-guide.md#21-the-metrics-foundation-key-performance-indicators-kpis)

