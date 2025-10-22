#!/bin/bash
# Deployment Script for 3D Asset Generator on AWS
# This script deploys the infrastructure using Terraform

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/terraform"
AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="3d-generator"
GEMINI_SECRET_NAME="3d-generator/prod/gemini-api-key"

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_banner() {
    echo ""
    echo "=========================================="
    echo "  3D Asset Generator - AWS Deployment"
    echo "=========================================="
    echo ""
}

# ============================================================================
# Pre-deployment Checks
# ============================================================================

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed"
        log_info "Install: https://aws.amazon.com/cli/"
        exit 1
    fi
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform is not installed"
        log_info "Install: https://www.terraform.io/downloads"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured"
        log_info "Run: aws configure"
        exit 1
    fi
    
    # Check if in correct directory
    if [ ! -d "$TERRAFORM_DIR" ]; then
        log_error "Terraform directory not found: $TERRAFORM_DIR"
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# ============================================================================
# Secrets Management
# ============================================================================

setup_secrets() {
    log_info "Checking AWS Secrets Manager..."
    
    # Check if secret exists
    if aws secretsmanager describe-secret \
        --secret-id "$GEMINI_SECRET_NAME" \
        --region "$AWS_REGION" &> /dev/null; then
        log_success "Secret already exists: $GEMINI_SECRET_NAME"
    else
        log_warning "Secret does not exist: $GEMINI_SECRET_NAME"
        echo ""
        echo "You need to create the Gemini API Key secret."
        echo ""
        read -p "Do you want to create it now? (y/n): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -sp "Enter your Gemini API Key: " GEMINI_KEY
            echo
            
            aws secretsmanager create-secret \
                --name "$GEMINI_SECRET_NAME" \
                --description "Gemini API Key for 3D Asset Generator" \
                --secret-string "{\"api_key\":\"$GEMINI_KEY\"}" \
                --region "$AWS_REGION"
            
            log_success "Secret created successfully"
        else
            log_error "Cannot proceed without Gemini API Key secret"
            echo ""
            echo "Create it manually with:"
            echo "aws secretsmanager create-secret \\"
            echo "    --name $GEMINI_SECRET_NAME \\"
            echo "    --secret-string '{\"api_key\":\"YOUR_KEY\"}' \\"
            echo "    --region $AWS_REGION"
            exit 1
        fi
    fi
}

# ============================================================================
# Terraform Deployment
# ============================================================================

terraform_init() {
    log_info "Initializing Terraform..."
    cd "$TERRAFORM_DIR"
    terraform init
    log_success "Terraform initialized"
}

terraform_plan() {
    log_info "Creating Terraform plan..."
    cd "$TERRAFORM_DIR"
    
    terraform plan \
        -var="aws_region=$AWS_REGION" \
        -out=tfplan
    
    log_success "Terraform plan created"
    echo ""
    log_warning "Please review the plan above carefully"
    echo ""
    read -p "Do you want to proceed with deployment? (y/n): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment cancelled"
        exit 0
    fi
}

terraform_apply() {
    log_info "Applying Terraform configuration..."
    cd "$TERRAFORM_DIR"
    
    terraform apply tfplan
    
    log_success "Infrastructure deployed successfully"
}

# ============================================================================
# Post-deployment
# ============================================================================

get_outputs() {
    log_info "Retrieving deployment information..."
    cd "$TERRAFORM_DIR"
    
    echo ""
    echo "=========================================="
    echo "  Deployment Information"
    echo "=========================================="
    echo ""
    
    ALB_DNS=$(terraform output -raw alb_dns_name 2>/dev/null || echo "N/A")
    ALB_URL=$(terraform output -raw alb_url 2>/dev/null || echo "N/A")
    INSTANCE_ID=$(terraform output -raw ec2_instance_id 2>/dev/null || echo "N/A")
    VPC_ID=$(terraform output -raw vpc_id 2>/dev/null || echo "N/A")
    
    echo "Load Balancer DNS: $ALB_DNS"
    echo "Application URL:   $ALB_URL"
    echo "EC2 Instance ID:   $INSTANCE_ID"
    echo "VPC ID:            $VPC_ID"
    echo ""
    echo "=========================================="
    echo ""
    
    # Save to file
    cat > "$SCRIPT_DIR/deployment_info.txt" << EOF
Deployment Information
======================
Date: $(date)
Region: $AWS_REGION

Load Balancer DNS: $ALB_DNS
Application URL:   $ALB_URL
EC2 Instance ID:   $INSTANCE_ID
VPC ID:            $VPC_ID

Health Check:
curl $ALB_URL/health

View Logs:
aws logs tail /aws/ec2/$PROJECT_NAME --follow --region $AWS_REGION

SSH to Instance (from bastion):
aws ssm start-session --target $INSTANCE_ID --region $AWS_REGION
EOF
    
    log_success "Deployment info saved to: $SCRIPT_DIR/deployment_info.txt"
}

verify_deployment() {
    log_info "Verifying deployment..."
    cd "$TERRAFORM_DIR"
    
    ALB_URL=$(terraform output -raw alb_url 2>/dev/null || echo "")
    
    if [ -z "$ALB_URL" ]; then
        log_warning "Could not retrieve ALB URL"
        return
    fi
    
    log_info "Waiting for application to be ready (this may take a few minutes)..."
    
    MAX_ATTEMPTS=30
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        if curl -f -s "$ALB_URL/health" > /dev/null 2>&1; then
            log_success "Application is healthy and ready!"
            echo ""
            echo "🎉 Access your application at: $ALB_URL"
            echo ""
            return 0
        fi
        
        ATTEMPT=$((ATTEMPT + 1))
        echo -n "."
        sleep 10
    done
    
    echo ""
    log_warning "Health check timeout - application may still be starting"
    log_info "Check logs with: aws logs tail /aws/ec2/$PROJECT_NAME --follow"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    print_banner
    
    check_prerequisites
    setup_secrets
    terraform_init
    terraform_plan
    terraform_apply
    get_outputs
    verify_deployment
    
    echo ""
    log_success "Deployment completed!"
    echo ""
    echo "Next steps:"
    echo "1. Test the application at the URL above"
    echo "2. Monitor logs: aws logs tail /aws/ec2/$PROJECT_NAME --follow"
    echo "3. To destroy: cd $TERRAFORM_DIR && terraform destroy"
    echo ""
}

# Run main function
main "$@"
