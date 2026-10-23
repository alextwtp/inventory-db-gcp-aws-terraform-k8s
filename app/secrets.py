import os

CLOUD_PROVIDER = os.getenv("CLOUD_PROVIDER", "local") # "aws", "gcp", or "local"

def get_secret(secret_name: str) -> str:
    if CLOUD_PROVIDER == "aws":
        import boto3
        client = boto3.client('secretsmanager', region_name=os.getenv("AWS_REGION", "us-east-1"))
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
        
    elif CLOUD_PROVIDER == "gcp":
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GCP_PROJECT_ID")
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
        
    else:
        # For local development, directly grab environment variables or the .env file
        return os.getenv(secret_name, "")