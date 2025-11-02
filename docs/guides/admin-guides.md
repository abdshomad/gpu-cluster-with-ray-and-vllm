# Administrator Guide - GPU Cluster Platform

This guide is for system administrators responsible for deploying, managing, and maintaining the GPU Cluster Platform infrastructure.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Initial Setup](#initial-setup)
4. [Deployment](#deployment)
5. [Service Management](#service-management)
6. [Container Management](#container-management)
7. [Resource Management](#resource-management)
8. [Security](#security)
9. [Backup and Recovery](#backup-and-recovery)
10. [Upgrades and Updates](#upgrades-and-updates)
11. [Multi-Node Deployment](#multi-node-deployment)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 22.04 recommended)
- **Docker**: Version 20.10 or later
- **Docker Compose**: Version 2.0 or later
- **NVIDIA GPU**: CUDA-compatible GPU (L4, A100, H100, T4, V100, A10, A10G)
- **NVIDIA Drivers**: Latest stable drivers for your GPU
- **NVIDIA Container Toolkit**: `nvidia-docker2` package
- **Disk Space**: At least 50GB free space (for models and containers)
- **Memory**: 32GB+ RAM recommended
- **Network**: Ports available for services (configurable)

### Software Installation

#### Install Docker and Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose (v2)
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

#### Install NVIDIA Container Toolkit

```bash
# Add NVIDIA package repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-container-toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.4.0-runtime-ubuntu22.04 nvidia-smi
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/abdshomad/gpu-cluster-with-ray-and-vllm.git
cd gpu-cluster-with-ray-and-vllm
```

### Verify GPU Availability

```bash
# Check GPU detection
nvidia-smi

# Verify Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.4.0-runtime-ubuntu22.04 nvidia-smi
```

---

## Initial Setup

### 1. Create Environment Files

```bash
# Create .env from example (if exists)
cp .env.example .env

# Or create .env manually
cat > .env << EOF
# Model Configuration
MODEL_ID=Qwen/Qwen2.5-32B-Instruct
TENSOR_PARALLEL_SIZE=4
ACCELERATOR_TYPE=L4

# Scaling Configuration
MIN_REPLICAS=1
MAX_REPLICAS=4
TARGET_ONGOING_REQUESTS=32
MAX_ONGOING_REQUESTS=64

# Port Configuration
RAY_API_PORT=18000
RAY_DASHBOARD_PORT=18265
NGINX_HTTP_PORT=18080
NGINX_HTTPS_PORT=18443

# Ray Configuration
RAY_METRICS_EXPORT_PORT=8080
ROUTE_PREFIX=/v1

# vLLM Engine Configuration
MAX_NUM_BATCHED_TOKENS=8192
MAX_MODEL_LEN=8192
MAX_NUM_SEQS=64
TRUST_REMOTE_CODE=true
ENABLE_PREFIX_CACHING=true
EOF

# Create .secrets file
cat > .secrets << EOF
# Secrets file for GPU Cluster Platform
# This file is gitignored - never commit it

# HuggingFace Token (required for private models)
HUGGINGFACE_TOKEN=your_token_here
EOF

# Secure the secrets file
chmod 600 .secrets
```

### 2. Configure Ports

Check for port conflicts and adjust if needed:

```bash
# Check port availability
lsof -i :18080  # Nginx HTTP
lsof -i :18000  # Ray API
lsof -i :18265  # Ray Dashboard
lsof -i :19090  # Prometheus
lsof -i :13000  # Grafana

# Update .env if ports are in use
```

### 3. Verify Configuration

```bash
# Export environment variables for verification
export $(cat .env | grep -v '^#' | xargs)

# Verify configuration
docker compose -f docker/docker-compose.yml config
```

---

## Deployment

### Build and Start Services

```bash
# Navigate to docker directory
cd docker

# Build images (first time or after changes)
docker compose build

# Start services in detached mode
docker compose up -d

# View logs
docker compose logs -f
```

### Verify Deployment

```bash
# Check container status
docker compose ps

# Check Ray Serve logs
docker compose logs ray-serve

# Check Nginx logs
docker compose logs gpu-cluster-nginx-proxy

# Test API endpoint
curl http://localhost:18080/v1/models

# Test Ray Dashboard
curl http://localhost:18265
```

### Health Checks

```bash
# Service health
curl http://localhost:18080/health

# Ray cluster status
docker exec ray-serve ray status

# GPU availability in container
docker exec ray-serve nvidia-smi
```

---

## Service Management

### Start Services

```bash
cd docker
docker compose up -d
```

### Stop Services

```bash
cd docker
docker compose down
```

### Restart Services

```bash
cd docker
docker compose restart

# Restart specific service
docker compose restart ray-serve
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f ray-serve
docker compose logs -f gpu-cluster-nginx-proxy

# Last N lines
docker compose logs --tail=100 ray-serve
```

### Service Status

```bash
# Container status
docker compose ps

# Resource usage
docker stats

# Ray cluster status
docker exec ray-serve ray status
```

---

## Container Management

### Container Operations

```bash
# List containers
docker ps

# Inspect container
docker inspect ray-serve

# Execute commands in container
docker exec -it ray-serve bash
docker exec ray-serve nvidia-smi

# View container logs
docker logs ray-serve
docker logs gpu-cluster-nginx-proxy

# Remove stopped containers
docker container prune
```

### Image Management

```bash
# List images
docker images

# Remove unused images
docker image prune

# Remove specific image
docker rmi gpu-cluster-ray-serve

# Rebuild without cache
docker compose build --no-cache
```

### Volume Management

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect ray_metrics

# Remove unused volumes
docker volume prune

# Backup volume
docker run --rm -v ray_metrics:/data -v $(pwd):/backup \
    ubuntu tar czf /backup/ray_metrics_backup.tar.gz /data
```

---

## Resource Management

### GPU Resource Allocation

Verify GPU allocation matches configuration:

```bash
# Check available GPUs
nvidia-smi

# Verify GPUs in container
docker exec ray-serve nvidia-smi

# Check Ray cluster resources
docker exec ray-serve python -c "import ray; ray.init(); print(ray.cluster_resources())"
```

### Memory Management

Monitor memory usage:

```bash
# Container memory
docker stats

# System memory
free -h

# GPU memory
nvidia-smi

# Ray memory usage
docker exec ray-serve ray status
```

### Disk Space Management

```bash
# Check disk usage
df -h

# Docker disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

### Network Configuration

```bash
# List networks
docker network ls

# Inspect network
docker network inspect gpu-cluster-with-ray-and-vllm_default

# Test connectivity
docker exec ray-serve ping gpu-cluster-nginx-proxy
```

---

## Security

### Secrets Management

1. **Never commit `.secrets` file**
   ```bash
   # Verify .secrets is in .gitignore
   git check-ignore .secrets
   ```

2. **Secure file permissions**
   ```bash
   chmod 600 .secrets
   ```

3. **Rotate secrets regularly**
   ```bash
   # Update HuggingFace token in .secrets
   # Restart services after updating
   docker compose restart
   ```

### Network Security

1. **Firewall Configuration**
   ```bash
   # Allow only necessary ports
   sudo ufw allow 18080/tcp  # Nginx HTTP
   sudo ufw allow 18265/tcp  # Ray Dashboard (if needed externally)
   sudo ufw enable
   ```

2. **Internal Network Isolation**
   - Containers communicate on internal Docker network
   - Only expose necessary ports to host

3. **SSL/TLS Configuration** (Future)
   - Configure SSL certificates in Nginx
   - Enable HTTPS on port 443/18443

### Access Control

1. **Ray Dashboard Access**
   - By default, dashboard is accessible without authentication
   - Consider adding authentication for production

2. **API Authentication** (Future)
   - Implement API key authentication
   - Use rate limiting

---

## Backup and Recovery

### Configuration Backup

```bash
# Backup configuration files
tar czf config_backup_$(date +%Y%m%d).tar.gz \
    .env .secrets docker/docker-compose.yml
```

### Volume Backup

```bash
# Backup Ray metrics volume
docker run --rm -v ray_metrics:/data -v $(pwd):/backup \
    ubuntu tar czf /backup/ray_metrics_$(date +%Y%m%d).tar.gz /data
```

### Recovery Procedure

```bash
# Stop services
docker compose down

# Restore configuration
tar xzf config_backup_YYYYMMDD.tar.gz

# Restore volumes (if needed)
docker run --rm -v ray_metrics:/data -v $(pwd):/backup \
    ubuntu tar xzf /backup/ray_metrics_YYYYMMDD.tar.gz -C /

# Restart services
docker compose up -d
```

---

## Upgrades and Updates

### Update Configuration

1. **Update .env file** with new settings
2. **Restart services** to apply changes
   ```bash
   docker compose restart
   ```

### Update Code/Images

```bash
# Pull latest code
git pull

# Rebuild images
docker compose build

# Restart services
docker compose up -d
```

### Model Updates

```bash
# Update MODEL_ID in .env
# Restart Ray Serve service
docker compose restart ray-serve

# Monitor model loading
docker compose logs -f ray-serve
```

### Dependency Updates

```bash
# Update requirements.txt
# Rebuild images
docker compose build --no-cache

# Restart services
docker compose up -d
```

---

## Multi-Node Deployment

### Overview

For multi-node deployments, additional configuration is required:

1. **Ray Cluster Setup**: Configure Ray head and worker nodes
2. **Network Configuration**: Ensure nodes can communicate
3. **Shared Storage**: Model storage accessible to all nodes

### Configuration Steps

1. **Configure Ray Head Node**:
   ```bash
   # On head node
   ray start --head --dashboard-host=0.0.0.0
   ```

2. **Join Worker Nodes**:
   ```bash
   # On worker nodes
   ray start --address=<head-node-ip>:10001
   ```

3. **Update .env**:
   ```bash
   RAY_HEAD_HOST=<head-node-ip>
   ```

### Load Balancing

- Configure Nginx upstream for multiple Ray nodes
- Use DNS or service discovery for node discovery

---

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check logs
docker compose logs

# Verify configuration
docker compose config

# Check port conflicts
lsof -i :18080
```

#### GPU Not Detected

```bash
# Verify NVIDIA runtime
docker info | grep -i runtime

# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.4.0-runtime-ubuntu22.04 nvidia-smi

# Check accelerator type in .env matches GPU
```

#### Out of Memory

```bash
# Check memory usage
docker stats
nvidia-smi

# Reduce tensor parallel size or model size
# Edit .env: TENSOR_PARALLEL_SIZE=2
```

#### Port Conflicts

```bash
# Find process using port
lsof -i :18080

# Update .env with different ports
# Restart services
```

### Debug Mode

```bash
# Run services in foreground for debugging
docker compose up

# Interactive shell in container
docker exec -it ray-serve bash
docker exec -it gpu-cluster-nginx-proxy sh
```

### Log Analysis

```bash
# Search logs for errors
docker compose logs | grep -i error

# Follow logs in real-time
docker compose logs -f

# Export logs
docker compose logs > deployment.log
```

### Reset Deployment

```bash
# Stop and remove containers
docker compose down

# Remove volumes (WARNING: Deletes data)
docker compose down -v

# Rebuild from scratch
docker compose build --no-cache
docker compose up -d
```

---

## Best Practices

### 1. Resource Monitoring

- Monitor GPU utilization regularly
- Track memory and disk usage
- Set up alerts for resource exhaustion

### 2. Log Management

- Rotate logs regularly
- Centralize logs for analysis
- Monitor for errors and warnings

### 3. Configuration Management

- Version control all configuration (except secrets)
- Document all changes
- Test changes in staging first

### 4. Backup Strategy

- Regular configuration backups
- Periodic volume backups
- Test recovery procedures

### 5. Security

- Keep secrets secure
- Update dependencies regularly
- Monitor for security vulnerabilities

### 6. Documentation

- Document all custom configurations
- Keep deployment notes
- Update runbooks

---

## Additional Resources

- [Troubleshooting Guide](../trouble-shooting.md) - Common errors and solutions
- [vLLM Ray Serve Guide](../vllm-ray-serve-guide.md) - Technical deployment details
- [Docker Documentation](https://docs.docker.com/)
- [Ray Documentation](https://docs.ray.io/)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)

---

## Support

For issues:
1. Check [Troubleshooting Guide](../trouble-shooting.md)
2. Review service logs
3. Consult Ray Dashboard for cluster status
4. Check GPU availability with `nvidia-smi`

