import psycopg2

from logger_decorator import logs


class DatabaseManager:
    def __init__(
        self, db_name, db_user, db_password, db_host="localhost", db_port="5432"
    ):
        self.connection = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        self.connection.autocommit = True
        self.cursor = self.connection.cursor()

    # Удаление базы данных
    @logs
    def delete_database(self):
        self.cursor.execute("CALL delete_database();")
        return True

    # Вывод содержимого таблиц
    @logs
    def show_tables_content(self):
        self.cursor.execute("SELECT * FROM show_tables_content();")
        results = self.cursor.fetchall()
        return results

    # Очистка одной таблицы
    @logs
    def clear_table(self, table_name):
        try:
            self.cursor.execute(
                f"CALL clear_sertain_table('{str(table_name).lower()}');"
            )
        except Exception:
            return False
        return True

    # Очистка всех таблиц
    @logs
    def clear_all_tables(self):
        pass

    # Добавление новых данных
    @logs
    def add_data(self):
        pass

    # Поиск по заранее выбранному (вами) текстовому не ключевому полю
    @logs
    def search_by_text_field(self):
        pass

    # Обновление кортежа
    @logs
    def update_row(self):
        pass

    # Удаление по заранее выбранному текстовому не ключевому полю
    @logs
    def delete_by_text_field(self):
        pass

    # Удаление конкретной записи, выбранной пользователем
    @logs
    def delete_specific_record(self):
        pass

    def close(self):
        self.cursor.close()
        self.connection.close()
