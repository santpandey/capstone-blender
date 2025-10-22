#!/bin/bash
# EC2 User Data Script for 3D Asset Generator
# Ubuntu 22.04 LTS - Production Deployment

set -e  # Exit on error
set -x  # Print commands for debugging

# ============================================================================
# System Configuration
# ============================================================================

# Log all output
exec > >(tee /var/log/user-data.log)
exec 2>&1

echo "=========================================="
echo "Starting 3D Asset Generator Deployment"
echo "=========================================="
echo "Time: $(date)"
echo "Region: ${region}"
echo "Project: ${project_name}"

# Update system
echo "[1/10] Updating system packages..."
apt-get update -y
apt-get upgrade -y

# Install essential packages
echo "[2/10] Installing essential packages..."
apt-get install -y \
    curl \
    wget \
    git \
    unzip \
    python3-pip \
    python3-venv \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    awscli \
    jq

# ============================================================================
# Install Docker
# ============================================================================

echo "[3/10] Installing Docker..."
apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Add ubuntu user to docker group
usermod -aG docker ubuntu

echo "Docker version: $(docker --version)"

# ============================================================================
# Install Blender (Linux Version)
# ============================================================================

echo "[4/10] Installing Blender..."
cd /opt
wget -q https://download.blender.org/release/Blender4.0/blender-4.0.2-linux-x64.tar.xz
tar -xf blender-4.0.2-linux-x64.tar.xz
mv blender-4.0.2-linux-x64 blender
rm blender-4.0.2-linux-x64.tar.xz

# Create symlink for easy access
ln -sf /opt/blender/blender /usr/local/bin/blender

# Verify Blender installation
blender --version

echo "✅ Blender installed at: /opt/blender/blender"

# ============================================================================
# Install Python UV
# ============================================================================

echo "[5/10] Installing UV (Python package manager)..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="/root/.cargo/bin:$PATH"

# Make uv available system-wide
ln -sf /root/.cargo/bin/uv /usr/local/bin/uv

uv --version

# ============================================================================
# Setup Application Directory
# ============================================================================

echo "[6/10] Setting up application directory..."
mkdir -p /app
cd /app

# Clone application repository
echo "Cloning repository: ${git_repo_url}"
git clone -b ${git_branch} ${git_repo_url} .

# Set ownership
chown -R ubuntu:ubuntu /app

# ============================================================================
# Retrieve Secrets from AWS Secrets Manager
# ============================================================================

echo "[7/10] Retrieving secrets from AWS Secrets Manager..."

# Get Gemini API Key
SECRET_JSON=$(aws secretsmanager get-secret-value \
    --secret-id ${gemini_secret_name} \
    --region ${region} \
    --query SecretString \
    --output text)

GEMINI_API_KEY=$(echo $SECRET_JSON | jq -r '.api_key // .GEMINI_API_KEY')

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ ERROR: Failed to retrieve Gemini API Key"
    exit 1
fi

echo "✅ Successfully retrieved secrets"

# ============================================================================
# Create Environment Configuration
# ============================================================================

echo "[8/10] Creating environment configuration..."

cat > /app/.env << EOF
# Environment Configuration
ENVIRONMENT=production
AWS_REGION=${region}
AWS_EXECUTION_ENV=EC2

# Blender Configuration
BLENDER_PATH=/opt/blender/blender
BLENDER_DOCKER=false
EXECUTION_MODE=local

# API Keys (from AWS Secrets Manager)
GEMINI_API_KEY=$GEMINI_API_KEY

# Application Settings
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# Paths
BASE_DIR=/app
SCRIPTS_DIR=/app/generated_scripts
MODELS_DIR=/app/generated_models
EOF

chmod 600 /app/.env
chown ubuntu:ubuntu /app/.env

echo "✅ Environment configuration created"

# ============================================================================
# Install Python Dependencies
# ============================================================================

echo "[9/10] Installing Python dependencies with UV..."
cd /app

# Install dependencies using uv
su - ubuntu -c "cd /app && /usr/local/bin/uv sync"

# Create required directories
mkdir -p /app/generated_scripts
mkdir -p /app/generated_models
mkdir -p /app/logs

chown -R ubuntu:ubuntu /app/generated_scripts
chown -R ubuntu:ubuntu /app/generated_models
chown -R ubuntu:ubuntu /app/logs

echo "✅ Python dependencies installed"

# ============================================================================
# Setup Systemd Service
# ============================================================================

echo "[10/10] Setting up systemd service..."

cat > /etc/systemd/system/${project_name}.service << 'SERVICEEOF'
[Unit]
Description=3D Asset Generator Application
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/app
Environment="PATH=/usr/local/bin:/usr/bin:/bin:/root/.cargo/bin"
EnvironmentFile=/app/.env
ExecStart=/usr/local/bin/uv run python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10
StandardOutput=append:/app/logs/app.log
StandardError=append:/app/logs/error.log

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Reload systemd and start service
systemctl daemon-reload
systemctl enable ${project_name}.service
systemctl start ${project_name}.service

echo "✅ Service started"

# ============================================================================
# Setup CloudWatch Logs Agent (Optional)
# ============================================================================

echo "Setting up CloudWatch Logs..."

# Install CloudWatch agent
wget -q https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i -E ./amazon-cloudwatch-agent.deb
rm amazon-cloudwatch-agent.deb

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'CWEOF'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/app/logs/app.log",
            "log_group_name": "/aws/ec2/${project_name}",
            "log_stream_name": "{instance_id}/app.log"
          },
          {
            "file_path": "/app/logs/error.log",
            "log_group_name": "/aws/ec2/${project_name}",
            "log_stream_name": "{instance_id}/error.log"
          },
          {
            "file_path": "/var/log/user-data.log",
            "log_group_name": "/aws/ec2/${project_name}",
            "log_stream_name": "{instance_id}/user-data.log"
          }
        ]
      }
    }
  }
}
CWEOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -s \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

echo "✅ CloudWatch Logs configured"

# ============================================================================
# Setup Log Rotation
# ============================================================================

cat > /etc/logrotate.d/${project_name} << 'LOGEOF'
/app/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 ubuntu ubuntu
    postrotate
        systemctl reload ${project_name}.service > /dev/null 2>&1 || true
    endscript
}
LOGEOF

# ============================================================================
# Health Check
# ============================================================================

echo "Waiting for application to start..."
sleep 30

# Check if application is running
if systemctl is-active --quiet ${project_name}.service; then
    echo "✅ Application service is running"
    
    # Test health endpoint
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Health check passed"
    else
        echo "⚠️ Health check failed - application may still be starting"
    fi
else
    echo "❌ Application service failed to start"
    systemctl status ${project_name}.service
    exit 1
fi

# ============================================================================
# Completion
# ============================================================================

echo "=========================================="
echo "✅ Deployment completed successfully!"
echo "=========================================="
echo "Application URL: http://localhost:8000"
echo "Logs: /app/logs/"
echo "Service: systemctl status ${project_name}"
echo "=========================================="

# Signal successful completion to CloudFormation (if used)
# /opt/aws/bin/cfn-signal -e $? --stack <stack-name> --resource <resource> --region ${region}
