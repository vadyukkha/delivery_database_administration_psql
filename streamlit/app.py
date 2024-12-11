import os
import subprocess

import pandas as pd
from db_procedures import DatabaseManager
from dotenv import load_dotenv
from logger import logging, logs
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

import streamlit as st

load_dotenv()

DB_INIT_SCRIPT = os.getenv("DB_INIT_SCRIPT", "database/demo_small.sql")
DB_NAME = os.getenv("DB_NAME", "demo")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


class StreamlitDatabaseApp:
    def __init__(self):
        self.db_manager = None

    @logs
    def authenticate(self, login, password):
        """Authenticate user with database."""
        if not login or not password:
            st.warning("Please enter both login and password.")
            return False

        if self.connect_to_db(login, password):
            st.success(f"Successfully logged in {DB_NAME} as {login}!")
            st.session_state.logged_in = True
            st.session_state.username = login
            logging.info(f"User '{login}' logged in '{DB_NAME}' successfully.")
            return True
        else:
            st.error("Failed to connect to the database with the provided credentials.")
            return False

    @logs
    def connect_to_db(self, login, password):
        """Connect to the database."""
        if not self.database_exists():
            self.initialize_database()

        try:
            if "db_manager" not in st.session_state:
                self.db_manager = DatabaseManager(
                    DB_NAME, login, password, DB_HOST, DB_PORT
                )
                st.session_state.db_manager = self.db_manager
            else:
                self.db_manager = st.session_state.db_manager

            logging.debug(
                f"Database type: {type(self.db_manager)} Database: {self.db_manager}"
            )
            return self.db_manager.test_connection()
        except Exception as e:
            logging.error(f"Error connecting to the database: {e}")
            st.error(f"Failed to connect to the database: {e}")
            return False

    @logs
    def database_exists(self):
        """Check if the database exists."""
        try:
            admin_engine = create_engine(
                f"postgresql://postgres:{ADMIN_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres",
                isolation_level="AUTOCOMMIT",
            )
            with admin_engine.connect() as conn:
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                    {"db_name": DB_NAME},
                )
                return result.scalar() is not None
        except SQLAlchemyError as e:
            logging.error(f"Error checking database existence: {e}")
            return False

    @logs
    def initialize_database(self):
        """Initialize the database using SQL script."""
        try:
            admin_engine = create_engine(
                f"postgresql://postgres:{ADMIN_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres",
                isolation_level="AUTOCOMMIT",
            )
            with admin_engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
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
            env["PGPASSWORD"] = ADMIN_PASSWORD

            subprocess.run(command, env=env, check=True)
            logging.info("Database initialized successfully with provided SQL script.")
            return True
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
            st.error("Failed to initialize database.")
            return False

    def show_main_interface(self):
        """Main interface for database operations."""

        if "db_manager" in st.session_state:
            self.db_manager = st.session_state.db_manager
        else:
            st.error("Database manager is not initialized.")
            return

        if st.session_state.logged_in:
            st.sidebar.title(
                f"Username - {st.session_state.username}\nDatabase - {DB_NAME}"
            )
            if st.sidebar.button("Logout"):
                st.session_state.logged_in = False
                st.success("Logged out successfully.")
                logging.info(
                    f"User {st.session_state.username} logged out successfully."
                )
                st.session_state.username = None
                self.db_manager.close()
                st.rerun()

        st.sidebar.title("Database Operations")
        operation = st.sidebar.radio(
            "Choose an operation",
            [
                "Show Tables Content",
                "Clear Table",
                "Clear All Tables",
                "Delete Database",
                "Add Data",
                "Search by Text Field",
                "Update Row",
                "Delete by Text Field",
                "Delete Specific Record",
            ],
            key="operation_selectbox",
        )

        if operation == "Show Tables Content":
            logging.debug(
                f"Database type: {type(self.db_manager)} Database: {self.db_manager}"
            )
            result = self.db_manager.show_tables_content()
            if result:
                self.__show_results(result)
            else:
                st.error("Database is empty.")

        elif operation == "Clear Table":
            table_name = st.text_input("Enter table name to clear")
            if st.button("Clear Table"):
                if table_name:
                    if self.db_manager.clear_table(table_name):
                        st.success(f"Table '{table_name}' cleared successfully!")
                    else:
                        st.error(f"Failed to clear table '{table_name}'.")
                else:
                    st.warning("Please enter a table name.")

        elif operation == "Clear All Tables":
            if st.button("Clear All Tables"):
                self.db_manager.clear_all_tables()
                st.success("All tables cleared successfully!")

        elif operation == "Delete Database":
            if st.button("Delete Database"):
                logging.info("Button 'Delete Database' pressed")
                self.db_manager.delete_database()
                st.success("Database deleted successfully!")

        elif operation == "Add Data":
            table_name = st.text_input("Enter table name to add row")
            updates = st.text_area(
                "Enter data as JSON. For example: {'name': 'New Name', 'email': 'new_email@example.com', 'phone': '1234567890', 'address': 'Moscow'}"
            )
            if st.button("Add Data"):
                updates_dict = eval(updates)
                if self.db_manager.add_data(table_name, updates_dict):
                    st.success("Data added successfully!")
                else:
                    st.error(f"Failed to add data to table '{table_name}'.")

        elif operation == "Search by Text Field":
            query = st.text_input("Search by text field in Products table")
            if st.button("Search"):
                result = self.db_manager.search_by_text_field(query)
                if result:
                    self.__show_results(result)
                else:
                    st.warning("No matching results found.")

        elif operation == "Update Row":
            table_name = st.text_input("Enter table name to update row")
            row_id = st.text_input("Enter row ID to update")
            updates = st.text_area(
                "Enter updates as JSON. For example: {'user_id': 1, 'name': 'New Name', 'email': 'new_email@example.com', 'phone': '1234567890', 'address': 'Moscow'}"
            )
            if st.button("Update Row"):
                updates_dict = eval(updates)
                self.db_manager.update_row(table_name, row_id, updates_dict)
                st.success(
                    f"Row '{row_id}' in table '{table_name}' updated successfully!"
                )

        elif operation == "Delete by Text Field":
            query = st.text_input("Enter text field value to delete")
            if st.button("Delete"):
                self.db_manager.delete_by_text_field(query)
                st.success(f"Records with text field '{query}' deleted successfully!")

        elif operation == "Delete Specific Record":
            table_name = st.text_input("Enter table name to delete record from")
            record_id = st.text_input("Enter record ID to delete")
            if st.button("Delete Record"):
                self.db_manager.delete_specific_record(table_name, record_id)
                st.success(
                    f"Record '{record_id}' from '{table_name}' deleted successfully!"
                )

    @logs
    def __show_results(self, result):
        """Display results in a table format."""
        if not result:
            st.write("No results found.")
            return False

        if len(result[0]) != 2:
            df = pd.DataFrame(result)
            st.write(df)
            logging.info("Results displayed successfully.")
            return True

        all_passed = True
        tables_data = {}
        for table_name, table_content in result:
            if table_name not in tables_data:
                tables_data[table_name] = []
            tables_data[table_name].append(table_content)

        for table_name, table_content in tables_data.items():
            st.subheader(f"{table_name.capitalize()}")
            dfs = []
            for data_content in table_content:
                df = pd.DataFrame([data_content])
                dfs += [df]
                logging.info("Results displayed successfully.")
                if df.empty:
                    all_passed = False
            final_df = pd.concat(dfs)
            st.write(final_df)
        return all_passed

    def run(self):
        """Run the Streamlit app."""
        st.title("Database Manager Application")

        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False

        if not st.session_state.logged_in:
            self.show_login_interface()

        if st.session_state.logged_in:
            self.show_main_interface()

    def show_login_interface(self):
        """Отображение интерфейса для входа и выхода."""
        st.subheader("Login to Database")
        login = st.text_input("Login", "")
        password = st.text_input("Password", "", type="password")

        if not st.session_state.logged_in:
            if st.button("Login"):
                if self.authenticate(login, password):
                    st.session_state.logged_in = True
                    st.rerun()


if __name__ == "__main__":
    app = StreamlitDatabaseApp()
    app.run()
