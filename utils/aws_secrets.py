"""
AWS Secrets Manager Integration
================================
Retrieves secrets from AWS Secrets Manager for production deployments.
Falls back to .env file for local development.
"""

import os
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

def is_aws_environment() -> bool:
    """Check if running in AWS environment"""
    return any([
        os.getenv("AWS_EXECUTION_ENV"),  # Lambda/ECS
        os.getenv("AWS_REGION"),          # General AWS
        os.path.exists("/var/run/secrets"),  # EC2 with IMDSv2
    ])

def get_secret_from_aws(secret_name: str, region: str = "us-east-1") -> Dict:
    """
    Retrieve secret from AWS Secrets Manager
    
    Args:
        secret_name: Name/ARN of the secret
        region: AWS region
        
    Returns:
        Dictionary containing secret values
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        client = boto3.client('secretsmanager', region_name=region)
        
        logger.info(f"Retrieving secret: {secret_name} from region: {region}")
        response = client.get_secret_value(SecretId=secret_name)
        
        if 'SecretString' in response:
            secret = json.loads(response['SecretString'])
            logger.info(f"✅ Successfully retrieved secret: {secret_name}")
            return secret
        else:
            raise ValueError("Secret does not contain SecretString")
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        logger.error(f"❌ AWS Secrets Manager error: {error_code}")
        
        if error_code == 'ResourceNotFoundException':
            logger.error(f"Secret '{secret_name}' not found")
        elif error_code == 'InvalidRequestException':
            logger.error(f"Invalid request for secret '{secret_name}'")
        elif error_code == 'InvalidParameterException':
            logger.error(f"Invalid parameter for secret '{secret_name}'")
        elif error_code == 'DecryptionFailure':
            logger.error(f"Cannot decrypt secret '{secret_name}'")
        elif error_code == 'InternalServiceError':
            logger.error("AWS Secrets Manager internal error")
            
        raise
    
    except Exception as e:
        logger.error(f"❌ Unexpected error retrieving secret: {e}")
        raise

def get_secret_from_env(secret_keys: list) -> Dict:
    """
    Retrieve secrets from environment variables (local development)
    
    Args:
        secret_keys: List of environment variable names to retrieve
        
    Returns:
        Dictionary containing secret values
    """
    secrets = {}
    missing_keys = []
    
    for key in secret_keys:
        value = os.getenv(key)
        if value:
            secrets[key] = value
            logger.info(f"✅ Loaded {key} from environment")
        else:
            missing_keys.append(key)
            logger.warning(f"⚠️ Missing environment variable: {key}")
    
    if missing_keys:
        logger.error(f"❌ Missing required environment variables: {missing_keys}")
        raise EnvironmentError(f"Missing required variables: {missing_keys}")
    
    return secrets

def load_secrets(
    secret_name: Optional[str] = None,
    secret_keys: Optional[list] = None,
    region: str = "us-east-1"
) -> Dict:
    """
    Load secrets from AWS Secrets Manager or environment variables
    
    Strategy:
    - Production (AWS): Use AWS Secrets Manager
    - Development (Local): Use .env file / environment variables
    
    Args:
        secret_name: AWS Secrets Manager secret name (for production)
        secret_keys: List of env var names (for development)
        region: AWS region
        
    Returns:
        Dictionary containing all secrets
        
    Example:
        >>> secrets = load_secrets(
        ...     secret_name="3d-generator/prod/api-keys",
        ...     secret_keys=["GEMINI_API_KEY", "AWS_REGION"]
        ... )
        >>> gemini_key = secrets.get("GEMINI_API_KEY")
    """
    logger.info("=" * 80)
    logger.info("SECRETS LOADING")
    logger.info("=" * 80)
    
    if is_aws_environment() and secret_name:
        # Production: Load from AWS Secrets Manager
        logger.info("Environment: AWS Production")
        logger.info(f"Loading secrets from AWS Secrets Manager: {secret_name}")
        
        try:
            secrets = get_secret_from_aws(secret_name, region)
            logger.info(f"✅ Loaded {len(secrets)} secrets from AWS")
            return secrets
        except Exception as e:
            logger.error(f"❌ Failed to load from AWS Secrets Manager: {e}")
            logger.warning("⚠️ Falling back to environment variables...")
            
            if secret_keys:
                return get_secret_from_env(secret_keys)
            else:
                raise
    else:
        # Development: Load from environment variables
        logger.info("Environment: Local Development")
        logger.info("Loading secrets from environment variables")
        
        if not secret_keys:
            logger.warning("⚠️ No secret_keys provided for local development")
            return {}
        
        return get_secret_from_env(secret_keys)

# Convenience functions for common secrets
def get_gemini_api_key(region: str = "us-east-1") -> str:
    """Get Gemini API Key from appropriate source"""
    secrets = load_secrets(
        secret_name="3d-generator/prod/gemini-api-key",
        secret_keys=["GEMINI_API_KEY"],
        region=region
    )
    return secrets.get("GEMINI_API_KEY") or secrets.get("api_key")

def get_all_app_secrets(region: str = "us-east-1") -> Dict:
    """Get all application secrets"""
    secrets = load_secrets(
        secret_name="3d-generator/prod/app-secrets",
        secret_keys=[
            "GEMINI_API_KEY",
            "AWS_REGION",
            "ENVIRONMENT",
            "LOG_LEVEL"
        ],
        region=region
    )
    return secrets

if __name__ == "__main__":
    # Test secrets loading
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*80)
    print("Testing Secrets Loading")
    print("="*80 + "\n")
    
    try:
        # Try loading Gemini API key
        api_key = get_gemini_api_key()
        print(f"✅ Successfully loaded Gemini API Key: {api_key[:10]}...")
    except Exception as e:
        print(f"❌ Failed to load secrets: {e}")
