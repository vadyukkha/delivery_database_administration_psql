import psycopg2


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
    def delete_database(self):
        pass

    # Вывод содержимого таблиц
    def show_tables_content(self):
        pass

    # Очистка одной таблицы
    def clear_table(self):
        pass

    # Очистка всех таблиц
    def clear_all_tables(self):
        pass

    # Добавление новых данных
    def add_data(self):
        pass

    # Поиск по заранее выбранному (вами) текстовому не ключевому полю
    def search_by_text_field(self):
        pass

    # Обновление кортежа
    def update_row(self):
        pass

    # Удаление по заранее выбранному текстовому не ключевому полю
    def delete_by_text_field(self):
        pass

    # Удаление конкретной записи, выбранной пользователем
    def delete_specific_record(self):
        pass

    def close(self):
        self.cursor.close()
        self.connection.close()
