# 🛑 AWS Shutdown & Resource Cleanup Guide

## 📋 Overview

Two scripts available for shutting down AWS infrastructure:

| Script | Purpose | Use Case |
|--------|---------|----------|
| **shutdown.sh** | Complete cleanup with verification | ✅ **Recommended** - Ensures all resources deleted |
| **destroy.sh** | Quick Terraform destroy | ⚡ Fast, but may leave orphaned resources |

---

## 🎯 Recommended: Complete Shutdown

### Use `shutdown.sh` for comprehensive cleanup:

```bash
cd aws
chmod +x shutdown.sh
./shutdown.sh
```

### What it does:

1. ✅ **Safety Confirmation** - Requires explicit confirmation
2. ✅ **Pre-Shutdown Checks** - Verifies tools installed
3. ✅ **Resource Inventory** - Saves list of resources being deleted
4. ✅ **Terraform Destroy** - Deletes all Terraform-managed resources
5. ✅ **Verification Loop** - Waits and verifies each resource type deleted
6. ✅ **Force Cleanup** - Handles stubborn resources (NAT Gateway, etc.)
7. ✅ **Secrets Management** - Asks about deleting secrets
8. ✅ **Local Cleanup** - Removes Terraform state files
9. ✅ **Final Report** - Generates deletion report

### Time Required: ~10-15 minutes

---

## ⚡ Quick: Terraform Destroy Only

### Use `destroy.sh` for fast teardown:

```bash
cd aws
./destroy.sh
```

### What it does:

- ✅ Runs `terraform destroy`
- ❌ Does NOT verify deletion
- ❌ Does NOT wait for resources
- ❌ Does NOT handle orphaned resources
- ❌ Does NOT clean up secrets

### Time Required: ~5 minutes

⚠️ **Warning**: May leave behind resources that cost money!

---

## 📊 Detailed Comparison

### Shutdown.sh (Comprehensive)

**Pros:**
- ✅ Verifies ALL resources deleted
- ✅ Waits for slow resources (NAT Gateway: 5 min)
- ✅ Handles dependencies correctly
- ✅ Force cleanup for stuck resources
- ✅ Manages secrets
- ✅ Generates reports
- ✅ No surprise AWS bills

**Cons:**
- ⏱️ Takes 10-15 minutes
- 🔍 More verbose output

**Use when:**
- Production teardown
- Complete project end
- Cost optimization
- Need audit trail

### Destroy.sh (Quick)

**Pros:**
- ⚡ Fast (5 minutes)
- 🎯 Simple output
- 🔄 Good for dev cycles

**Cons:**
- ❌ May leave orphaned resources
- ❌ No verification
- ❌ Secrets remain
- 💸 Potential for unexpected costs

**Use when:**
- Development testing
- Quick iteration
- Planning to redeploy soon

---

## 🔍 What Gets Deleted

### Terraform-Managed Resources

Both scripts delete:
- ✅ EC2 Instance
- ✅ Application Load Balancer
- ✅ Target Groups
- ✅ VPC, Subnets, Route Tables
- ✅ Internet Gateway
- ✅ NAT Gateway (takes 5+ min)
- ✅ Elastic IPs
- ✅ Security Groups
- ✅ IAM Roles & Policies
- ✅ Launch Templates

### Additional Cleanup (shutdown.sh only)

- ✅ CloudWatch Log Groups (optional)
- ✅ AWS Secrets (asks for confirmation)
- ✅ Orphaned resources
- ✅ Terraform state files

---

## 🚨 Safety Features (shutdown.sh)

### 1. Double Confirmation

```
Are you ABSOLUTELY SURE? (type 'yes')
Type project name to confirm: 3d-generator
```

### 2. Resource Inventory

Saves list of all resources before deletion:
```
deleted_resources_20241024_112600.txt
```

### 3. Verification Loop

Monitors deletion of:
- EC2 instances
- Load balancers
- NAT gateways
- Elastic IPs
- VPCs
- Security groups
- IAM roles
- CloudWatch logs

