"""
Central config file loaded from environment variables.
Copy .env.example to .env and fill in your values before running anything.
"""
import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")

# These tags get applied to every resource this tool creates.
# Makes it easy to find and clean up everything later.
DEFAULT_TAGS = {
    "Project":   "infra-automation",
    "ManagedBy": "aws-infra-automation",
    "Env":       os.getenv("ENV", "dev"),
}
