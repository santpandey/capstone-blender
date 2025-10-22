# AWS Secrets Manager Configuration
# Stores sensitive credentials securely

# ============================================================================
# Secrets Manager - Gemini API Key
# ============================================================================

# Note: The actual secret value should be created manually or via AWS CLI
# This Terraform config only creates the secret placeholder

resource "aws_secretsmanager_secret" "gemini_api_key" {
  name        = var.gemini_secret_name
  description = "Gemini API Key for 3D Asset Generator"
  
  recovery_window_in_days = 7  # Grace period before permanent deletion
  
  tags = merge(var.tags, {
    Name        = "Gemini API Key"
    Sensitivity = "High"
  })
}

# Secret rotation (optional - requires Lambda function)
# resource "aws_secretsmanager_secret_rotation" "gemini_api_key" {
#   secret_id           = aws_secretsmanager_secret.gemini_api_key.id
#   rotation_lambda_arn = aws_lambda_function.rotate_secret.arn
#   
#   rotation_rules {
#     automatically_after_days = 30
#   }
# }

# ============================================================================
# Output Secret ARN
# ============================================================================

output "gemini_secret_arn" {
  description = "ARN of the Gemini API Key secret"
  value       = aws_secretsmanager_secret.gemini_api_key.arn
  sensitive   = true
}

output "gemini_secret_name" {
  description = "Name of the Gemini API Key secret"
  value       = aws_secretsmanager_secret.gemini_api_key.name
}

# ============================================================================
# Instructions for Setting Secret Value
# ============================================================================

# To set the secret value after deployment, run:
# 
# aws secretsmanager put-secret-value \
#     --secret-id 3d-generator/prod/gemini-api-key \
#     --secret-string '{"api_key":"YOUR_ACTUAL_GEMINI_KEY_HERE"}' \
#     --region us-east-1
#
# Or use AWS Console:
# 1. Go to AWS Secrets Manager
# 2. Find secret: 3d-generator/prod/gemini-api-key
# 3. Click "Set secret value"
# 4. Enter JSON: {"api_key": "your_key_here"}
