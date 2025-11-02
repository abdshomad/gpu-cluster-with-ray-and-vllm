# **Production-Grade vLLM Serving: A Guide to Ray Serve Deployment, Observability, and PII Security**

## **Part 1: Foundational Deployment \- Serving vLLM with Ray Serve**

### **1.1 Core Concepts: Why vLLM on Ray Serve?**

Deploying Large Language Models (LLMs) into production requires bridging the gap between raw inference speed and scalable, resilient serving infrastructure. This is achieved by combining two specialized components: vLLM as the inference engine and Ray Serve as the serving framework.

* **vLLM:** This is the high-performance inference engine. Its primary contributions are optimizations like PagedAttention and continuous batching, which dramatically increase throughput (queries per second) and reduce latency for LLM inference, especially on high-demand GPU hardware.  
* **Ray Serve:** This is the scalable, production-grade serving framework. While vLLM excels at running a model on a single node, Ray Serve provides the critical production features vLLM lacks:  
  * **Scalability:** Horizontally scales by creating more replicas (instances) of the vLLM engine and load-balancing across them.  
  * **Distribution:** Abstracts the complexity of multi-node and multi-GPU serving, allowing a single model to span multiple machines.  
  * **Autoscaling:** Dynamically adjusts the number of replicas based on real-time traffic, ensuring high availability without over-provisioning resources.  
  * **API Endpoint:** Provides a unified HTTP and FastAPI endpoint for the model, handling request batching and streaming.

This combination is symbiotic: Ray Serve abstracts the complex orchestration, allowing operators to manage multi-GPU parallelism (tensor parallelism) and multi-node parallelism (pipeline parallelism) through simple configuration parameters rather than complex, bespoke engineering code.

### **1.2 The Modern Deployment Pattern: LLMConfig and build\_openai\_app**

The officially documented and recommended approach for this integration is the high-level ray.serve.llm module. This abstraction simplifies deployment into two main components:

1. **LLMConfig:** This is a central dataclass that defines the entire deployment. It is the single point of control, encapsulating the model to be loaded, the vLLM engine parameters, and the Ray Serve resource and scaling configurations.  
2. **build\_openai\_app:** This function consumes one or more LLMConfig objects and automatically constructs a complete, production-ready FastAPI application. This application is pre-configured to be compatible with the OpenAI API, complete with schema validation, request handling, and load balancing across the defined models.

### **1.3 Implementation: Annotated Deployment Code**

The following Python script demonstrates a complete, production-oriented deployment using this modern pattern.

#### **Step 1: Dependencies**

Ensure the necessary packages are installed in the Ray cluster's Python environment.  
`# This code requires:`  
`# pip install "ray[serve,llm]>=2.45.0" vllm`  
`# [span_11](start_span)[span_11](end_span)`

#### **Step 2: Define the LLMConfig**

This configuration deploys a 32-billion parameter Qwen model, distributing it across 4 GPUs using tensor parallelism and enabling autoscaling.  
`from ray import serve`  
`from ray.serve.llm import LLMConfig, build_openai_app`

`# LLMConfig is the single point of control for the model,`   
`# resources, and vLLM engine parameters.`  
`llm_config = LLMConfig(`  
    `# 1. Model Loading Configuration [span_12](start_span)[span_12](end_span)`  
    `model_loading_config={`  
        `'model_id': 'Qwen/Qwen2.5-32B-Instruct'`  
        `# For pre-downloaded models, to speed up startup:`  
        `# 'model_source': '/path/to/local/model' [span_26](start_span)[span_26](end_span)[span_28](start_span)[span_28](end_span)`  
    `},`  
      
    `# 2. Deployment & Scaling Configuration [span_13](start_span)[span_13](end_span)`  
    `deployment_config={`  
        `'autoscaling_config': {`  
            `'min_replicas': 1,`  
            `'max_replicas': 4, # Scale up to 4 replicas [span_30](start_span)[span_30](end_span)`  
            `'target_ongoing_requests': 32, # Target 32 concurrent requests per replica [span_14](start_span)[span_14](end_span)`  
        `},`  
        `'max_ongoing_requests': 64, # Max concurrent requests per replica [span_15](start_span)[span_15](end_span)`  
    `},`

    `# 3. Ray Actor Resource Allocation`  
    `accelerator_type='L4', # Specify the GPU type, e.g., L4, H100, A100 [span_31](start_span)[span_31](end_span)[span_33](start_span)[span_33](end_span)`  
    `num_replicas=1, # The initial number of replicas to start`

    `# 4. vLLM Engine Keyword Arguments (kwargs) [span_16](start_span)[span_16](end_span)`  
    `engine_kwargs={`  
        `# Distribute the model across 4 GPUs [span_17](start_span)[span_17](end_span)`  
        `'tensor_parallel_size': 4,`   
        `# For multi-node, one could also set:`  
        `# 'pipeline_parallel_size': 2[span_27](start_span)[span_27](end_span)[span_29](start_span)[span_29](end_span)`  
          
        `# vLLM performance tuning`  
        `'max_num_batched_tokens': 8192,`  
        `'max_model_len': 8192,`  
        `'max_num_seqs': 64,`  
        `'trust_remote_code': True,`  
        `'enable_prefix_caching': True[span_35](start_span)[span_35](end_span)[span_36](start_span)[span_36](end_span)`  
    `},`  
