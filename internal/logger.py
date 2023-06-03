import functools
import logging
import pathlib

PROJECT_DIR = pathlib.Path(__file__).parent.parent.resolve()
LOGS_DIR = PROJECT_DIR.joinpath("logs")

from time import time


def get_logger_filename(module: str) -> str:
    print(module)
    module_name = pathlib.Path(module).name.split(".")[0]
    logs_filename = LOGS_DIR.joinpath(f"{module_name}.log")
    return logs_filename


def configure_logger(logs_filename: str, log_level: int):
    LOGS_DIR.mkdir(exist_ok=False)

    logging.basicConfig(
        filename=logs_filename,
        level=log_level,
        format="%(asctime)s : %(name)s : %(levelname)s: %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
    )


def log_step(logger: logging.Logger, msg: str):
    def decorator(func):
        @functools.wraps(func)
        def wrap(*args, **kwargs):
            before = time()
            logger.debug(f"Start {msg}")
            res = func(*args, **kwargs)
            after = time()
            logger.debug(f"Finish {msg} [{after - before}]")
            return res

        return wrap

    return decorator


def log_step_async(logger: logging.Logger, msg: str):
    def decorator(coro):
        @functools.wraps(coro)
        async def wrap(*args, **kwargs):
            before = time()
            logger.debug(f"Start {msg}")
            res = await coro(*args, **kwargs)
            after = time()
            logger.debug(f"Finish {msg} [{after - before}]")
            return res

        return wrap

    return decorator
