# 🚀 AWS Deployment Checklist

## 📋 Pre-Deployment Tasks

### 1. Code Changes Required

#### ✅ Update `blender_executor.py`
- [x] Add cross-platform path detection
- [x] Support Windows/Linux/Docker environments
- [x] Use environment variables for configuration
- **Status**: ✅ COMPLETED

#### ✅ Create `utils/aws_secrets.py`
- [x] AWS Secrets Manager integration
- [x] Fallback to environment variables for local dev
- [x] Helper functions for retrieving secrets
- **Status**: ✅ COMPLETED

#### ⏳ Update `backend/main.py`
- [ ] Import and use `aws_secrets.py`
- [ ] Replace direct `os.getenv()` calls with `load_secrets()`
- [ ] Test locally with `.env` file
- **Status**: TODO

```python
# Add to backend/main.py
from utils.aws_secrets import get_gemini_api_key

# Replace:
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# With:
try:
    GEMINI_API_KEY = get_gemini_api_key()
except Exception as e:
    logger.error(f"Failed to load secrets: {e}")
    raise
```

### 2. AWS Infrastructure Files

#### ✅ Files to KEEP (Updated)
- [x] `aws/terraform/variables.tf` - NEW (centralized config)
- [x] `aws/terraform/main_simplified.tf` - NEW (single EC2, no ASG)
- [x] `aws/terraform/user_data_updated.sh` - NEW (Ubuntu, proper setup)
- [x] `aws/terraform/secrets_updated.tf` - NEW (Secrets Manager)
- [x] `aws/deploy_updated.sh` - NEW (deployment automation)
- [x] `aws/destroy.sh` - KEEP (teardown script)

#### ❌ Files to REMOVE (Obsolete)
- [ ] `aws/terraform/sagemaker.tf` - REMOVE (not using SageMaker)
- [ ] `aws/terraform/main.tf` - REPLACE with `main_simplified.tf`
- [ ] `aws/terraform/user_data.sh` - REPLACE with `user_data_updated.sh`
- [ ] `aws/start-aws.sh` - REMOVE (use terraform)
- [ ] `aws/stop-aws.sh` - REMOVE (use terraform)
- [ ] `aws/deploy.sh` - REPLACE with `deploy_updated.sh`

### 3. Git Repository Setup

#### Update `.gitignore`
```gitignore
# AWS
aws/terraform/.terraform/
aws/terraform/terraform.tfstate*
aws/terraform/tfplan
aws/deployment_info.txt

# Secrets
.env
.env.local
.env.production
**/secrets.tf
```

#### Push Code to GitHub
```bash
git add .
git commit -m "AWS deployment configuration"
git push origin main
```

#### Update `variables.tf` with your repo URL
```hcl
variable "git_repo_url" {
  default     = "https://github.com/YOUR_USERNAME/capstone-blender.git"
}
```

---

## 🔐 Secrets Management

### Create AWS Secret (Before Deployment)

**Option 1: AWS CLI**
```bash
aws secretsmanager create-secret \
    --name 3d-generator/prod/gemini-api-key \
    --description "Gemini API Key for 3D Asset Generator" \
    --secret-string '{"api_key":"YOUR_ACTUAL_GEMINI_KEY_HERE"}' \
    --region us-east-1
```

**Option 2: AWS Console**
1. Go to AWS Secrets Manager
2. Click "Store a new secret"
3. Choose "Other type of secret"
4. Key: `api_key`, Value: `YOUR_GEMINI_KEY`
5. Secret name: `3d-generator/prod/gemini-api-key`

**Verify Secret**
```bash
aws secretsmanager get-secret-value \
    --secret-id 3d-generator/prod/gemini-api-key \
    --region us-east-1
```

---

## 🏗️ Deployment Steps

### Step 1: Prerequisites
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output (json)
```

### Step 2: Verify Setup
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check Terraform
terraform version

# Check if secret exists
aws secretsmanager describe-secret \
    --secret-id 3d-generator/prod/gemini-api-key \
    --region us-east-1
```