`)`

#### **Step 3: Build and Run the Application**

The build\_openai\_app function creates the FastAPI application, which is then deployed to the cluster using serve.run.  
`# build_openai_app translates the LLMConfig into a`   
`# deployable FastAPI application [span_37](start_span)[span_37](end_span)[span_38](start_span)[span_38](end_span)`  
`llm_app = build_openai_app({"llm_configs": [llm_config]})`

`# serve.run deploys the application to the Ray cluster`  
`# and exposes it at the specified route prefix.`  
`serve.run(llm_app, route_prefix="/v1")`

#### **Step 4: Interact with the Endpoint**

Once deployed, the service can be queried using any OpenAI-compatible client.  
`from openai import OpenAI`

`# Connect to the local Ray Serve endpoint`  
`client = OpenAI(`  
    `base_url="http://localhost:8000/v1",`   
    `api_key="fake-key" # API key is not used`  
`)`

`print("Sending request to vLLM on Ray Serve...")`  
`response = client.chat.completions.create(`  
    `model='Qwen/Qwen2.5-32B-Instruct',`  
    `messages=,`  
    `stream=True`  
`)`

`# Stream the response`  
`for chunk in response:`  
    `if chunk.choices.delta.content is not None:`  
        `print(chunk.choices.delta.content, end="", flush=True)`

`print("\nStream complete.")`

*(Code synthesized from )*

### **1.4 Production Considerations: Cluster and Dependencies**

Before deployment, several prerequisites must be met on the cluster itself:

* **Hardware:** The accelerator\_type (e.g., 'L4', 'H100') specified in LLMConfig must match the GPU resources available in the Ray cluster. Furthermore, the tensor\_parallel\_size must not exceed the number of GPUs available *per node*.  
* **Dependencies:** The vllm package must be installed in the runtime environment of all Ray worker nodes. This is typically managed in the Ray cluster configuration file under pip or runtime\_env settings.  
* **Version Compatibility:** The integration between Ray and vLLM is under active development. Mismatched versions of ray\[serve,llm\] and vllm are a frequent source of deployment failures. It is imperative to consult the official Ray and vLLM documentation to ensure the selected versions are compatible. The presence of environment variables like VLLM\_USE\_V1="1" in some documentation is indicative of this rapid iteration and the potential for breaking changes between releases.

## **Part 2: Comprehensive Observability \- Monitoring the Deployed Model**

A deployed model is incomplete without robust monitoring. Ray's observability strategy is centered on its native ability to emit time-series metrics in the **Prometheus format**. Ray nodes (head and workers) expose a /metrics endpoint that all major observability tools can consume.

### **2.1 The Metrics Foundation: Key Performance Indicators (KPIs)**

Effective monitoring requires tracking not just generic service metrics but also LLM-specific "Golden Signals." The vLLM engine, when run on Ray Serve, exposes a rich set of these metrics.  
An SRE or MLOps engineer must prioritize the following metrics:

1. **Time to First Token (TTFT):** vllm:time\_to\_first\_token\_seconds. This histogram measures the *perceived responsiveness* of the model, covering the time for prompt ingestion and the prefill stage.  
2. **Time Per Output Token (TPOT):** vllm:time\_per\_output\_token\_seconds. This histogram measures the *generation speed* (decode) of the model.  
3. **KV Cache Utilization:** vllm:gpu\_cache\_usage\_perc. This gauge (0-1) is the **primary resource bottleneck** for vLLM. If this metric reaches 1 (100%), the engine is saturated and cannot accept new requests. This, not overall GPU memory, is the most critical metric for load and autoscaling.  
4. **Request States:** vllm:num\_requests\_running and vllm:num\_requests\_waiting. These gauges show the engine's internal load. A persistently non-zero \_waiting count indicates the service is saturated.

The following table synthesizes these critical metrics into a dashboarding and alerting guide for a production environment.  
**Table 2.1: Critical Observability Metrics for vLLM on Ray Serve**

