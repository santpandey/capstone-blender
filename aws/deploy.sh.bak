#!/bin/bash
# AWS Deployment Script for 3D Asset Generator

set -e

# Configuration
AWS_REGION="us-east-1"
STACK_NAME="3d-generator"
DOMAIN_NAME="${1:-3d-generator.yourdomain.com}"

echo "🚀 Deploying 3D Asset Generator to AWS..."
echo "Region: $AWS_REGION"
echo "Domain: $DOMAIN_NAME"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install and configure AWS CLI."
    exit 1
fi

# Check Terraform
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not found. Please install Terraform."
    exit 1
fi

# Verify AWS credentials
echo "🔐 Checking AWS credentials..."
aws sts get-caller-identity > /dev/null || {
    echo "❌ AWS credentials not configured. Run 'aws configure'"
    exit 1
}

# Initialize Terraform
echo "🔧 Initializing Terraform..."
cd terraform
terraform init

# Plan deployment
echo "📋 Planning deployment..."
terraform plan \
    -var="aws_region=$AWS_REGION" \
    -var="domain_name=$DOMAIN_NAME" \
    -out=tfplan

# Confirm deployment
echo "⚠️  Review the plan above. Continue with deployment? (y/N)"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled."
    exit 0
fi

# Apply deployment
echo "🚀 Deploying infrastructure..."
terraform apply tfplan

# Get outputs
ALB_DNS=$(terraform output -raw load_balancer_dns)
VPC_ID=$(terraform output -raw vpc_id)

echo "✅ Deployment completed!"
echo "🌐 Application URL: http://$ALB_DNS"
echo "📊 VPC ID: $VPC_ID"

# Setup Route 53 (if domain provided)
if [[ "$DOMAIN_NAME" != "3d-generator.yourdomain.com" ]]; then
    echo "🌍 Setting up Route 53..."
    
    # Find hosted zone
    HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name \
        --dns-name "$DOMAIN_NAME" \
        --query "HostedZones[0].Id" \
        --output text | sed 's|/hostedzone/||')
    
    if [[ "$HOSTED_ZONE_ID" != "None" ]]; then
        # Create Route 53 record
        cat > route53-record.json << EOF
{
    "Changes": [{
        "Action": "UPSERT",
        "ResourceRecordSet": {
            "Name": "$DOMAIN_NAME",
            "Type": "A",
            "AliasTarget": {
                "DNSName": "$ALB_DNS",
                "EvaluateTargetHealth": true,
                "HostedZoneId": "$(aws elbv2 describe-load-balancers --names 3d-generator-alb --query 'LoadBalancers[0].CanonicalHostedZoneId' --output text)"
            }
        }
    }]
}
EOF
        
        aws route53 change-resource-record-sets \
            --hosted-zone-id "$HOSTED_ZONE_ID" \
            --change-batch file://route53-record.json
        
        rm route53-record.json
        
        echo "✅ Route 53 configured!"
        echo "🌐 Domain URL: http://$DOMAIN_NAME"
    else
        echo "⚠️  Hosted zone not found for $DOMAIN_NAME"
        echo "   Please create a hosted zone or use the ALB DNS name"
    fi
fi

echo ""
echo "🎉 Deployment Summary:"
echo "   • Infrastructure: ✅ Deployed"
echo "   • Load Balancer: $ALB_DNS"
echo "   • Frontend: Accessible via ALB"
echo "   • Backend: Running in private subnet"
echo "   • Auto Scaling: 1-3 instances"
echo ""
echo "📝 Next steps:"
echo "   1. Test the application: http://$ALB_DNS"
echo "   2. Configure SSL certificate (optional)"
echo "   3. Set up monitoring and alerts"
echo "   4. Configure backup strategy"

cd ..
