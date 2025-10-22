# Terraform Variables for 3D Asset Generator AWS Deployment

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "3d-generator"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

# EC2 Configuration
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.large"
  
  validation {
    condition     = contains(["t3.medium", "t3.large", "t3.xlarge", "c5.large", "c5.xlarge"], var.instance_type)
    error_message = "Instance type must be a valid compute instance for Blender workloads"
  }
}

variable "ebs_volume_size" {
  description = "EBS volume size in GB"
  type        = number
  default     = 50
}

variable "ebs_volume_type" {
  description = "EBS volume type"
  type        = string
  default     = "gp3"
}

# Networking
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidr" {
  description = "CIDR block for private subnet"
  type        = string
  default     = "10.0.10.0/24"
}

# Application Configuration
variable "app_port" {
  description = "Application port"
  type        = number
  default     = 8000
}

variable "health_check_path" {
  description = "Health check endpoint path"
  type        = string
  default     = "/health"
}

# Git Repository
variable "git_repo_url" {
  description = "Git repository URL for application code"
  type        = string
  default     = "https://github.com/yourusername/capstone-blender.git"
}

variable "git_branch" {
  description = "Git branch to deploy"
  type        = string
  default     = "main"
}

# Secrets
variable "gemini_secret_name" {
  description = "Name of Gemini API key secret in Secrets Manager"
  type        = string
  default     = "3d-generator/prod/gemini-api-key"
}

# Auto Scaling (disabled by default for low traffic)
variable "enable_auto_scaling" {
  description = "Enable auto scaling group (false = single instance)"
  type        = bool
  default     = false
}

variable "min_size" {
  description = "Minimum number of instances (if auto scaling enabled)"
  type        = number
  default     = 1
}

variable "max_size" {
  description = "Maximum number of instances (if auto scaling enabled)"
  type        = number
  default     = 1
}

variable "desired_capacity" {
  description = "Desired number of instances (if auto scaling enabled)"
  type        = number
  default     = 1
}

# Domain (Optional)
variable "domain_name" {
  description = "Domain name for the application (optional)"
  type        = string
  default     = ""
}

variable "route53_zone_id" {
  description = "Route 53 hosted zone ID (optional)"
  type        = string
  default     = ""
}

# Monitoring
variable "enable_cloudwatch_logs" {
  description = "Enable CloudWatch logs"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch logs retention in days"
  type        = number
  default     = 7
}

# Tags
variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "3D Asset Generator"
    Environment = "Production"
    ManagedBy   = "Terraform"
  }
}
