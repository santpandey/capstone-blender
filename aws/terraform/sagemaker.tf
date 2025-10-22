# SageMaker endpoint for BlenderLLM deployment
# Optional - only deployed if DEPLOY_BLENDER_LLM=true

variable "deploy_blender_llm" {
  description = "Deploy BlenderLLM on SageMaker"
  type        = bool
  default     = false
}

variable "blender_llm_instance_type" {
  description = "Instance type for BlenderLLM SageMaker endpoint"
  type        = string
  default     = "ml.g4dn.xlarge"
}

# SageMaker execution role
resource "aws_iam_role" "sagemaker_execution_role" {
  count = var.deploy_blender_llm ? 1 : 0
  name  = "blender-llm-sagemaker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "sagemaker_execution_role_policy" {
  count      = var.deploy_blender_llm ? 1 : 0
  role       = aws_iam_role.sagemaker_execution_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

# SageMaker model
resource "aws_sagemaker_model" "blender_llm_model" {
  count          = var.deploy_blender_llm ? 1 : 0
  name           = "blender-llm-model"
  execution_role_arn = aws_iam_role.sagemaker_execution_role[0].arn

  primary_container {
    image = "763104351884.dkr.ecr.us-east-1.amazonaws.com/huggingface-pytorch-inference:2.0.0-transformers4.28.1-gpu-py310-cu118-ubuntu20.04"
    
    environment = {
      HF_MODEL_ID = "FreedomIntelligence/BlenderLLM"
      HF_TASK     = "text-generation"
    }
  }

  tags = {
    Name        = "BlenderLLM Model"
    Environment = "production"
    Project     = "3d-generator"
  }
}

# SageMaker endpoint configuration
resource "aws_sagemaker_endpoint_configuration" "blender_llm_config" {
  count = var.deploy_blender_llm ? 1 : 0
  name  = "blender-llm-endpoint-config"

  production_variants {
    variant_name           = "primary"
    model_name            = aws_sagemaker_model.blender_llm_model[0].name
    initial_instance_count = 1
    instance_type         = var.blender_llm_instance_type
    initial_variant_weight = 1
  }

  tags = {
    Name        = "BlenderLLM Endpoint Config"
    Environment = "production"
    Project     = "3d-generator"
  }
}

# SageMaker endpoint
resource "aws_sagemaker_endpoint" "blender_llm_endpoint" {
  count                = var.deploy_blender_llm ? 1 : 0
  name                 = "blender-llm-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.blender_llm_config[0].name

  tags = {
    Name        = "BlenderLLM Endpoint"
    Environment = "production"
    Project     = "3d-generator"
  }
}

# Output SageMaker endpoint name
output "blender_llm_endpoint_name" {
  description = "SageMaker endpoint name for BlenderLLM"
  value       = var.deploy_blender_llm ? aws_sagemaker_endpoint.blender_llm_endpoint[0].name : null
}
