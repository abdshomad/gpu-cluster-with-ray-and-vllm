# Dockerfile for vLLM + Ray Serve GPU Cluster Platform
# Base image: NVIDIA CUDA runtime with Ubuntu 22.04
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    curl \
    wget \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /app

# Create virtual environment using uv
RUN uv venv /app/.venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy requirements file
COPY requirements.txt /app/

# Install Python dependencies using uv
RUN uv pip install --system -r requirements.txt

# Copy deployment script
COPY src/ /app/src/

# Expose ports (configurable via environment variables, defaults shown)
# Ray API port (default: 8000)
EXPOSE 8000
# Ray Dashboard port (default: 8265)
EXPOSE 8265

# Set entrypoint to run deployment script using uv run python
ENTRYPOINT ["uv", "run", "python", "src/deploy.py"]

