import logging

from .config import CLOUD_SCHEMA_PATH
from .logger import log_step, log_step_async
from .models import CloudEnvironment

logger = logging.getLogger(__name__)


@log_step(logger, "reading schema")
def read_schema():
    with open(CLOUD_SCHEMA_PATH, "r+") as f:
        content = f.read()
    return content


@log_step_async(logger, "getting cloud environment")
async def get_cloud_environment() -> CloudEnvironment:
    content = read_schema()
    cloud_env = CloudEnvironment.parse_raw(content)

    return cloud_env
