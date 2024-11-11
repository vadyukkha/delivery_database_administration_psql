import logging
import os
from functools import wraps
from tkinter import messagebox

import psycopg2
from dotenv import load_dotenv

load_dotenv()
log_file = os.getenv("LOG_PATH", "logging_data/db_connection.log")

if os.path.exists(log_file):
    os.remove(log_file)

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def dbconnect_logger(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Running {func.__name__} with args: {args}, kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logging.info(f"Finished {func.__name__} with result: {result}")
            return result
        except psycopg2.Error as e:
            logging.error(f"Error in {func.__name__}: {e}")
            messagebox.showerror("Database Error", f"An error occurred: {e}")
            return None

    return wrapper