### Step 3: Update Terraform Files
```bash
cd aws/terraform

# Rename new files
mv main_simplified.tf main.tf
mv user_data_updated.sh user_data.sh
mv secrets_updated.tf secrets.tf

# Remove old files
rm -f sagemaker.tf

# Update git repo URL in variables.tf
nano variables.tf  # Update git_repo_url
```

### Step 4: Initialize Terraform
```bash
cd aws/terraform
terraform init
```

### Step 5: Plan Deployment
```bash
terraform plan -out=tfplan

# Review the plan carefully
# Expected resources:
# - VPC, Subnets, IGW, NAT Gateway
# - ALB, Target Group
# - EC2 Instance
# - Security Groups
# - IAM Roles
# - Secrets Manager
```

### Step 6: Deploy Infrastructure
```bash
terraform apply tfplan

# This will take 5-10 minutes
# Watch for any errors
```

### Step 7: Get Deployment Info
```bash
# Get ALB DNS name
terraform output alb_dns_name

# Get full URL
terraform output alb_url

# Example output:
# http://3d-generator-alb-123456789.us-east-1.elb.amazonaws.com
```

### Step 8: Verify Deployment
```bash
# Wait 2-3 minutes for instance to initialize
sleep 180

# Test health endpoint
curl http://YOUR_ALB_DNS/health

# Expected response:
# {"status":"healthy","version":"1.0.0"}
```

---

## ✅ Post-Deployment Verification

### 1. Check Application Health
```bash
ALB_DNS=$(terraform output -raw alb_dns_name)
curl http://$ALB_DNS/health
```

### 2. View CloudWatch Logs
```bash
# Application logs
aws logs tail /aws/ec2/3d-generator --follow --region us-east-1

# User data logs (startup script)
aws logs tail /aws/ec2/3d-generator --follow \
    --filter-pattern "user-data" \
    --region us-east-1
```

### 3. Connect to EC2 Instance (if needed)
```bash
# Get instance ID
INSTANCE_ID=$(terraform output -raw ec2_instance_id)

# Connect via SSM Session Manager (no SSH key needed)
aws ssm start-session --target $INSTANCE_ID --region us-east-1

# Or via SSH (if you added a key pair)
# Note: Instance is in private subnet, need bastion host
```

### 4. Test Application
```bash
# Generate a test asset
curl -X POST http://$ALB_DNS/generate \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Create a blue sphere"}'

# Response will include job_id
# {"job_id": "abc-123", "status": "processing"}

# Check status
curl http://$ALB_DNS/status/abc-123

# Download model when ready
curl http://$ALB_DNS/download/abc-123 -o model.glb
```

---

## 📊 Monitoring & Maintenance

### CloudWatch Metrics
```bash
# View CPU utilization
aws cloudwatch get-metric-statistics \
    --namespace AWS/EC2 \
    --metric-name CPUUtilization \
    --dimensions Name=InstanceId,Value=$INSTANCE_ID \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-02T00:00:00Z \
    --period 3600 \
    --statistics Average
```

### Application Logs
```bash
# Real-time logs
aws logs tail /aws/ec2/3d-generator --follow

# Filter errors
aws logs filter-pattern /aws/ec2/3d-generator \
    --filter-pattern "ERROR"

# Export logs to S3 (for long-term storage)
aws logs create-export-task \
    --log-group-name /aws/ec2/3d-generator \
    --from 1609459200000 \
    --to 1609545600000 \
    --destination s3-bucket-name \
    --destination-prefix logs/
```

### Cost Monitoring
```bash
# Check current month costs
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=DIMENSION,Key=SERVICE
```

---

## 🔄 Updates & Maintenance

### Update Application Code
```bash
# SSH into instance
aws ssm start-session --target $INSTANCE_ID

# Pull latest code
cd /app
sudo -u ubuntu git pull origin main

# Restart application
sudo systemctl restart 3d-generator

# Check status
sudo systemctl status 3d-generator
```

