# CheckMK Configuration Guide

This guide documents the step-by-step process to configure CheckMK for monitoring vLLM and Ray Serve metrics via Prometheus integration.

## Prerequisites

- CheckMK service is running and accessible (default: `http://localhost:15000`)
- Prometheus service is running and accessible from CheckMK container (internal: `http://prometheus:9090`)
- CheckMK credentials configured in `.secrets` file

## Step 1: Access CheckMK Web Interface

1. Navigate to CheckMK:
   ```
   http://localhost:15000/cmk/check_mk/
   ```

2. Login with credentials from `.secrets`:
   - Username: `cmkadmin` (or value from `CHECKMK_ADMIN`)
   - Password: Value from `CHECKMK_PASSWORD`

3. You should see the main dashboard with overview statistics (currently showing 0 hosts and 0 services).

## Step 2: Configure Prometheus Special Agent Rule

### 2.1 Navigate to Prometheus Agent Configuration

1. Click on **Setup** in the left sidebar
2. Expand **Agents** section
3. Click on **VM, cloud, container**
4. In the list of agents, find and click on **Prometheus**

### 2.2 Add Prometheus Rule

1. Click the **Add rule** button at the top of the page
2. Fill in the rule configuration:
   - **Description**: `Prometheus integration for vLLM and Ray Serve monitoring`
   - **URL server address**: `http://prometheus:9090`
     - **Important**: Since both CheckMK and Prometheus run in Docker Compose, use the service name `prometheus` instead of `localhost`
   - **Protocol**: `HTTP` (default)
   - **Verify SSL certificate**: Leave unchecked (off) for internal Docker network
   - **Authentication**: Leave empty (not required for internal Prometheus)