| Metric Name | Type | Source | Operational Significance (The "Why") |
| :---- | :---- | :---- | :---- |
| vllm:time\_to\_first\_token\_seconds | Histogram | vLLM Engine | **(User-Perceived Latency)** Measures time from request to first token. High TTFT \= prefill bottleneck. **Alert on p95 \> 2s.** |
| vllm:time\_per\_output\_token\_seconds | Histogram | vLLM Engine | **(Generation Speed)** Measures time *between* tokens. High TPOT \= slow decoding. **Track average.** |
| vllm:gpu\_cache\_usage\_perc | Gauge | vLLM Engine | **(Primary Bottleneck)** KV cache usage (0-1). If 1, engine is saturated. **Autoscale on \> 0.8.** |
| vllm:num\_requests\_running | Gauge | vLLM Engine | Number of *active* requests in the vLLM engine. **Track for load.** |
| vllm:num\_requests\_waiting | Gauge | vLLM Engine | Number of *queued* requests. If \> 0, engine is saturated. **Alert on \> 0\.** |
| vllm:prompt\_tokens\_total | Counter | vLLM Engine | Total prompt tokens processed. **Track for cost/usage analysis.** |
| vllm:generation\_tokens\_total | Counter | vLLM Engine | Total generated tokens. **Track for cost/usage analysis.** |
| serve\_deployment\_processing\_latency\_ms | Histogram | Ray Serve | **(Total Latency)** End-to-end time *within* the replica, including queueing. **Alert on p95 \> 5s.** |
| serve\_num\_router\_requests\_total | Counter | Ray Serve | Total number of requests received by the Serve ingress. **Track for throughput (RPS).** |
| serve\_deployment\_replica\_starts\_total | Counter | Ray Serve | Number of replica scale-ups. **Monitor for autoscaler activity/churn.** |
| serve\_num\_deployment\_replicas | Gauge | Ray Serve | Current number of active replicas. **Correlate with load metrics.** |

### **2.2 Primary Stack: Prometheus and Grafana**

This combination is the default, de facto standard for monitoring Ray clusters and is the best-supported path.

#### **2.2.1 Prometheus Scraping Configuration**

Prometheus must be configured to discover and scrape the /metrics endpoints from all Ray nodes. The method differs based on the environment.  
**Path A: Local / VM Deployment** This path is ideal for development and testing.

1. Start the Ray head node with a specific metrics port: ray start \--head \--metrics-export-port=8080.  
2. Ray conveniently generates a complete prometheus.yml configuration file, which is placed in the head node's filesystem at /tmp/ray/session\_latest/metrics/prometheus/prometheus.yml.  
3. This generated file uses file\_sd\_configs to automatically discover all worker nodes in the cluster.  
4. The user can then start a local Prometheus server, pointing it directly to this auto-generated file: ./prometheus \--config.file=/tmp/ray/session\_latest/metrics/prometheus/prometheus.yml.

**Path B: Kubernetes (KubeRay) Deployment** This is the recommended path for production.

1. Install the kube-prometheus-stack Helm chart, which provides the Prometheus Operator.  
2. Install the KubeRay operator. When installing, the key is to set metrics.serviceMonitor.enabled=true in the Helm configuration.  
3. This ServiceMonitor automatically configures the Prometheus Operator to find all Ray clusters and scrape their PodMonitor endpoints, automating the discovery of all Ray head and worker pods.

#### **2.2.2 Grafana Dashboard Implementation**

Users do not need to build complex Grafana dashboards from scratch.

1. **Add Data Source:** First, configure Grafana to use the Prometheus server (from step 2.2.1) as a data source. The URL will typically be http://af-prometheus-kube-prometh-prometheus.prometheus.svc.cluster.local:9090 or similar within Kubernetes.  
2. **Import Pre-built Dashboards:** Ray provides a set of pre-built Grafana dashboard JSON files.  
   * On the Ray head pod, these JSON files are located in /tmp/ray/session\_latest/metrics/grafana/dashboards/.  
   * A user can copy these files from the pod to their local machine (e.g., using kubectl cp) and manually import them into Grafana.  
   * **Automation:** When using the KubeRay install.sh script, this process can be fully automated by including the \--auto-load-dashboard true flag, which automatically loads these dashboards into Grafana upon installation.  
3. **Embedding (Optional):** For convenience, these Grafana panels can be embedded directly into the Ray Dashboard's "Metrics" view. This requires setting two environment variables on the Ray head node: RAY\_GRAFANA\_HOST (the address Grafana is reachable from the *backend*) and RAY\_GRAFANA\_IFRAME\_HOST (the address Grafana is reachable from the *user's browser*).