### 4. Force Cleanup

If resources stuck after Terraform destroy:
```
Attempt force cleanup? (y/n)
```

Handles:
- NAT Gateways in "deleting" state
- Elastic IPs not released
- Security groups with dependencies
- VPCs with remaining subnets

### 5. Final Report

Generates comprehensive status report:
```
shutdown_report_20241024_112630.txt
```

---

## 📝 Example Output

### shutdown.sh Output

```bash
==========================================
  AWS Resource Shutdown & Cleanup
  Project: 3D Asset Generator
==========================================

[INFO] Checking prerequisites...
[SUCCESS] All prerequisites met

[INFO] Saving resource information...
[SUCCESS] Resource information saved

[INFO] Creating destruction plan...
[SUCCESS] Destruction plan created

[WARNING] Starting resource destruction...
[SUCCESS] Terraform destroy completed

[INFO] Verifying EC2 instances deleted...
[SUCCESS] ✓ No EC2 instances found

[INFO] Verifying load balancers deleted...
[SUCCESS] ✓ No load balancers found

[INFO] Verifying NAT gateways deleted...
[WARNING] ⚠ NAT gateways still exist
[INFO] NAT gateways can take several minutes to delete...

[INFO] Waiting 30 seconds before next check...

[SUCCESS] All resources successfully deleted!

[INFO] Delete secrets? (y/n): y
[SUCCESS] Secrets deleted

[SUCCESS] ✅ AWS resource shutdown completed!
```

---

## 💰 Cost Implications

### Immediate Cost Savings (per month)

After complete shutdown:

| Resource | Monthly Cost | Status |
|----------|--------------|--------|
| EC2 Instance | -$60 | ✅ Deleted |
| ALB | -$22 | ✅ Deleted |
| NAT Gateway | -$33 | ✅ Deleted |
| EBS Storage | -$4 | ✅ Deleted |
| **Total Savings** | **-$119/month** | |

### Potential Lingering Costs

If NOT properly cleaned:

| Resource | Monthly Cost | Risk |
|----------|--------------|------|
| NAT Gateway | $33 | 🔴 High |
| Elastic IP | $3.65 | 🟡 Medium |
| EBS Snapshots | $0.05/GB | 🟢 Low |
| CloudWatch Logs | $0.50/GB | 🟢 Low |
| Secrets Manager | $0.40/secret | 🟢 Low |

⚠️ **NAT Gateway** is the biggest risk - continues charging even if idle!

---

## 🔧 Troubleshooting

### Issue: "Resources still exist after destroy"

**Solution**: Run shutdown.sh with force cleanup
```bash
./shutdown.sh
# When prompted: Attempt force cleanup? y
```

### Issue: "Terraform state locked"

**Solution**: 
```bash
cd terraform
terraform force-unlock <lock-id>
```

### Issue: "Permission denied"

**Solution**:
```bash
chmod +x shutdown.sh
chmod +x destroy.sh
```

### Issue: "NAT Gateway taking forever"

**Explanation**: NAT Gateways can take 5-10 minutes to delete
```bash
# Monitor status:
aws ec2 describe-nat-gateways \
    --filter "Name=tag:Name,Values=3d-generator*" \
    --region us-east-1
```

### Issue: "VPC won't delete"

**Cause**: Dependencies (subnets, internet gateways)

**Solution**: shutdown.sh handles this automatically, or:
```bash
# Manual cleanup:
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=3d-generator*"
aws ec2 delete-vpc --vpc-id vpc-xxxxx
```

---

## 📋 Shutdown Checklist

### Before Running Shutdown

- [ ] Backup any important data (generated models)
- [ ] Export CloudWatch logs if needed
- [ ] Document configuration for future reference
- [ ] Notify team members
- [ ] Check for running jobs

### After Running Shutdown

- [ ] Verify $0 AWS bill next month
- [ ] Check AWS Console for orphaned resources
- [ ] Review generated reports
- [ ] Delete local Terraform state backups (optional)
- [ ] Update documentation

