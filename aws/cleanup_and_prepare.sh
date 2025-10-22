#!/bin/bash
# Cleanup and prepare AWS deployment files
# This script removes obsolete files and renames new files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  AWS Deployment Files Cleanup"
echo "=========================================="
echo ""

# ============================================================================
# Remove obsolete files
# ============================================================================

echo "[1/3] Removing obsolete files..."

# Remove SageMaker (not using it)
if [ -f "terraform/sagemaker.tf" ]; then
    echo "  - Removing terraform/sagemaker.tf (SageMaker not needed)"
    rm terraform/sagemaker.tf
fi

# Remove old start/stop scripts (use terraform instead)
if [ -f "start-aws.sh" ]; then
    echo "  - Removing start-aws.sh (obsolete)"
    rm start-aws.sh
fi

if [ -f "stop-aws.sh" ]; then
    echo "  - Removing stop-aws.sh (obsolete)"
    rm stop-aws.sh
fi

# Remove old deploy script (replaced with deploy_updated.sh)
if [ -f "deploy.sh" ] && [ -f "deploy_updated.sh" ]; then
    echo "  - Backing up old deploy.sh to deploy.sh.bak"
    mv deploy.sh deploy.sh.bak
fi

echo "✅ Obsolete files removed"

# ============================================================================
# Rename new files
# ============================================================================

echo ""
echo "[2/3] Renaming new files to active names..."

cd terraform

# Backup old main.tf if it exists
if [ -f "main.tf" ] && [ -f "main_simplified.tf" ]; then
    echo "  - Backing up old main.tf to main.tf.old"
    mv main.tf main.tf.old
fi

# Rename new main.tf
if [ -f "main_simplified.tf" ]; then
    echo "  - Activating main_simplified.tf → main.tf"
    mv main_simplified.tf main.tf
fi

# Backup old user_data.sh
if [ -f "user_data.sh" ] && [ -f "user_data_updated.sh" ]; then
    echo "  - Backing up old user_data.sh to user_data.sh.old"
    mv user_data.sh user_data.sh.old
fi

# Rename new user_data.sh
if [ -f "user_data_updated.sh" ]; then
    echo "  - Activating user_data_updated.sh → user_data.sh"
    mv user_data_updated.sh user_data.sh
fi

# Backup old secrets.tf if it exists
if [ -f "secrets.tf" ] && [ -f "secrets_updated.tf" ]; then
    echo "  - Backing up old secrets.tf to secrets.tf.old"
    mv secrets.tf secrets.tf.old
fi

# Rename new secrets.tf
if [ -f "secrets_updated.tf" ]; then
    echo "  - Activating secrets_updated.tf → secrets.tf"
    mv secrets_updated.tf secrets.tf
fi

cd ..

# Rename deploy script
if [ -f "deploy_updated.sh" ]; then
    echo "  - Activating deploy_updated.sh → deploy.sh"
    mv deploy_updated.sh deploy.sh
    chmod +x deploy.sh
fi

echo "✅ Files renamed"

# ============================================================================
# Create .gitignore for Terraform
# ============================================================================

echo ""
echo "[3/3] Creating/updating .gitignore..."

cat > terraform/.gitignore << 'EOF'
# Terraform
.terraform/
.terraform.lock.hcl
terraform.tfstate
terraform.tfstate.backup
tfplan
*.tfvars
!terraform.tfvars.example

# Backups
*.old
*.bak

# OS
.DS_Store
Thumbs.db
EOF

echo "✅ .gitignore created"

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "=========================================="
echo "  Cleanup Complete!"
echo "=========================================="
echo ""
echo "Active files:"
echo "  ✅ terraform/main.tf (simplified, single EC2)"
echo "  ✅ terraform/user_data.sh (Ubuntu setup)"
echo "  ✅ terraform/secrets.tf (AWS Secrets Manager)"
echo "  ✅ terraform/variables.tf (configuration)"
echo "  ✅ deploy.sh (deployment automation)"
echo "  ✅ destroy.sh (teardown)"
echo ""
echo "Backed up files (in case you need them):"
echo "  📦 terraform/main.tf.old"
echo "  📦 terraform/user_data.sh.old"
echo "  📦 terraform/secrets.tf.old (if existed)"
echo "  📦 deploy.sh.bak"
echo ""
echo "Next steps:"
echo "  1. Update terraform/variables.tf with your Git repo URL"
echo "  2. Review terraform/main.tf configuration"
echo "  3. Run: ./deploy.sh"
echo ""
