# 🚀 Deployment Guide - 3D Asset Generator

Complete deployment guide for local development, Docker, and AWS production environments.

## 📋 Prerequisites

### Local Development
- Python 3.11+
- uv package manager
- Git

### Docker Deployment
- Docker 20.10+
- Docker Compose 2.0+

### AWS Deployment
- AWS CLI configured
- Terraform 1.0+
- Domain name (optional)

## 🏠 Local Development

### 1. Clone and Setup
```bash
git clone <repository-url>
cd capstone

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/Mac
# or
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Install dependencies
uv sync --extra web --extra mcp --extra vector
```

### 2. Start Services
```bash
# Terminal 1: Backend
cd backend
uv run python main.py

# Terminal 2: Frontend
cd front_end
python -m http.server 3000
```

### 3. Access Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health Check: http://localhost:8000/health

## 🐳 Docker Deployment

### 1. Quick Start
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 2. Build and Deploy
```bash
# Build images
docker-compose build

# Start in background
docker-compose up -d

# Check status
docker-compose ps
```

### 3. Access Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health Check: http://localhost:8000/health

### 4. Troubleshooting
```bash
# View logs
docker-compose logs backend
docker-compose logs frontend

# Restart services
docker-compose restart

# Clean rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## ☁️ AWS Production Deployment

### 1. Prerequisites Setup
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure

# Install Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### 2. Deploy Infrastructure
```bash
cd aws
chmod +x deploy.sh

# Deploy with custom domain
./deploy.sh your-domain.com

# Or deploy with default ALB DNS
./deploy.sh
```

### 3. Deployment Process
The deployment script will:
1. ✅ Initialize Terraform
2. ✅ Plan infrastructure changes
3. ✅ Create VPC with public/private subnets
4. ✅ Deploy Application Load Balancer
5. ✅ Launch EC2 instances with Auto Scaling
6. ✅ Configure security groups
7. ✅ Setup Route 53 (if domain provided)

### 4. Post-Deployment
```bash
# Get deployment outputs
cd terraform
terraform output

# Check application health
curl http://<alb-dns>/health

# View EC2 instances
aws ec2 describe-instances --filters "Name=tag:Name,Values=3d-generator-instance"
```

### 5. SSL Certificate (Optional)
```bash
# Request SSL certificate
aws acm request-certificate \
    --domain-name your-domain.com \
    --validation-method DNS

# Update ALB listener for HTTPS
# (Manual step - update Terraform configuration)
```

## 🔧 Configuration

### Environment Variables
```bash
# Backend configuration
BLENDER_DOCKER=true          # Enable Docker mode
AWS_REGION=us-east-1         # AWS region
ENVIRONMENT=production       # Environment name

# Optional: API keys
GEMINI_API_KEY=your-key      # For LLM features
```

### Resource Requirements

#### Local Development
- CPU: 2+ cores
- RAM: 4GB minimum, 8GB recommended
- Disk: 2GB free space

#### Docker Deployment
- CPU: 2+ cores
- RAM: 8GB minimum, 16GB recommended
- Disk: 5GB free space

#### AWS Production
- Instance Type: t3.large (2 vCPU, 8GB RAM)
- Storage: 20GB EBS volume
- Network: VPC with public/private subnets

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# Application health
curl http://localhost:8000/health

# System metrics
curl http://localhost:8000/metrics

# Docker container status
docker-compose ps
```

### Log Management
```bash
# View application logs
docker-compose logs -f backend

# AWS CloudWatch (production)
aws logs describe-log-groups
aws logs tail /aws/ec2/3d-generator
```

### Backup Strategy
```bash
# Backup generated models
tar -czf models-backup-$(date +%Y%m%d).tar.gz generated_models/

# Database backup (if applicable)
# Configure automated S3 backups for production
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Blender Not Found
```bash
# Check Blender installation
blender --version

# Docker: Rebuild with Blender
docker-compose build --no-cache
```

#### 2. Memory Issues
```bash
# Check memory usage
docker stats

# Increase Docker memory limits
# Edit docker-compose.yml memory settings
```

#### 3. Port Conflicts
```bash
# Check port usage
netstat -tulpn | grep :8000

# Kill conflicting processes
sudo kill -9 $(lsof -t -i:8000)
```

#### 4. AWS Deployment Issues
```bash
# Check Terraform state
cd terraform
terraform plan

# View AWS resources
aws ec2 describe-instances
aws elbv2 describe-load-balancers
```

### Performance Optimization

#### 1. Backend Scaling
```bash
# Increase worker processes
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

#### 2. AWS Auto Scaling
```bash
# Update Auto Scaling Group
aws autoscaling update-auto-scaling-group \
    --auto-scaling-group-name 3d-generator-asg \
    --desired-capacity 2
```

#### 3. Caching
- Implement Redis for job status caching
- Use CloudFront for static asset delivery
- Enable EBS optimization for faster I/O

## 🔄 Updates & Maintenance

### Application Updates
```bash
# Pull latest code
git pull origin main

# Docker: Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# AWS: Update deployment
cd aws
./deploy.sh
```

### Infrastructure Updates
```bash
# Update Terraform configuration
cd terraform
terraform plan
terraform apply
```

### Security Updates
```bash
# Update base images
docker-compose build --no-cache

# Update system packages (AWS)
# Handled automatically by user data script
```

## 📞 Support

### Logs Location
- Local: Console output
- Docker: `docker-compose logs`
- AWS: CloudWatch Logs

### Key Metrics
- Generation success rate: `/metrics` endpoint
- Response times: Application logs
- Resource usage: CloudWatch/Docker stats

### Emergency Procedures
```bash
# Stop all services immediately
docker-compose down

# AWS: Terminate all instances
aws autoscaling update-auto-scaling-group \
    --auto-scaling-group-name 3d-generator-asg \
    --desired-capacity 0

# Destroy AWS infrastructure
cd aws
./destroy.sh
```
