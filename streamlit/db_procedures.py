from logger import logging, logs
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker


class DatabaseManager:
    def __init__(
        self, db_name, db_user, db_password, db_host="localhost", db_port="5432"
    ):
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        self.engine = create_engine(db_url)
        self.metadata = MetaData()
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    @logs
    def test_connection(self):
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            logging.error(f"Error testing connection: {e}")
            return False

    @logs
    def delete_database(self):
        """Удаление базы данных"""
        try:
            with self.engine.connect() as conn:
                logging.debug(f"Dropping database {self.engine.url.database}")
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                    text("CALL drop_delivery_tables();")
                )
            return True
        except SQLAlchemyError as e:
            logging.error(f"Error deleting database: {e}")
            return False

    @logs
    def show_tables_content(self):
        """Вывод содержимого таблиц"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT * FROM show_tables_content();"))
                return result.fetchall()
        except SQLAlchemyError as e:
            logging.error(f"Error showing tables content: {e}")
            return []

    @logs
    def clear_table(self, table_name):
        """Очистка одной таблицы"""
        try:
            with self.engine.connect() as conn:
                logging.debug(f"Clearing table '{table_name.lower()}'")
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                    text(f"CALL clear_sertain_table('{table_name.lower()}');")
                )
            return True
        except SQLAlchemyError as e:
            logging.error(f"Error clearing table {table_name}: {e}")
            return False

    @logs
    def clear_all_tables(self):
        """Очистка всех таблиц"""
        try:
            with self.engine.connect() as conn:
                logging.debug("Clearing all tables")
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                    text("CALL clear_all_tables();")
                )
            return True
        except SQLAlchemyError as e:
            logging.error(f"Error clearing all tables: {e}")
            return False

    @logs
    def add_data(self, table_name, data):
        """Добавление новых данных"""
        if not table_name or not data:
            return False

        query = ""
        logging.debug(f"Adding data to table '{table_name.lower()}'")
        if table_name.lower() == "product":
            name = data["name"]
            description = data["description"]
            price = data["price"]
            stock = data["stock"]
            query = f"SELECT add_info('{name}', '{description}', {price}, {stock});"
        elif table_name.lower() == "users":
            name = data["name"]
            email = data["email"]
            phone = data["phone"]
            address = data["address"]
            query = f"SELECT add_info('{name}'::varchar, '{email}'::varchar, '{phone}'::varchar, '{address}'::varchar);"
        elif table_name.lower() == "orderitems":
            order_id = data["order_id"]
            product_id = data["product_id"]
            quantity = data["quantity"]
            query = f"SELECT add_info({order_id}, {product_id}, {quantity});"
        elif table_name.lower() == "orders":
            user_id = data["user_id"]
            status = data["status"]
            query = f"SELECT add_info({user_id}, '{status}');"
        else:
            logging.error(f"Error adding data: table '{table_name.lower()}' not found")
            return False

        try:
            with self.engine.connect() as conn:
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                    text(query)
                )
            return True
        except SQLAlchemyError as e:
            logging.error(f"Error adding data: {e}")
            return False

    @logs
    def search_by_text_field(self, request_msg_desc):
        """Поиск по заранее выбранному (вами) текстовому не ключевому полю"""
        try:
            with self.engine.connect() as conn:
                logging.debug(f"Searching by text '{request_msg_desc}'")
                result = conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                    text(
                        f"SELECT * FROM search_products_by_desc('{request_msg_desc}');"
                    )
                )
                return result.fetchall()
        except SQLAlchemyError as e:
            logging.error(f"Error searching by text field: {e}")
            return False

    @logs
    def update_row(self, table_name, key, data):
        """Обновление кортежа"""
        if not table_name or not data or not key:
            return False

        query = ""
        try:
            logging.debug(
                f"Updating row with key '{key}' in table '{table_name.lower()}'"
            )
            if table_name.lower() == "product":
                name = data["name"]
                description = data["description"]
                price = data["price"]
                query = (
                    f"SELECT update_cortege({key}, '{name}', '{description}', {price});"
                )
            elif table_name.lower() == "users":
                name = data["name"]
                email = data["email"]
                phone = data["phone"]
                address = data["address"]
                query = f"SELECT update_cortege({key}, '{name}', '{email}', '{phone}', '{address}');"
            elif table_name.lower() == "orderitems":
                order_id = data["order_id"]
                product_id = data["product_id"]
                quantity = data["quantity"]
                query = f"SELECT update_cortege({key}, {order_id}, {product_id}, {quantity});"
            elif table_name.lower() == "orders":
                user_id = data["user_id"]
                status = data["status"]
                query = f"SELECT update_cortege({key}, {user_id}, '{status}');"
        except Exception as e:
            logging.error(f"Error updating row: {e}")
            return False

        try:
            with self.engine.connect() as conn:
                logging.debug(
                    f"Updating row with key '{key}' in table '{table_name.lower()}'"
                )
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                    text(query)
                )
            return True
        except SQLAlchemyError as e:
            logging.error(f"Error updating row: {e}")
            return False

    @logs
    def delete_by_text_field(self, request_msg_desc):
        """Удаление по заранее выбранному текстовому не ключевому полю"""
        try:
            with self.engine.connect() as conn:
                logging.debug(f"Deleting by text '{request_msg_desc}'")
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                    text(f"CALL delete_products_by_desc('{request_msg_desc}');")
                )
            return True
        except SQLAlchemyError as e:
            logging.error(f"Error deleting by text field: {e}")
            return False

    @logs
    def delete_specific_record(self, table_name, key):
        """Удаление конкретной записи, выбранной пользователем"""
        try:
            with self.engine.connect() as conn:
                logging.debug(
                    f"Deleting record with key '{key}' from table '{table_name.lower()}'"
                )
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                    text(
                        f"CALL delete_specific_record('{table_name.lower()}', '{key}');"
                    )
                )
            return True
        except SQLAlchemyError as e:
            logging.error(f"Error deleting specific record: {e}")
            return False

    @logs
    def close(self):
        """Закрываем сессию и соединение с базой данных"""
        if self.session:
            # Закрытие всех активных транзакций, если они есть
            try:
                self.session.commit()
            except SQLAlchemyError:
                self.session.rollback()  # В случае ошибки откатываем изменения

            # Закрытие сессии
            self.session.close()
            self.session = None

        # Закрытие соединения с базой данных, если оно было установлено
        if self.engine:
            self.engine.dispose()
