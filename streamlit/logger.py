import logging
import os
from functools import wraps

from dotenv import load_dotenv

load_dotenv()

if not os.path.exists("logging_data"):
    os.makedirs("logging_data")

log_file = os.getenv("LOG_PATH", "logging_data/db_connection.log")

logging.basicConfig(
    filename=log_file,
    filemode="w",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def logs(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Running '{func.__name__}' with args: {args}, kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logging.info(f"Finished '{func.__name__}' with result: {result}")
            return result
        except Exception as e:
            logging.error(f"Error in '{func.__name__}': {e}")
            return None

    return wrapper