### **2.3 Alternative and Enterprise Tooling Integration**

The central /metrics endpoint allows integration with nearly any monitoring tool.

#### **2.3.1 CheckMK Integration**

There is no native Checkmk plugin for Ray. However, Checkmk provides a "Prometheus special agent," which is the correct integration path. This agent queries Prometheus and pulls the data into Checkmk.  
**Implementation Steps:**

1. In Checkmk, create a new host. This host will represent the *Prometheus data source*, not the Ray cluster itself.  
2. Navigate to Setup \> Agents \> VM, cloud, container and create a "Prometheus" rule, configuring it to point to the Prometheus server's URL.  
3. Within the rule, select Service creation using PromQL queries.  
4. Define new Checkmk services by writing PromQL queries. For example, to monitor the vLLM KV cache:  
   * **Service Name:** vLLM\_KV\_Cache\_Utilization  
   * **PromQL Query:** avg(vllm:gpu\_cache\_usage\_perc{job="ray"}) \* 100  
5. Checkmk will execute this query against Prometheus and treat the result as a standard service, allowing for Checkmk's alerting and dashboarding to be applied to Ray/vLLM metrics.

#### **2.3.2 Datadog Integration**

Datadog provides an official, supported integration for Ray. The Datadog Agent is configured to scrape the same OpenMetrics endpoint that Prometheus uses.  
**Implementation Steps:**

1. Ensure the Datadog Agent (version 7.49.0 or later) is installed.  
2. **For VM/Host Deployments:** Edit the ray.d/conf.yaml file in the agent's configuration directory and specify the endpoint :  
   `# ray.d/conf.yaml`  
   `instances:`  
    `- openmetrics_endpoint: http://<RAY_HEAD_NODE_IP>:8080`  
      `# Optionally collect custom application metrics`  
      `extra_metrics:`  
        `- my_custom_ray_metric`

3. **For Kubernetes (Recommended):** The integration is configured via pod annotations. Add the following annotation to the headGroupSpec and workerGroupSpecs in the KubeRay RayCluster or RayService manifest :  
   `template:`  
     `metadata:`  
       `annotations:`  
         `ad.datadoghq.com/ray.checks: |-`  
           `{`  
             `"ray": {`  
               `"instances": [`  
                 `{`  
                   `"openmetrics_endpoint": "http://%%host%%:8080"`  
                 `}`  
               `]`  
             `}`  
           `}`

#### **2.3.3 OpenTelemetry (OTel) Integration \- A Critical Warning**

Ray's documentation includes an integration with OpenTelemetry for distributed tracing. However, the official documentation explicitly states this is an **"Alpha feature and no longer under active development/being maintained"**.  
Relying on an unmaintained, alpha-status feature for production-critical observability is a significant technical risk. The supported, robust, and maintained path for Ray/vLLM observability is the Prometheus metrics endpoint. If distributed tracing is required, it should be implemented at the application level (e.g., using standard OpenTelemetry in the FastAPI layer) rather than depending on the deprecated ray.util.tracing module.

## **Part 3: Data Security \- Architecting PII Masking for Inputs and Outputs**

A primary security risk in LLM applications is the inadvertent submission of Personally Identifiable Information (PII) by users. This PII (names, emails, addresses) can then be captured in request logs, stored in intermediate systems, or even exposed in model outputs, creating significant compliance and privacy risks.  
The recommended solution is to implement an architecture that intercepts, analyzes, and anonymizes PII in both requests and responses. The premier open-source tool for this in Python is **Microsoft Presidio**.

### **3.1 Core Tooling: Microsoft Presidio Implementation**

Presidio operates in a two-stage process: Analyze (detect PII) and Anonymize (mask or replace PII).

#### **3.1.1 Step 1: Detecting PII with AnalyzerEngine**

The AnalyzerEngine uses a combination of NLP models (like spaCy) and regex-based recognizers to identify PII entities within a text.  
**Code Example:**  
`from presidio_analyzer import AnalyzerEngine`

`# This loads the default spaCy model and recognizers [span_129](start_span)[span_129](end_span)`  
`analyzer = AnalyzerEngine()`

`text = "My name is John Doe and my email is john.doe@example.com"`

`# Scan the text for specific PII entities`  
`analyzer_results = analyzer.analyze(`  
    `text=text,`  
    `entities=, # Specify entities to find [span_130](start_span)[span_130](end_span)`  
    `language='en'`  
`)`

`# Returns:`  
`print(analyzer_results)`

*(Code synthesized from )*

#### **3.1.2 Step 2: Anonymizing PII with AnonymizerEngine**

