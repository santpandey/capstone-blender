#!/bin/bash
# Setup script permissions for AWS deployment/shutdown

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Setting execute permissions on AWS scripts..."

chmod +x deploy.sh
chmod +x destroy.sh
chmod +x shutdown.sh
chmod +x cleanup_and_prepare.sh
chmod +x setup_scripts.sh

echo "✅ All scripts now executable"
echo ""
echo "Available scripts:"
echo "  ./deploy.sh              - Deploy to AWS"
echo "  ./destroy.sh             - Quick Terraform destroy"
echo "  ./shutdown.sh            - Complete shutdown with verification (RECOMMENDED)"
echo "  ./cleanup_and_prepare.sh - Prepare files for deployment"
echo ""
