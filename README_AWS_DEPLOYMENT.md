# 🚀 AWS Deployment Guide - 3D Asset Generator

## 📋 Quick Reference

### Your 7 Questions - All Answered ✅

| # | Question | Answer | Status |
|---|----------|--------|--------|
| 1 | Use Terraform? | **YES** - Complete IaC | ✅ Done |
| 2 | Blender .exe on Linux? | Linux version `/opt/blender/blender` | ✅ Done |
| 3 | Windows paths on Linux? | Environment-aware paths | ✅ Done |
| 4 | AWS folder cleanup? | Old files removed/backed up | ✅ Done |
| 5 | .env secrets in AWS? | AWS Secrets Manager | ✅ Done |
| 6 | EC2 instance size? | **t3.large** (~$60/month) | ✅ Done |
| 7 | AWS networking? | Secure 3-tier VPC | ✅ Done |

---

## 📚 Documentation Structure

### Main Documents
1. **AWS_DEPLOYMENT_STRATEGY.md** (50+ pages)
   - Comprehensive strategy
   - Detailed architecture
   - Cost analysis
   - Troubleshooting

2. **AWS_DEPLOYMENT_CHECKLIST.md** (30+ pages)
   - Step-by-step deployment
   - Pre/post deployment tasks
   - Monitoring setup
   - Cleanup procedures

3. **DEPLOYMENT_SUMMARY.md** (15 pages)
   - Executive summary
   - Quick answers to all 7 questions
   - Cost breakdown
   - Next actions

4. **README_AWS_DEPLOYMENT.md** (This file)
   - Quick start guide
   - File structure
   - Common tasks

---

## 🎯 30-Minute Deployment Plan

### Phase 1: Preparation (10 min)

```bash
# 1. Install tools
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip && sudo mv terraform /usr/local/bin/

# 2. Configure AWS
aws configure

# 3. Create secret
aws secretsmanager create-secret \
    --name 3d-generator/prod/gemini-api-key \
    --secret-string '{"api_key":"YOUR_KEY"}' \
    --region us-east-1
```

### Phase 2: Code Updates (5 min)

```bash
# 1. Cleanup AWS files
cd aws
chmod +x cleanup_and_prepare.sh
./cleanup_and_prepare.sh

# 2. Update Git repo URL
cd terraform
nano variables.tf  # Change git_repo_url

# 3. Commit and push
git add .
git commit -m "AWS deployment ready"
git push origin main
```

### Phase 3: Deploy (15 min)

```bash
# 1. Initialize
cd aws/terraform
terraform init

# 2. Plan
terraform plan -out=tfplan

# 3. Deploy
terraform apply tfplan

# 4. Get URL
terraform output alb_url
```

### Phase 4: Verify (5 min)

```bash
# Test health
curl http://YOUR_ALB_DNS/health

# Test generation
curl -X POST http://YOUR_ALB_DNS/generate \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Create a blue sphere"}'
```

---

## 📁 File Structure

### New Files Created

```
d:\code\capstone\
│
├── blender_executor.py          (UPDATED - Cross-platform)
│
├── utils/
│   └── aws_secrets.py           (NEW - Secrets Manager)
│
├── aws/
│   ├── cleanup_and_prepare.sh   (NEW - Cleanup script)
│   ├── deploy.sh                (NEW - Deployment automation)
│   ├── destroy.sh               (KEPT - Teardown)
│   │
│   └── terraform/
│       ├── main.tf              (NEW - Simplified infrastructure)
│       ├── variables.tf         (NEW - Configuration)
│       ├── user_data.sh         (NEW - Ubuntu setup)
│       └── secrets.tf           (NEW - Secrets config)
│
└── Documentation/
    ├── AWS_DEPLOYMENT_STRATEGY.md       (50+ pages)
    ├── AWS_DEPLOYMENT_CHECKLIST.md      (30+ pages)
    ├── DEPLOYMENT_SUMMARY.md            (15 pages)
    └── README_AWS_DEPLOYMENT.md         (This file)
```

