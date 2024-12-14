import os
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk

from dotenv import load_dotenv

from database_functions import DatabaseManager
from logger_decorator import dbconnect_logger, logging, logs

load_dotenv()

DB_INIT_SCRIPT = os.getenv("DB_INIT_SCRIPT", "database/demo_small.sql")
DB_NAME = os.getenv("DB_NAME", "demo")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")


class GUIDispatcherBD:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Login to Database")
        self.root.geometry("400x400")

        self.db_manager = None

        self.create_login_window()

    @logs
    def create_login_window(self):
        ttk.Label(self.root, text="Login:").pack(pady=(20, 5))
        self.login_entry = ttk.Entry(self.root)
        self.login_entry.pack(pady=5)

        ttk.Label(self.root, text="Password:").pack(pady=5)
        self.password_entry = ttk.Entry(self.root, show="*")
        self.password_entry.pack(pady=5)

        login_button = ttk.Button(self.root, text="Login", command=self.authenticate)
        login_button.pack(pady=20)

    @logs
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
            self.initialize_database()

        self.db_manager = DatabaseManager(DB_NAME, login, password, DB_HOST, DB_PORT)
        return True

    @dbconnect_logger
    def database_exists(self):
        admin_connection = DatabaseManager("postgres", "postgres", "", DB_HOST, DB_PORT)
        admin_connection.cursor.execute(
            f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'"
        )
        checker_exist = admin_connection.cursor.fetchone() is not None
        admin_connection.close()
        return checker_exist

    @dbconnect_logger
    def initialize_database(self):
        connect_admin = DatabaseManager("postgres", "postgres", "", DB_HOST, DB_PORT)
        connect_admin.cursor.execute(f"CREATE DATABASE {DB_NAME}")
        logging.info(f"Database '{DB_NAME}' created successfully.")
        connect_admin.close()

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
        return True

    @logs
    def show_main_window(self):
        main_window = tk.Tk()
        main_window.title("Main Application Window")
        main_window.geometry("800x600")

        ttk.Label(
            main_window, text="Connected to Database!", font=("Helvetica", 16)
        ).pack(pady=20)

        # Создаем Frame для кнопок
        button_frame = ttk.Frame(main_window, padding=10)
        button_frame.pack(pady=20)

        # Настройка стиля кнопок
        button_style = {"padding": 5, "width": 30}

        # Обертка для выполнения команд с уведомлениями
        def execute_command(command, success_message):
            logging.info(f"Executing command: {command.__name__}")
            try:
                if command == self.db_manager.show_tables_content:
                    result = command()
                    if result:
                        self.__show_results(result)
                    else:
                        messagebox.showerror("Error", "Database is empty.")
                elif command == self.db_manager.clear_table:
                    self.__request_table_name(command)
                else:
                    command()
                    messagebox.showinfo("Success", success_message)
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {str(e)}")

        # Кнопки CRUD операций
        ttk.Label(
            button_frame, text="Database Operations", font=("Helvetica", 14)
        ).grid(row=0, column=0, columnspan=2, pady=(0, 10))

        ttk.Button(
            button_frame,
            text="Delete Database",
            command=lambda: execute_command(
                self.db_manager.delete_database, "Database deleted successfully!"
            ),
            **button_style,
        ).grid(row=1, column=0, padx=10, pady=5)

        ttk.Button(
            button_frame,
            text="Show Tables Content",
            command=lambda: execute_command(
                self.db_manager.show_tables_content,
                "Tables content displayed successfully!",
            ),
            **button_style,
        ).grid(row=1, column=1, padx=10, pady=5)

        ttk.Button(
            button_frame,
            text="Clear Table",
            command=lambda: execute_command(
                self.db_manager.clear_table, "Table cleared successfully!"
            ),
            **button_style,
        ).grid(row=2, column=0, padx=10, pady=5)

        ttk.Button(
            button_frame,
            text="Clear All Tables",
            command=lambda: execute_command(
                self.db_manager.clear_all_tables, "All tables cleared successfully!"
            ),
            **button_style,
        ).grid(row=2, column=1, padx=10, pady=5)

        # Кнопки для работы с данными
        ttk.Label(button_frame, text="Data Operations", font=("Helvetica", 14)).grid(
            row=3, column=0, columnspan=2, pady=(20, 10)
        )

        ttk.Button(
            button_frame,
            text="Add Data",
            command=lambda: execute_command(
                self.db_manager.add_data, "Data added successfully!"
            ),
            **button_style,
        ).grid(row=4, column=0, padx=10, pady=5)

        ttk.Button(
            button_frame,
            text="Search by Text Field",
            command=lambda: execute_command(
                self.db_manager.search_by_text_field, "Search completed successfully!"
            ),
            **button_style,
        ).grid(row=4, column=1, padx=10, pady=5)

        ttk.Button(
            button_frame,
            text="Update Row",
            command=lambda: execute_command(
                self.db_manager.update_row, "Row updated successfully!"
            ),
            **button_style,
        ).grid(row=5, column=0, padx=10, pady=5)

        ttk.Button(
            button_frame,
            text="Delete by Text Field",
            command=lambda: execute_command(
                self.db_manager.delete_by_text_field, "Data deleted successfully!"
            ),
            **button_style,
        ).grid(row=5, column=1, padx=10, pady=5)

        ttk.Button(
            button_frame,
            text="Delete Specific Record",
            command=lambda: execute_command(
                self.db_manager.delete_specific_record, "Record deleted successfully!"
            ),
            **button_style,
        ).grid(row=6, column=0, columnspan=2, padx=10, pady=5)

        # Button exit
        ttk.Button(
            button_frame,
            text="Exit",
            command=lambda: main_window.destroy(),
            **button_style,
        ).grid(row=7, column=0, columnspan=2, padx=10, pady=5)

        main_window.mainloop()

    def run(self) -> None:
        self.root.mainloop()

    @logs
    def __show_results(self, result):
        # Создаем новое окно для отображения результатов
        self.result_window = tk.Tk()
        self.result_window.title("Tables Content")
        self.result_window.geometry("1024x768")
        self.result_window.resizable(True, True)
        self.result_window.minsize(800, 600)

        # Создаем Canvas для прокрутки
        canvas = tk.Canvas(self.result_window)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Создаем вертикальную прокрутку
        scrollbar = ttk.Scrollbar(
            self.result_window, orient=tk.VERTICAL, command=canvas.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Привязываем прокрутку к Canvas
        canvas.config(yscrollcommand=scrollbar.set)

        # Создаем рамку для всех элементов внутри Canvas
        frame = ttk.Frame(canvas)

        # Размещение рамки в Canvas
        canvas.create_window((0, 0), window=frame, anchor="nw")

        # Обновляем размер Canvas, когда добавляются новые элементы
        def on_frame_configure(event):
            canvas.config(scrollregion=canvas.bbox("all"))

        frame.bind("<Configure>", on_frame_configure)

        for table_name, table_content in result:
            # Добавляем название таблицы
            table_label = ttk.Label(
                frame, text=f"Table: {table_name}", font=("Helvetica", 14, "bold")
            )
            table_label.pack(pady=10)

            # Проверяем, что table_content не пустой
            if not table_content:
                continue

            # Получаем заголовки столбцов из ключей первого элемента
            columns = list(table_content.keys())

            # Создаем рамку для Treeview и Scrollbar
            table_frame = ttk.Frame(frame)
            table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Создаем Scrollbar для Treeview
            scrollbar_vertical = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)

            # Создаем Scrollbar для горизонтальной прокрутки
            scrollbar_horizontal = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)

            # Создаем Treeview для отображения данных
            tree = ttk.Treeview(
                table_frame,
                columns=columns,
                show="headings",
                yscrollcommand=scrollbar_vertical.set,
                xscrollcommand=scrollbar_horizontal.set,
            )

            # Устанавливаем заголовки
            for col in columns:
                tree.heading(col, text=col)

            # Располагаем Treeview в рамке
            tree.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)

            # Связываем Scrollbar с Treeview
            scrollbar_vertical.config(command=tree.yview)
            scrollbar_vertical.pack(side=tk.RIGHT, fill=tk.Y)

            scrollbar_horizontal.config(command=tree.xview)
            scrollbar_horizontal.pack(side=tk.BOTTOM, fill=tk.X)

            # Заполняем данными
            tree.insert("", "end", values=list(table_content.values()))

        # Кнопка выхода
        exit_button = ttk.Button(
            self.result_window, text="Exit", command=self.result_window.destroy
        )
        exit_button.pack(pady=10, side=tk.BOTTOM)

        self.result_window.mainloop()

    @logs
    def __request_table_name(self, cmd):
        # Создаем новое окно для запроса имени таблицы
        self.table_name_window = tk.Tk()
        self.table_name_window.title("Table Name")
        self.table_name_window.geometry("400x200")

        ttk.Label(self.table_name_window, text="Enter Table Name:").pack(pady=20)
        self.table_name_entry = ttk.Entry(self.table_name_window)
        self.table_name_entry.pack(pady=10)

        # Функция для обработки подтверждения
        def on_confirm():
            table_name = self.table_name_entry.get()
            if table_name:
                result = cmd(table_name)
                if result:
                    messagebox.showinfo(
                        "Success", f"Operation successful for table '{table_name}'!"
                    )
                else:
                    messagebox.showerror(
                        "Error", f"Table '{table_name}' does not exist."
                    )
            else:
                messagebox.showwarning("Input Error", "Please enter a table name.")
            self.table_name_window.destroy()  # Закрываем окно после выполнения

        confirm_button = ttk.Button(
            self.table_name_window,
            text="Confirm",
            command=on_confirm,  # Связываем кнопку с обработчиком
        )
        confirm_button.pack(pady=20)

        self.table_name_window.mainloop()


if __name__ == "__main__":
    GUIDispatcherBD().run()
