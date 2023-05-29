from .config import CLOUD_SCHEMA_PATH
from .models import CloudEnvironment


async def get_cloud_environment() -> CloudEnvironment:
    with open(CLOUD_SCHEMA_PATH, "r+") as f:
        content = f.read()
    cloud_env = CloudEnvironment.parse_raw(content)
    return cloud_env
