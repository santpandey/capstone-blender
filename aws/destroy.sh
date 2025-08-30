#!/bin/bash
# AWS Destruction Script for 3D Asset Generator

set -e

echo "🗑️  Destroying 3D Asset Generator AWS infrastructure..."

# Check Terraform
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not found. Please install Terraform."
    exit 1
fi

# Confirm destruction
echo "⚠️  This will destroy ALL AWS resources. Are you sure? (y/N)"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "❌ Destruction cancelled."
    exit 0
fi

# Destroy infrastructure
echo "💥 Destroying infrastructure..."
cd terraform
terraform destroy -auto-approve

echo "✅ Infrastructure destroyed!"
echo "💰 Remember to check for any remaining resources that might incur costs."

cd ..