The AnonymizerEngine takes the analyzer\_results from Step 1 and applies "operators" (e.g., replace, mask, encrypt) to the original text to create a sanitized version.  
**Code Example:**  
`from presidio_anonymizer import AnonymizerEngine`  
`from presidio_anonymizer.entities import OperatorConfig`

`anonymizer = AnonymizerEngine()`

`# Define an anonymization policy (policy)`  
`operators = {`  
    `# Replace any "PERSON" entity with "<REDACTED>"`  
    `"PERSON": OperatorConfig("replace", {"new_value": "<REDACTED>"}),`  
      
    `# "Mask" any "EMAIL_ADDRESS"`  
    `"EMAIL_ADDRESS": OperatorConfig("mask", {`  
        `"masking_char": "*",`   
        `"chars_to_mask": 10,`   
        `"from_end": False`  
    `})`  
`}`

`anonymized_result = anonymizer.anonymize(`  
    `text=text,`  
    `analyzer_results=analyzer_results, # Results from Step 1`  
    `operators=operators`  
`)`

`# Result: "My name is <REDACTED> and my email is j**********@example.com"`  
`print(anonymized_result.text)`

*(Code synthesized from )*

### **3.2 Architectural Pattern 1: Ingress Middleware via FastAPI Integration**

The most direct approach is to leverage the fact that Ray Serve applications (including those from build\_openai\_app) are FastAPI applications. One could add FastAPI middleware to intercept all incoming requests, apply the Presidio logic, and then forward the sanitized request to the model.  
While conceptually simple, this pattern has significant drawbacks. The build\_openai\_app function abstracts away the FastAPI app object, making middleware injection difficult and brittle. More importantly, this forces the PII-scanning logic (a CPU-intensive task) to run in the same process and on the same resource (potentially a valuable GPU node) as the ingress, creating a performance bottleneck.

### **3.3 Architectural Pattern 2 (Recommended): Ray Serve Deployment Composition**

A more robust, scalable, and "Ray-native" solution is to use **Deployment Composition**. This pattern treats the PII service and the vLLM service as two separate, linkable microservices, which can be scaled independently.  
This architecture consists of two deployments:

1. **PII\_Deployment:** A new, CPU-bound deployment that runs Presidio. It serves as the new application ingress.  
2. **vLLM\_Deployment:** The GPU-bound build\_openai\_app deployment from Part 1, which now becomes an internal, backend service.

**Implementation Concept:**  
`from ray import serve`  
`from ray.serve.handle import DeploymentHandle, DeploymentResponse`  
`from starlette.requests import Request`  
`from presidio_analyzer import AnalyzerEngine`  
`from presidio_anonymizer import AnonymizerEngine, OperatorConfig`

`# --- DEPLOYMENT 1: THE VLLM MODEL (from Part 1) ---`  
`# This app is built but NOT run directly. It has a name`  
`# so the PII service can find it.`  
`llm_app = build_openai_app({"llm_configs": [llm_config]})`  
`vllm_deployment = llm_app.options(name="vllm_service")`

`# --- DEPLOYMENT 2: THE PII "GUARDRAIL" (NEW INGRESS) ---`  
`@serve.deployment(`  
    `route_prefix="/v1", # This is now the main public endpoint`  
    `autoscaling_config={"min_replicas": 1, "max_replicas": 10} # Scales independently`  
`)`  
`class PIIService:`  
    `def __init__(self, vllm_handle: DeploymentHandle):`  
        `# Ray Serve injects a handle to the vLLM service [span_147](start_span)[span_147](end_span)`  
        `self.vllm_handle = vllm_handle`   
          
        `# Initialize Presidio engines`  
        `self.analyzer = AnalyzerEngine()`  
        `self.anonymizer = AnonymizerEngine()`  
        `self.operators = {`  
            `"DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED>"})`  
        `}`

    `async def __call__(self, http_request: Request):`  
        `# 1. Get request body`  
        `body = await http_request.json()`  
          
        `# 2. Find and Anonymize PII in prompts`  
        `# (This requires custom logic to iterate over the 'messages' list)`  
        `sanitized_body = self.anonymize_prompts(body)`  
          
        `# 3. Forward SANITIZED request to the vLLM deployment`  
        `# This call is non-blocking [span_148](start_span)[span_148](end_span)`  
        `vllm_response_future: DeploymentResponse = self.vllm_handle.remote(sanitized_body)`  
          
        `# 4. Get vLLM response`  
        `response_data = await vllm_response_future`  
          
        `# 5. (Optional) Anonymize the *output* from the LLM`  
        `final_response = self.anonymize_response(response_data)`  
          
        `return final_response`

    `def anonymize_prompts(self, body):`  
        `#... (Custom logic to loop 'messages', run Presidio)...`  
        `return body # Return the modified (sanitized) body`

    `def anonymize_response(self, response_data):`  
        `#... (Custom logic to scan LLM output and mask PII)...`  
        `return response_data`