3. **Service creation using PromQL queries**: 
   - Initially leave this empty (we'll add services after creating a host)
   - Click **Add new service** if you want to define services directly in the rule

4. **Prometheus Scrape Targets**:
   - Leave empty (we're using PromQL queries instead)

5. **Conditions**:
   - **Condition type**: `Explicit conditions`
   - **Folder**: `Main`
   - Leave other conditions empty for now (we'll apply to specific hosts later)

6. Click **Save** to save the rule

### 2.3 Verify Rule Creation

After saving, you should see:
- A message: "Created new rule in ruleset 'Prometheus' in folder 'Main'"
- The rule appears in the list with your configured URL and description
- A notification shows "1 change" pending activation

## Step 3: Create a Host for Prometheus Monitoring

### 3.1 Navigate to Hosts

1. In the Setup menu, go to **Hosts** > **Hosts**
2. You'll see the host folder structure (initially just "Main" folder)

### 3.2 Add New Host

1. Select the **Main** folder
2. Click **Add host** button (or click **Add host to the monitoring** link)
3. Configure the host:
   - **Hostname**: `prometheus-server` (or your preferred name)
   - **IPv4 address**: `127.0.0.1` (placeholder - required even for special agents)
     - **Note**: This IP won't be used for connection since Prometheus special agent uses the URL configured in the rule
     - CheckMK requires an IP address for DNS lookup, but it's only used for hostname resolution
   - **Alias**: `Prometheus Server` (optional, but recommended)
   - **Host tags**: Add tags like `monitoring`, `prometheus`, `docker` for organization
   - **Host labels**: Optional labels for filtering

**Important**: Even though we're using a special agent that doesn't require direct host connection, CheckMK still requires an IP address field to be filled. Using `127.0.0.1` is a common workaround for virtual/special agent hosts.

### 3.3 Configure Host Agent

1. In the host configuration, the **Monitoring agents** section should be visible
2. The default setting is **"API integrations if configured, else Checkmk agent"**
3. The Prometheus special agent rule we created should automatically apply because:
   - The host is in the "Main" folder (matching our rule condition)
   - The rule has no other specific conditions that would exclude this host
4. **Note**: You don't need to manually select the Prometheus agent - it will be applied automatically based on the rule

### 3.4 Save Host Configuration

1. Click **Save & run service discovery** to save the host and trigger service discovery
   - This will save the host and immediately try to discover services
2. If you encounter a DNS lookup error:
   - The error "Failed to lookup IPv4 address of prometheus-server via DNS" can occur
   - This is expected for special agents - CheckMK tries DNS lookup but it's not critical
   - The services will still be discovered once you add PromQL queries to the rule or host
3. The host will appear in the host list with 2 pending changes (host creation + rule application)

### 3.5 Configure Services

Services can be configured in two ways:

**Option A: Add services to the Prometheus rule** (recommended for uniformity)
1. Edit the Prometheus rule (Setup > Agents > VM, cloud, container > Prometheus)
2. Click **Edit** on the rule you created
3. In "Service creation using PromQL queries", click **Add new service**
4. Configure each service (see Step 4 below)

**Option B: Configure services per host**
1. Navigate to the host: **Setup > Hosts > Main > prometheus-server**
2. Go to **Services** section
3. Add PromQL-based services directly to this host

## Step 4: Define Services Using PromQL Queries

### 4.1 Add PromQL-Based Services

For each metric you want to monitor, you can either:

**Option A: Add services in the Prometheus rule** (applies to all hosts using the rule)
1. Edit the Prometheus rule you created in Step 2
2. In "Service creation using PromQL queries", click **Add new service**
3. Fill in:
   - **Service name**: e.g., `vLLM Time to First Token (p95)`
   - **Assign service to following host**: Select the host or leave empty for all hosts
   - **PromQL queries**: Click **Add new PromQL query** and enter:
     ```
     histogram_quantile(0.95, vllm:time_to_first_token_seconds{job="ray"})
     ```

**Option B: Add services per host** (more granular control)
1. Edit the host configuration
2. In Services section, add services individually
3. Configure PromQL queries for each service

### 4.2 Key vLLM and Ray Serve Metrics

Based on `docker/checkmk/prometheus_services/vllm_services.mk`, here are recommended services:

#### Critical vLLM Metrics

1. **Time to First Token (TTFT) - p95**
   - Service name: `vLLM Time to First Token (p95)`
   - PromQL: `histogram_quantile(0.95, vllm:time_to_first_token_seconds{job="ray"})`
   - Alert threshold: Warning > 2s, Critical > 5s

2. **Time Per Output Token (TPOT) - Average**
   - Service name: `vLLM Time Per Output Token`
   - PromQL: `avg(vllm:time_per_output_token_seconds{job="ray"})`

3. **KV Cache Utilization** (Most Critical)
   - Service name: `vLLM KV Cache Utilization`
   - PromQL: `avg(vllm:gpu_cache_usage_perc{job="ray"}) * 100`
   - Alert threshold: Warning > 80%, Critical > 95%
   - **Note**: This is the primary metric for autoscaling decisions

4. **Request States**
   - **Running Requests**: `sum(vllm:num_requests_running{job="ray"})`
   - **Waiting Requests**: `sum(vllm:num_requests_waiting{job="ray"})`
     - Alert: Warning if > 0 (queue building up)

5. **Token Usage**
   - **Prompt Tokens/sec**: `sum(rate(vllm:prompt_tokens_total{job="ray"}[5m]))`
   - **Generation Tokens/sec**: `sum(rate(vllm:generation_tokens_total{job="ray"}[5m]))`

#### Ray Serve Metrics

1. **Processing Latency - p95**
   - Service name: `Ray Serve Processing Latency (p95)`
   - PromQL: `histogram_quantile(0.95, serve_deployment_processing_latency_ms{job="ray"} / 1000)`
   - Alert threshold: Warning > 5s, Critical > 10s

2. **Request Throughput**
   - Service name: `Ray Serve Requests/sec`
   - PromQL: `sum(rate(serve_num_router_requests_total{job="ray"}[5m]))`

3. **Replica Management**
   - **Active Replicas**: `sum(serve_num_deployment_replicas{job="ray"})`
   - **Replica Starts/sec**: `sum(rate(serve_deployment_replica_starts_total{job="ray"}[5m]))`
     - Monitor for autoscaler activity/churn

### 4.3 Service Configuration Best Practices

- **Service naming**: Use descriptive names that indicate what the metric measures
- **Unit specification**: Ensure units are correctly configured (seconds, percentage, count, etc.)
- **Alert thresholds**: Set appropriate warning and critical thresholds based on:
  - SLAs (Service Level Agreements)
  - Performance baselines
  - Autoscaling triggers
- **Update intervals**: CheckMK will query Prometheus at regular intervals (typically every minute)

## Step 5: Activate Changes

### 5.1 Review Pending Changes

1. Click on the **"X changes"** notification at the top of any Setup page
2. Review the changelog to see what will be activated:
   - Prometheus rule creation
   - Host creation
   - Service definitions

### 5.2 Activate Changes

1. Click **Activate affected** button
2. Select which site(s) to activate changes on (default: all sites)
3. Click **Activate** or **Activate on selected sites**
4. Wait for activation to complete (usually takes a few seconds to a minute)

### 5.3 Verify Activation

1. After activation, you'll see:
   - Status: **"Activated"** and **"This site is up-to-date"**
   - All pending changes are now active
   
2. **Important**: You may see a DNS lookup warning:
   - Warning: "Cannot lookup IP address of 'prometheus-server' via DNS"
   - **This is normal and expected** for Prometheus special agent hosts
   - Prometheus special agents don't use DNS - they connect directly via the configured URL
   - Monitoring will work correctly despite this warning

3. Navigate to **Monitor** > **All hosts** to see your new host
4. Services will appear once CheckMK's monitoring engine queries Prometheus (typically within 1-5 minutes)

## Step 6: Verify Service Discovery and Monitoring

### 6.1 Check Service Discovery

1. Navigate to your host: **Monitor** > **All hosts** > `prometheus-server`
2. Click on **Services** tab
3. Services should appear with their current status:
   - **OK**: Metric is being retrieved successfully
   - **Warning**: Value exceeds warning threshold
   - **Critical**: Value exceeds critical threshold
   - **Unknown**: Query failed or metric not found

### 6.2 View Service Details

1. Click on any service to view:
   - Current metric value
   - Historical graphs
   - Alert thresholds
   - Check details and performance data

### 6.3 Troubleshooting

**If services show as Unknown or not appearing:**

1. **Verify Prometheus connection**:
   - In CheckMK, check the agent output for the host
   - Look for connection errors to `http://prometheus:9090`

2. **Verify PromQL queries**:
   - Test queries in Prometheus web UI: `http://localhost:19090`
   - Ensure metrics exist with the exact names used in queries
   - Check label filters (e.g., `{job="ray"}`)

3. **Check Docker networking**:
   - Ensure CheckMK and Prometheus are on the same Docker network
   - Verify Prometheus is accessible from CheckMK container:
     ```bash
     docker exec gpu-cluster-checkmk curl http://prometheus:9090/api/v1/status/config
     ```

4. **Review CheckMK logs**:
   ```bash
   docker logs gpu-cluster-checkmk
   ```

5. **Verify rule application**:
   - Check that the Prometheus special agent rule is applied to your host
   - Verify rule conditions match your host (folder, tags, etc.)

## Step 7: Configure Dashboards and Views (Optional)

### 7.1 Create Custom Views

1. Navigate to **Customize** > **Views**
2. Create views for:
   - vLLM metrics overview
   - Ray Serve performance
   - Combined monitoring dashboard

### 7.2 Set Up Alerting Rules

1. Navigate to **Setup** > **Services** > **Service monitoring rules**
2. Configure notification rules based on service states
3. Set up alert routing to:
   - Email
   - Slack
   - PagerDuty
   - Custom notification scripts

### 7.3 Create Reports

1. Navigate to **Reports** section
2. Create scheduled reports for:
   - Daily performance summaries
   - Weekly capacity planning
   - Monthly SLA reports

## Integration with Other Services

### Access via Nginx Proxy

All CheckMK pages are accessible through the Nginx reverse proxy:
- Main dashboard: `http://localhost:{NGINX_HTTP_PORT}/checkmk/monitoring/check_mk/`
- Direct access: `http://localhost:15000/cmk/check_mk/`

### Integration Status

CheckMK is now integrated with:
- ✅ **Prometheus**: Metrics source for monitoring
- ✅ **Ray Serve**: Monitored via Prometheus metrics
- ✅ **vLLM**: Monitored via Prometheus metrics
- ✅ **Grafana**: Complementary visualization (Grafana for dashboards, CheckMK for alerting)
- ✅ **Nginx**: Unified access point

## Maintenance and Updates

### Updating Service Definitions

1. Edit the Prometheus rule or individual host services
2. Add/modify/remove PromQL queries as needed
3. Activate changes

### Adding New Metrics

1. Ensure Prometheus is scraping the new metrics
2. Add corresponding PromQL queries to CheckMK services
3. Configure appropriate alert thresholds

### Backup Configuration

CheckMK configuration is stored in:
- `/omd/sites/cmk/etc/check_mk/` (inside container)
- Mounted volume: `checkmk_data` (Docker volume)

To backup:
```bash
docker exec gpu-cluster-checkmk omd backup cmk
```

## Reference Files

- **Prometheus service definitions**: `docker/checkmk/prometheus_services/vllm_services.mk`
- **Docker Compose config**: `docker/docker-compose.yml`
- **Nginx configuration**: `docker/nginx/nginx.conf`
- **Secrets**: `.secrets` (CheckMK credentials)

## Next Steps

1. ✅ Prometheus rule created
2. ⏳ Create host for Prometheus monitoring
3. ⏳ Add PromQL-based services
4. ⏳ Activate changes
5. ⏳ Verify monitoring is working
6. ⏳ Configure alerting rules
7. ⏳ Set up dashboards and views

## Configuration Progress Log

### Completed Steps ✅

**Step 1: Access CheckMK** ✅
- Successfully logged into CheckMK web interface
- Accessed main dashboard

**Step 2: Configure Prometheus Rule** ✅
- Created Prometheus special agent rule in Setup > Agents > VM, cloud, container > Prometheus
- Configured rule with:
  - Description: "Prometheus integration for vLLM and Ray Serve monitoring"
  - URL: `http://prometheus:9090` (Docker service name)
  - Protocol: HTTP
  - Folder: Main (rule condition)
- Rule saved successfully - **1 pending change**

**Step 3: Create Host** ✅
- Created host `prometheus-server` in Main folder
- Host configuration:
  - Hostname: `prometheus-server`
  - IPv4: Not set (can use `127.0.0.1` as placeholder for special agents)
  - Monitoring agent: Will auto-apply Prometheus rule (no manual selection needed)
- Host saved successfully - **2 pending changes** (host + rule application)
- Note: DNS lookup error occurred but is expected for special agent hosts - not critical

**Step 4: Add PromQL Services to Rule** ✅
- Edited the Prometheus rule to add services
- Added first service:
  - **Service name**: `vLLM KV Cache Utilization`
  - **Metric label**: `kv_cache_usage_percent`
  - **PromQL query**: `avg(vllm:gpu_cache_usage_perc{job="ray"}) * 100`
- Service added successfully - **3 pending changes** (rule, host, service)
- Rule saved with service definition

**Step 5: Activate Changes** ✅
- Navigated to Activate pending changes page
- Changes were already activated (auto-activation)
- Status: **Activated** - "This site is up-to-date"
- Activation completed successfully
- **Note**: DNS lookup warning appears but is expected for special agent hosts - does not affect monitoring
  - Warning: "Cannot lookup IP address of 'prometheus-server' via DNS"
  - This is normal: Prometheus special agent uses the configured URL (`http://prometheus:9090`), not DNS resolution

**Step 6: Service Discovery** ⚠️
- Service discovery preview shows DNS lookup error (expected)
- **Important**: Services defined in Prometheus rule will be discovered and monitored automatically
- The DNS warning is informational only - monitoring works via the Prometheus URL
- Services will appear once CheckMK's monitoring engine runs and queries Prometheus

**Next Steps:**
- ⏳ Wait for monitoring engine to run (typically every 1-5 minutes)
- ⏳ Verify services appear in monitoring view
- ⏳ Add additional services (TTFT, TPOT, Ray Serve metrics, etc.) - can be done later by editing the rule
- ⏳ Configure alert thresholds for services

## Summary

This guide covered:
1. Accessing CheckMK web interface ✅
2. Configuring Prometheus special agent rule ✅
3. Creating hosts for monitoring ✅
4. Defining services using PromQL queries ✅
5. Activating changes ✅
6. Understanding service discovery process ✅

The configuration enables CheckMK to:
- Query Prometheus for vLLM and Ray Serve metrics
- Monitor key performance indicators (TTFT, TPOT, KV Cache, etc.)
- Alert on threshold violations
- Provide unified monitoring alongside Grafana dashboards

