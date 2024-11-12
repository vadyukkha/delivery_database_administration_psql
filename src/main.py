import os
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk

import psycopg2
from dotenv import load_dotenv

from logger_decorator import dbconnect_logger, logging

load_dotenv()

DB_INIT_SCRIPT = os.getenv("DB_INIT_SCRIPT", "database/demo_small.sql")
DB_NAME = os.getenv("DB_NAME", "airport")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")


class DispatcherBD:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Login to Database")
        self.root.geometry("400x400")

        self.connection = None

        self.create_login_window()

    def create_login_window(self):
        ttk.Label(self.root, text="Login:").pack(pady=(20, 5))
        self.login_entry = ttk.Entry(self.root)
        self.login_entry.pack(pady=5)

        ttk.Label(self.root, text="Password:").pack(pady=5)
        self.password_entry = ttk.Entry(self.root, show="*")
        self.password_entry.pack(pady=5)

        login_button = ttk.Button(self.root, text="Login", command=self.authenticate)
        login_button.pack(pady=20)

    def authenticate(self):
        login = self.login_entry.get()
        password = self.password_entry.get()

        if login == "" and password == "":
            messagebox.showwarning(
                "Input Error", "Please enter both login and password."
            )
            return

        if self.connect_to_db(login, password):
            messagebox.showinfo("Login Success", "Successfully logged in!")
            self.root.destroy()
            self.show_main_window()
        else:
            messagebox.showerror(
                "Login Failed",
                "Failed to connect to the database with the provided credentials.",
            )

    @dbconnect_logger
    def connect_to_db(self, login, password):
        if not self.database_exists():
            self.initialize_database(login, password)

        self.connection = psycopg2.connect(
            dbname=DB_NAME, user="postgres", password="", host=DB_HOST, port=DB_PORT
        )
        return True

    @dbconnect_logger
    def database_exists(self):
        with psycopg2.connect(
            dbname="postgres", user="postgres", host=DB_HOST, port=DB_PORT
        ) as conn:
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
            return cursor.fetchone() is not None

    @dbconnect_logger
    def initialize_database(self, login, password):
        connect_admin = psycopg2.connect(
            dbname="postgres", user="postgres", host=DB_HOST, port=DB_PORT
        )
        connect_admin.set_session(autocommit=True)
        cursor = connect_admin.cursor()
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
        logging.info(f"Database '{DB_NAME}' created successfully.")

        command = [
            "psql",
            "-d",
            DB_NAME,
            "-U",
            "postgres",
            "-h",
            DB_HOST,
            "-p",
            DB_PORT,
            "-f",
            DB_INIT_SCRIPT,
        ]

        env = os.environ.copy()
        env["PGPASSWORD"] = ""

        subprocess.run(command, env=env, check=True)
        logging.info("Database initialized successfully with provided SQL script.")

        connect_admin.close()
        return True

    def show_main_window(self):
        main_window = tk.Tk()
        main_window.title("Main Application Window")
        main_window.geometry("1280x960")

        ttk.Label(main_window, text="Connected to Database!").pack(pady=20)

        # TO-DO: Добавить интерфейс для работы с базой данных

        main_window.mainloop()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    DispatcherBD().run()