`# --- BIND AND RUN THE COMPOSITION ---`  
`# 1. Bind the internal vLLM app (returns a handle)`  
`vllm_handle = vllm_deployment.bind()`

`# 2. Bind the PII service, INJECTING the vLLM handle [span_149](start_span)[span_149](end_span)`  
`app = PIIService.bind(vllm_handle)`

`# 3. Run the PII service as the main application`  
`serve.run(app)`

*(Architecture based on )*  
This composition pattern is vastly superior because the PII-scanning service (which is CPU-bound) and the vLLM inference service (which is GPU-bound) can be autoscaled *independently*. If the PII scanning becomes a bottleneck, Ray Serve can scale it up to 10 replicas without consuming any additional GPU resources.

### **3.4 Advanced Pattern: The "Bookend" for PII Deanonymization**

The architecture in 3.3 protects the LLM from PII, but it also degrades the user experience. A prompt of "My name is John" becomes "My name is \<REDACTED\>", and the LLM's response ("Hello, \<REDACTED\>") is unhelpful.  
The gold-standard solution is a "bookend" or "round-trip" pattern, which is an enhancement of the composition architecture:

1. **Ingress (Anonymize):** The PIIService intercepts the request. It uses Presidio to find PII and *encrypts* it or replaces it with a unique token (e.g., "John Doe" \-\> "ID-12345"). It stores this mapping (e.g., in a request-local dictionary or a fast K-V store like Redis).  
2. **Forward:** It sends the anonymized prompt ("...my name is ID-12345...") to the vLLM\_Deployment.  
3. **Response:** The LLM, which never sees the real PII, responds: "...hello ID-12345...".  
4. **Egress (Deanonymize):** The PIIService receives this response. It uses its stored map to perform the reverse substitution ("ID-12345" \-\> "John Doe").  
5. The end-user receives the final, coherent, and useful response: "...hello John Doe...".

This pattern is fully supported by Presidio, which includes an encrypt operator and a DeanonymizeEngine specifically for this purpose. This "bookend" architecture provides maximum data security and compliance (as the LLM never processes the raw PII) while simultaneously delivering maximum utility to the end-user.

### **3.5 Performance Impact of PII Masking**

PII scanning is not a "free" operation; it involves running an NLP model (spaCy) and complex regexes on every request, which adds latency. This cost must be managed, especially at scale.

* **Asynchronicity:** The \_\_call\_\_ method in the PIIService must be defined as async def to avoid blocking the server's event loop while performing I/O (like calling the vLLM handle) or CPU-bound work (like PII analysis).  
* **Batching:** The PIIService itself can leverage Ray Serve's @serve.batch decorator. This allows it to accumulate multiple incoming requests (e.g., 16 requests), analyze them as a batch (which is more efficient for Presidio), and then send a batch of 16 sanitized requests to the vLLM backend.  
* **Monitoring:** The performance of the PIIService must be monitored as a first-class component. If its serve\_deployment\_processing\_latency\_ms metric spikes, it indicates the PII-scanning step is the bottleneck, and its num\_replicas should be scaled up independently of the vLLM model.

## **Part 4: Conclusions and Recommendations**

This analysis leads to a set of clear, actionable recommendations for deploying vLLM in a production-grade, secure, and observable manner using Ray Serve.

1. **For Deployment:** Do not build custom deployment logic. The official ray.serve.llm library, specifically the LLMConfig and build\_openai\_app abstractions, is the state-of-the-art. This method provides a single point of configuration for model parameters, vLLM engine settings, and Ray Serve scaling, dramatically simplifying production deployments.  
2. **For Observability:** Standardize on the Prometheus/Grafana stack. Ray's native support for emitting Prometheus-formatted metrics from a central /metrics endpoint is the foundation for all monitoring. Focus on the "Golden Signals" of LLM serving—**TTFT, TPOT, and KV Cache Utilization**—not just generic GPU memory. Utilize the pre-built Grafana dashboards that Ray provides to accelerate setup. For enterprise integration, use the Datadog Agent's OpenMetrics support or Checkmk's Prometheus special agent. **Avoid the OpenTelemetry integration**, as it is an unmaintained Alpha feature.  
3. **For PII Security:** The recommended architecture is **Deployment Composition**. Create a dedicated, CPU-based "PII Guardrail" service using Microsoft Presidio, which acts as the ingress. This service should wrap the GPU-based vLLM deployment, which is injected using a DeploymentHandle. This pattern provides superior security and, critically, allows the PII-scanning logic and the LLM inference logic to be **scaled independently**, which is essential for managing performance and cost. For the best user experience and strongest security, implement the advanced **"bookend" (deanonymization)** pattern to ensure the LLM never processes raw PII, but the end-user still receives a coherent, readable response.

