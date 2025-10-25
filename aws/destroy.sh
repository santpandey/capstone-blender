#!/bin/bash
# Quick Terraform Destroy
# For comprehensive shutdown with verification, use: ./shutdown.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "  Quick Terraform Destroy"
echo "=========================================="
echo ""
echo "⚠️  Note: For comprehensive shutdown with verification,"
echo "    use: ./shutdown.sh"
echo ""

# Check Terraform
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not found. Please install Terraform."
    exit 1
fi

cd "$SCRIPT_DIR/terraform"

if [ ! -f "terraform.tfstate" ]; then
    echo "No terraform state found. Nothing to destroy."
    exit 0
fi

echo "Running Terraform destroy..."
terraform destroy

echo ""
echo "✅ Terraform destroy complete!"
echo ""
echo "To verify all resources are deleted and cleaned up, run:"
echo "  ./shutdown.sh"
echo ""
