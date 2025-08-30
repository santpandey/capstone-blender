# Multi-stage Docker build for 3D Asset Generator
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    xz-utils \
    curl \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libgl1-mesa-glx \
    libglu1-mesa \
    libxi6 \
    libxrandr2 \
    libxss1 \
    libxinerama1 \
    libxcursor1 \
    libxcomposite1 \
    libasound2 \
    libpulse0 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Download and install Blender
WORKDIR /opt
RUN wget -q https://download.blender.org/release/Blender4.0/blender-4.0.2-linux-x64.tar.xz \
    && tar -xf blender-4.0.2-linux-x64.tar.xz \
    && mv blender-4.0.2-linux-x64 blender \
    && rm blender-4.0.2-linux-x64.tar.xz

# Add Blender to PATH
ENV PATH="/opt/blender:${PATH}"
ENV BLENDER_DOCKER=true

# Set working directory
WORKDIR /app

# Copy Python dependencies
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --extra mcp --extra vector --extra web

# Copy application code
COPY . .

# Create directories for generated content
RUN mkdir -p generated_models generated_scripts

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application using uv
CMD ["uv", "run", "python", "backend/main.py"]