---

## 🎯 Manual Verification

### Check for Remaining Resources

```bash
# EC2 Instances
aws ec2 describe-instances \
    --filters "Name=tag:Project,Values=3D Asset Generator" \
    --region us-east-1

# Load Balancers
aws elbv2 describe-load-balancers \
    --region us-east-1 | grep 3d-generator

# NAT Gateways
aws ec2 describe-nat-gateways \
    --filter "Name=tag:Name,Values=3d-generator*" \
    --region us-east-1

# VPCs
aws ec2 describe-vpcs \
    --filters "Name=tag:Name,Values=3d-generator*" \
    --region us-east-1

# Elastic IPs
aws ec2 describe-addresses \
    --filters "Name=tag:Name,Values=3d-generator*" \
    --region us-east-1

# Secrets
aws secretsmanager list-secrets \
    --region us-east-1 | grep 3d-generator
```

### All Commands Should Return Empty Results

---

## 🔄 Re-Deployment After Shutdown

If you want to deploy again:

```bash
cd aws/terraform

# Terraform will rebuild from scratch
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

All resources recreated fresh!

---

## 📞 Emergency Shutdown

### If Something Goes Wrong

```bash
# 1. Stop the EC2 instance immediately
aws ec2 stop-instances --instance-ids <instance-id>

# 2. Run force cleanup
cd aws
./shutdown.sh
# Choose: force cleanup = yes

# 3. Manual cleanup if needed
aws ec2 delete-nat-gateway --nat-gateway-id <nat-id>
aws ec2 release-address --allocation-id <eip-id>

# 4. Contact AWS Support if stuck resources
```

---

## ✅ Recommended Approach

### For Production Shutdown:

```bash
# 1. Use comprehensive shutdown
cd aws
./shutdown.sh

# 2. Verify manually
aws ec2 describe-instances --filters "Name=tag:Project,Values=3D Asset Generator"

# 3. Check costs next month
# Should be $0 (except maybe $0.40 for secrets if kept)
```

### For Development:

```bash
# Quick iteration
./destroy.sh

# But verify periodically with:
./shutdown.sh
```

---

## 📊 Cost Monitoring After Shutdown

### Set Up Billing Alert

```bash
aws cloudwatch put-metric-alarm \
    --alarm-name "unexpected-costs-after-shutdown" \
    --alarm-description "Alert if AWS bill > $5" \
    --metric-name EstimatedCharges \
    --namespace AWS/Billing \
    --statistic Maximum \
    --period 21600 \
    --threshold 5 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1
```

### Check Cost Explorer

1. Go to AWS Console → Cost Explorer
2. Filter by: Last 30 days
3. Group by: Service
4. Should see charges drop to ~$0

---

## 🎉 Success Criteria

Shutdown is complete when:

1. ✅ `shutdown.sh` script completes successfully
2. ✅ All verification checks pass
3. ✅ AWS Console shows no EC2 instances
4. ✅ AWS Console shows no load balancers
5. ✅ AWS Console shows no VPCs (except default)
6. ✅ Next month's bill is ~$0
7. ✅ Final report generated
8. ✅ No surprise charges

---

## 📄 Generated Reports

After shutdown, check for:

```
aws/
├── deleted_resources_20241024_112600.txt    # Before deletion
├── shutdown_report_20241024_112630.txt       # After deletion
└── deployment_info.txt                       # Original deployment info
```

Keep these for audit/reference!

---

## 🆘 Support

### If Shutdown Fails:

1. Check the shutdown_report_*.txt file
2. Review CloudWatch logs
3. Run manual verification commands
4. Use AWS Console to inspect resources
5. Contact AWS Support if needed

### If Unexpected Costs:

1. Check Cost Explorer for service breakdown
2. Look for EBS snapshots (not managed by Terraform)
3. Check for CloudWatch alarms
4. Review S3 buckets (if created manually)

---

**Remember**: Use `shutdown.sh` for production, `destroy.sh` for dev! 🚀