### Update Infrastructure
```bash
cd aws/terraform

# Make changes to .tf files
nano main.tf

# Plan changes
terraform plan

# Apply changes
terraform apply
```

### Rotate Secrets
```bash
# Update Gemini API key
aws secretsmanager update-secret \
    --secret-id 3d-generator/prod/gemini-api-key \
    --secret-string '{"api_key":"NEW_KEY_HERE"}' \
    --region us-east-1

# Restart application to pick up new key
aws ssm send-command \
    --instance-ids $INSTANCE_ID \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=["systemctl restart 3d-generator"]'
```

---

## 🚨 Troubleshooting

### Application Not Responding
```bash
# Check instance status
aws ec2 describe-instance-status --instance-ids $INSTANCE_ID

# Check service status
aws ssm send-command \
    --instance-ids $INSTANCE_ID \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=["systemctl status 3d-generator"]'

# View recent logs
aws logs tail /aws/ec2/3d-generator --since 10m
```

### Health Check Failing
```bash
# Check target group health
aws elbv2 describe-target-health \
    --target-group-arn $(terraform output -raw target_group_arn)

# Common issues:
# 1. Security group blocking traffic
# 2. Application not listening on correct port
# 3. Health check path incorrect
```

### High Costs
```bash
# Check NAT Gateway data transfer (usually highest cost)
aws cloudwatch get-metric-statistics \
    --namespace AWS/NATGateway \
    --metric-name BytesOutToSource \
    --dimensions Name=NatGatewayId,Value=$NAT_ID \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-02T00:00:00Z \
    --period 3600 \
    --statistics Sum

# Consider:
# - Reducing NAT Gateway usage (cache external API calls)
# - Using S3 VPC endpoint for model storage
# - Enabling ALB access logs compression
```

---

## 🧹 Cleanup / Teardown

### Destroy Infrastructure
```bash
cd aws/terraform

# Plan destruction
terraform plan -destroy

# Destroy all resources
terraform destroy -auto-approve

# This will remove:
# - EC2 instance
# - Load balancer
# - VPC and networking
# - IAM roles
# - CloudWatch logs (if retention expired)
```

### Delete Secrets (Optional)
```bash
# Mark for deletion (7-day recovery window)
aws secretsmanager delete-secret \
    --secret-id 3d-generator/prod/gemini-api-key \
    --region us-east-1

# Force immediate deletion (cannot be recovered)
aws secretsmanager delete-secret \
    --secret-id 3d-generator/prod/gemini-api-key \
    --force-delete-without-recovery \
    --region us-east-1
```

---

## 📈 Cost Breakdown (Monthly)

| Resource | Type | Cost/Month |
|----------|------|------------|
| EC2 Instance | t3.large | ~$60 |
| ALB | Application Load Balancer | ~$22 |
| NAT Gateway | Single AZ | ~$32 |
| EBS Storage | 50 GB gp3 | ~$4 |
| Data Transfer | Moderate usage | ~$10 |
| Secrets Manager | 1 secret | ~$0.40 |
| CloudWatch Logs | 5 GB/month | ~$2.50 |
| **TOTAL** | | **~$131/month** |

**Optimization Options:**
- Use t3.medium instead: Save $30/month
- Remove NAT Gateway: Save $32/month (no outbound internet)
- Reduce logs retention: Save $2/month
- Reserved Instance: Save 30-40%

---

## ✅ Deployment Complete!

Your application should now be running at:
- **URL**: `http://<alb-dns-name>/`
- **Health**: `http://<alb-dns-name>/health`
- **Logs**: CloudWatch Logs `/aws/ec2/3d-generator`

**Next Steps:**
1. ✅ Test application with sample prompts
2. ✅ Set up custom domain (optional)
3. ✅ Enable HTTPS with ACM certificate (optional)
4. ✅ Configure backup strategy
5. ✅ Set up monitoring alerts
