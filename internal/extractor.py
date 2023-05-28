import os

from dotenv import load_dotenv

from .models import CloudEnvironment

load_dotenv()
SCHEMA_PATH_KEY = "CLOUD_ENV_PATH"


async def get_cloud_environment() -> CloudEnvironment:
    schema_path = os.getenv(SCHEMA_PATH_KEY)
    with open(schema_path, "r+") as f:
        content = f.read()
    cloud_env = CloudEnvironment.parse_raw(content)
    return cloud_env