### Files Removed

```
❌ aws/terraform/sagemaker.tf    (Not using SageMaker)
❌ aws/start-aws.sh              (Use Terraform)
❌ aws/stop-aws.sh               (Use Terraform)
```

---

## 🔧 Key Code Changes

### 1. Cross-Platform Paths (`blender_executor.py`)

```python
# BEFORE - Windows only ❌
BLENDER_EXECUTABLE = r"D:\blender.exe"
SCRIPT_DIR = Path(r"d:\code\capstone\generated_scripts")

# AFTER - Cross-platform ✅
if IS_DOCKER:
    BLENDER_EXECUTABLE = "/opt/blender/blender"
elif IS_LINUX:
    BLENDER_EXECUTABLE = os.getenv("BLENDER_PATH", "/usr/local/bin/blender")
elif IS_WINDOWS:
    BLENDER_EXECUTABLE = os.getenv("BLENDER_PATH", r"D:\blender.exe")

BASE_DIR = Path("/app") if IS_DOCKER or IS_AWS else Path(__file__).parent
SCRIPT_DIR = BASE_DIR / "generated_scripts"
```

### 2. Secrets Management (`utils/aws_secrets.py`)

```python
from utils.aws_secrets import get_gemini_api_key

# Automatically uses AWS Secrets Manager in production
# Falls back to .env file in development
GEMINI_API_KEY = get_gemini_api_key()
```

### 3. Backend Update (TODO - You need to do this)

```python
# backend/main.py
# REPLACE THIS:
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# WITH THIS:
from utils.aws_secrets import get_gemini_api_key
GEMINI_API_KEY = get_gemini_api_key()
```

---

## 🏗️ Architecture Diagram

```
                        Internet
                           │
                           ↓
                   ┌───────────────┐
                   │ Internet      │
                   │ Gateway       │
                   └───────┬───────┘
                           │
              ┌────────────┴────────────┐
              │   VPC (10.0.0.0/16)     │
              │                         │
              │  ┌───────────────────┐  │
              │  │ Public Subnets    │  │
              │  │ (2 AZs)           │  │
              │  │                   │  │
              │  │  ┌─────────────┐  │  │
              │  │  │    ALB      │  │  │ ← Users access here
              │  │  │  Port 80    │  │  │   http://alb-dns/
              │  │  └──────┬──────┘  │  │
              │  └─────────┼─────────┘  │
              │            │            │
              │  ┌─────────┼─────────┐  │
              │  │ Private Subnet    │  │
              │  │                   │  │
              │  │  ┌────────────┐   │  │
              │  │  │ EC2        │   │  │ ← Application runs here
              │  │  │ t3.large   │   │  │   /app/backend/main.py
              │  │  │ Port 8000  │   │  │   Blender: /opt/blender
              │  │  └──────┬─────┘   │  │
              │  └─────────┼─────────┘  │
              │            │            │
              │      ┌─────┴──────┐     │
              │      │ NAT Gateway│     │ ← Outbound API calls
              │      └─────┬──────┘     │   (Gemini, updates)
              └────────────┼────────────┘
                          │
                     Internet
```

---

## 💰 Cost Estimate

### Monthly Breakdown

```
EC2 Instance (t3.large)      $60.74
ALB                          $22.27
NAT Gateway                  $32.85
EBS (50 GB)                   $4.00
Data Transfer                 $0.90
Secrets Manager               $0.40
CloudWatch Logs               $2.50
─────────────────────────────────
TOTAL                       ~$124/month
```

### Optimization (Reserved Instance 1-year)

```
EC2 Instance (t3.large RI)   $42.52  (save 30%)
ALB                          $22.27
NAT Gateway                  $32.85
Other                         $7.80
─────────────────────────────────
TOTAL                        ~$106/month  💰
```

---

## 🚀 Common Tasks

### Deploy
```bash
cd aws/terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### Update Application
```bash
# SSH into instance
INSTANCE_ID=$(terraform output -raw ec2_instance_id)
aws ssm start-session --target $INSTANCE_ID