#### **Works cited**

1\. asprenger/ray\_vllm\_inference: A simple service that ... \- GitHub, https://github.com/asprenger/ray\_vllm\_inference 2\. Ray Serve: Scalable and Programmable Serving — Ray 2.51.0, https://docs.ray.io/en/latest/serve/index.html 3\. Serve a Large Language Model with vLLM — Ray 2.37.0, https://www.aidoczh.com/ray/serve/tutorials/vllm-example.html 4\. Serving LLMs — Ray 2.51.0, https://docs.ray.io/en/latest/serve/llm/index.html 5\. Deploy LLM with Ray Serve LLM — Ray 2.50.1 \- Ray Docs \- Ray.io, https://docs.ray.io/en/latest/ray-overview/examples/e2e-rag/notebooks/03\_Deploy\_LLM\_with\_Ray\_Serve.html 6\. Connecting to Ray Cluster and Launching vLLM with TP=8 and PP=2 in Deepseek R1 Mode on Kubernetes, https://discuss.vllm.ai/t/connecting-to-ray-cluster-and-launching-vllm-with-tp-8-and-pp-2-in-deepseek-r1-mode-on-kubernetes/1022 7\. Ray Serve Deepseek \- vLLM, https://docs.vllm.ai/en/v0.9.2/examples/online\_serving/ray\_serve\_deepseek.html 8\. Quickstart examples — Ray 2.51.0, https://docs.ray.io/en/latest/serve/llm/quick-start.html 9\. Running Very Large Language Models (VLLM) with Ray Serve | HPE AI Essentials Software 1.8.x Documentation, https://support.hpe.com/hpesc/public/docDisplay?docId=a00aie18hen\_us\&page=Tutorials/Tutorials/ray-vllm-example.html\&docLocale=en\_US 10\. Running Very Large Language Models (VLLM) with Ray Serve | HPE AI Essentials Software 1.9.x Documentation, https://support.hpe.com/hpesc/public/docDisplay?docId=a00aie19hen\_us\&page=Tutorials/Tutorials/ray-vllm-example.html\&docLocale=en\_US 11\. Ray Serve Latest version vLLM example requires code modification to work, https://discuss.ray.io/t/ray-serve-latest-version-vllm-example-requires-code-modification-to-work/20898 12\. Collecting and monitoring metrics — Ray 2.51.0, https://docs.ray.io/en/latest/cluster/metrics.html 13\. Monitoring & Debugging Ray Workloads: Ray Metrics \- Anyscale, https://www.anyscale.com/blog/monitoring-and-debugging-ray-workloads-ray-metrics 14\. Prometheus and Grafana \- vLLM, https://docs.vllm.ai/en/v0.7.3/getting\_started/examples/prometheus\_grafana.html 15\. Observability and monitoring — Ray 3.0.0.dev0 \- Ray Docs, https://docs.ray.io/en/master/serve/llm/user-guides/observability.html 16\. Metrics \- vLLM, https://docs.vllm.ai/en/latest/design/metrics.html 17\. Ray Monitor Not Connecting to Grafana and Prometheus, https://discuss.ray.io/t/ray-monitor-not-connecting-to-grafana-and-prometheus/10233 18\. Ray integration | New Relic Documentation, https://docs.newrelic.com/docs/infrastructure/host-integrations/host-integrations-list/ray-integration/ 19\. Using Prometheus and Grafana — Ray 2.51.0, https://docs.ray.io/en/latest/cluster/kubernetes/k8s-ecosystem/prometheus-grafana.html 20\. Enabling Metrics in the Ray Dashboard | HPE AI Essentials Software 1.8.x Documentation, https://support.hpe.com/hpesc/public/docDisplay?docId=a00aie18hen\_us\&page=Ray/enabling-metrics-in-ray-dashboard.html\&docLocale=en\_US 21\. Ray Grafana dashboards \- Anyscale Docs, https://docs.anyscale.com/monitoring/grafana-dashboards 22\. Ray Dashboard — Ray 2.51.0, https://docs.ray.io/en/latest/ray-observability/getting-started.html 23\. Configuring and Managing Ray Dashboard — Ray 2.50.1 \- Ray Docs, https://docs.ray.io/en/latest/cluster/configure-manage-dashboard.html 24\. Embedding Grafana visualizations into Ray Dashboard, https://discuss.ray.io/t/embedding-grafana-visualizations-into-ray-dashboard/12044 25\. Catalog of Check Plug-ins \- Checkmk, https://checkmk.com/integrations 26\. Integrating Prometheus \- Checkmk Docs, https://docs.checkmk.com/latest/en/monitoring\_prometheus.html 27\. Feature Pack 2 is out and comes with Prometheus-integration \- Checkmk, https://checkmk.com/blog/feature-pack-2-comes-with-prometheus-integration 28\. Ray \- Datadog Docs, https://docs.datadoghq.com/integrations/ray/ 29\. Monitor Ray applications and clusters with Datadog, https://www.datadoghq.com/blog/monitor-ray-with-datadog/ 30\. How to add Datadog annotation to Ray Pods, https://discuss.ray.io/t/how-to-add-datadog-annotation-to-ray-pods/15006 31\. Tracing — Ray 2.51.0, https://docs.ray.io/en/latest/ray-observability/user-guides/ray-tracing.html 32\. Key Concepts — Ray 2.50.1, https://docs.ray.io/en/latest/ray-observability/key-concepts.html 33\. Open telemetry integration with ray \- Ray Core, https://discuss.ray.io/t/open-telemetry-integration-with-ray/6401 34\. When Prompts Leak Secrets: The Hidden Risk in LLM Requests | Keysight Blogs, https://www.keysight.com/blogs/en/tech/nwvs/2025/08/04/pii-disclosure-in-user-request 35\. Understanding PII Leakage in Large Language Models: A Systematic Survey \- IJCAI, https://www.ijcai.org/proceedings/2025/1156.pdf 36\. Home \- Microsoft Presidio, https://microsoft.github.io/presidio/anonymizer/ 37\. presidio-analyzer · PyPI, https://pypi.org/project/presidio-analyzer/ 38\. Presidio Analyzer, https://microsoft.github.io/presidio/analyzer/ 39\. Identifying Personal Identifiable Information (PII) in Unstructured Data with Microsoft Presidio, https://www.statcan.gc.ca/en/data-science/network/identifying-personal-identifiable-information 40\. Getting Started with Microsoft's Presidio: A Step-by-Step Guide to Detecting and Anonymizing Personally Identifiable Information PII in Text \- MarkTechPost, https://www.marktechpost.com/2025/06/24/getting-started-with-microsofts-presidio-a-step-by-step-guide-to-detecting-and-anonymizing-personally-identifiable-information-pii-in-text/ 41\. Set Up FastAPI and HTTP \- Ray Serve, https://docs.ray.io/en/latest/serve/http-guide.html 42\. Ray Serve \+ FastAPI: The best of both worlds \- Anyscale, https://www.anyscale.com/blog/ray-serve-fastapi-the-best-of-both-worlds 43\. API built with serve and FastAPI only works thru curl or postman but not through another webapp \- Ray, https://discuss.ray.io/t/api-built-with-serve-and-fastapi-only-works-thru-curl-or-postman-but-not-through-another-webapp/3137 44\. Removing PII Data from OpenAI API Calls with Presidio and FastAPI, https://ploomber.io/blog/pii-openai/ 45\. Performance Tuning \- Ray Serve \- Ray Docs, https://docs.ray.io/en/latest/serve/advanced-guides/performance.html 46\. Understanding performance of Ray serve, https://discuss.ray.io/t/understanding-performance-of-ray-serve/13295 47\. Model composition \- Ray, https://ray-project.github.io/q4-2021-docs-hackathon/0.4/ray-ml/ray-serve/tutorials/model-composition/ 48\. Serving Models with Ray Serve \- Zencore Engineering \- Medium, https://medium.com/zencore/serving-models-with-ray-serve-8054fd5ac15e 49\. Multi-model composition with Ray Serve deployment graphs \- Anyscale, https://www.anyscale.com/blog/multi-model-composition-with-ray-serve-deployment-graphs 50\. Deploy Compositions of Models — Ray 2.50.1 \- Ray Docs, https://docs.ray.io/en/latest/serve/model\_composition.html 51\. Presidio in Action: Detecting and Securing PII in Text | by Lakmina Pramodya Gamage, https://blog.stackademic.com/presidio-in-action-detecting-and-securing-pii-in-text-451711e3c544 52\. Real-time PII Masking Deployment: Protect Sensitive Data Instantly \- hoop.dev, https://hoop.dev/blog/real-time-pii-masking-deployment-protect-sensitive-data-instantly/ 53\. Unmasking the Reality of PII Masking Models: Performance Gaps and the Call for Accountability \- arXiv, https://arxiv.org/pdf/2504.12308