# On instance
cd /app
sudo -u ubuntu git pull
sudo systemctl restart 3d-generator
```

### View Logs
```bash
# Real-time logs
aws logs tail /aws/ec2/3d-generator --follow

# Last 10 minutes
aws logs tail /aws/ec2/3d-generator --since 10m
```

### Check Costs
```bash
# Current month
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics BlendedCost
```

### Destroy Infrastructure
```bash
cd aws/terraform
terraform destroy -auto-approve
```

---

## ✅ Pre-Deployment Checklist

- [ ] AWS CLI installed and configured
- [ ] Terraform installed
- [ ] Gemini API key secret created in AWS
- [ ] Git repository URL updated in `variables.tf`
- [ ] Code pushed to GitHub
- [ ] AWS cleanup script executed
- [ ] `backend/main.py` updated to use `aws_secrets.py`
- [ ] Local testing completed

---

## 🎯 Post-Deployment Checklist

- [ ] Health check passing: `curl http://ALB_DNS/health`
- [ ] Can generate assets: Test with sample prompt
- [ ] CloudWatch logs visible
- [ ] Cost tracking enabled
- [ ] Billing alerts set up (optional)
- [ ] Custom domain configured (optional)
- [ ] HTTPS enabled (optional)

---

## 🆘 Quick Troubleshooting

### Application not responding
```bash
# Check instance status
aws ec2 describe-instance-status --instance-ids $INSTANCE_ID

# Check logs
aws logs tail /aws/ec2/3d-generator --since 5m

# Restart service
aws ssm send-command \
    --instance-ids $INSTANCE_ID \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=["systemctl restart 3d-generator"]'
```

### Health check failing
```bash
# Check target health
aws elbv2 describe-target-health \
    --target-group-arn $(terraform output -raw target_group_arn)

# Check security group rules
aws ec2 describe-security-groups \
    --group-ids $(terraform output -raw ec2_security_group_id)
```

### Secret not loading
```bash
# Test secret retrieval
aws secretsmanager get-secret-value \
    --secret-id 3d-generator/prod/gemini-api-key \
    --region us-east-1

# Check IAM permissions
aws iam get-role-policy \
    --role-name 3d-generator-ec2-role \
    --policy-name 3d-generator-secrets-manager
```

---

## 📞 Support Resources

### Documentation
- 📘 AWS_DEPLOYMENT_STRATEGY.md - Complete guide
- 📗 AWS_DEPLOYMENT_CHECKLIST.md - Step-by-step
- 📙 DEPLOYMENT_SUMMARY.md - Executive summary

### AWS Resources
- [EC2 User Guide](https://docs.aws.amazon.com/ec2/)
- [ALB Documentation](https://docs.aws.amazon.com/elasticloadbalancing/)
- [Secrets Manager Guide](https://docs.aws.amazon.com/secretsmanager/)
- [VPC Documentation](https://docs.aws.amazon.com/vpc/)

### Cost Management
- [AWS Cost Explorer](https://console.aws.amazon.com/cost-management/)
- [EC2 Pricing](https://aws.amazon.com/ec2/pricing/)
- [Calculator](https://calculator.aws/)

---

## 🎉 Success Criteria

Your deployment is successful when:

1. ✅ `curl http://ALB_DNS/health` returns `{"status":"healthy"}`
2. ✅ Can generate 3D asset from prompt
3. ✅ GLB file downloads successfully
4. ✅ CloudWatch logs are populating
5. ✅ Total cost is within budget (~$124/month)
6. ✅ No errors in application logs

---

## 🚀 You're Ready to Deploy!

Everything is prepared and documented. Follow the **30-Minute Deployment Plan** above to get started.

**Need help?** Check the comprehensive guides:
- AWS_DEPLOYMENT_STRATEGY.md (detailed)
- AWS_DEPLOYMENT_CHECKLIST.md (step-by-step)
- DEPLOYMENT_SUMMARY.md (quick reference)

**Good luck! 🎉**
