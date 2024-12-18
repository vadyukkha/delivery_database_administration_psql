from logger import logging, logs
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker


class DatabaseManager:
    def __init__(
        self, db_name, db_user, db_password, db_host="localhost", db_port="5432"
    ):
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        self.engine = create_engine(db_url, isolation_level="AUTOCOMMIT")
        self.metadata = MetaData()
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    @logs
    def test_connection(self):
        query = text("SELECT 1")
        try:
            with self.engine.connect() as conn:
                return self.__safe_execute(conn, query, None)
        except SQLAlchemyError as e:
            logging.error(f"Error testing connection: {e}")
            return False

    @logs
    def delete_database(self):
        """Удаление базы данных"""
        query = text("CALL delivery_init_schema.drop_delivery_tables();")
        try:
            with self.engine.connect() as conn:
                logging.debug(f"Dropping database {self.engine.url.database}")
                self.__safe_execute(conn, query, None)
            return True
        except SQLAlchemyError as e:
            logging.error(f"Error deleting database: {e}")
            return False

    @logs
    def show_tables_content(self):
        """Вывод содержимого таблиц"""
        query = text("SELECT * FROM delivery_schema.show_tables_content();")
        try:
            with self.engine.connect() as conn:
                result = self.__safe_execute(conn, query, None)
                return result.fetchall()
        except SQLAlchemyError as e:
            logging.error(f"Error showing tables content: {e}")
            return []

    @logs
    def clear_table(self, table_name):
        """Очистка одной таблицы"""
        if table_name not in ["products", "users", "orderitems", "orders"]:
            logging.error(f"Error clearing table: table '{table_name}' not found")
            return False

        query = text("CALL delivery_schema.clear_sertain_table(:table_name);")
        params = {"table_name": table_name.lower()}
        try:
            with self.engine.connect() as conn:
                logging.debug(f"Clearing table '{table_name.lower()}'")
                self.__safe_execute(conn, query, params)
            return True
        except SQLAlchemyError as e:
            logging.error(f"Error clearing table {table_name}: {e}")
            return False

    @logs
    def clear_all_tables(self):
        """Очистка всех таблиц"""
        query = text("CALL delivery_schema.clear_all_tables();")
        try:
            with self.engine.connect() as conn:
                logging.debug("Clearing all tables")
                self.__safe_execute(conn, query, None)
            return True
        except SQLAlchemyError as e:
            logging.error(f"Error clearing all tables: {e}")
            return False

    @logs
    def add_data(self, table_name, data):
        """Добавление новых данных"""
        if not table_name or not data:
            return False

        if table_name not in ["products", "users", "orderitems", "orders"]:
            logging.error(f"Error clearing table: table '{table_name}' not found")
            return False

        params = {}
        query = ""
        logging.debug(f"Adding data to table '{table_name.lower()}'")
        if table_name.lower() == "products":
            params = {
                "name": data["name"],
                "description": data["description"],
                "price": data["price"],
                "stock": data["stock"],
            }
            query = text(
                "SELECT delivery_schema.add_info(:name, :description, :price, :stock);"
            )
        elif table_name.lower() == "users":
            params = {
                "name": data["name"],
                "email": data["email"],
                "phone": data["phone"],
                "address": data["address"],
            }
            query = text(
                "SELECT delivery_schema.add_info(CAST(:name AS varchar), CAST(:email AS varchar), CAST(:phone AS varchar), CAST(:address AS varchar));"
            )
        elif table_name.lower() == "orderitems":
            params = {
                "order_id": data["order_id"],
                "product_id": data["product_id"],
                "quantity": data["quantity"],
            }
            query = text(
                "SELECT delivery_schema.add_info(:order_id, :product_id, :quantity);"
            )
        elif table_name.lower() == "orders":
            params = {
                "user_id": data["user_id"],
                "status": data["status"],
            }
            query = text("SELECT delivery_schema.add_info(:user_id, :status);")
        else:
            logging.error(f"Error adding data: table '{table_name.lower()}' not found")
            return False

        try:
            with self.engine.connect() as conn:
                logging.debug(
                    f"Adding data to table '{table_name.lower()}' with query: '{query}'"
                )
                return self.__safe_execute(conn, query, params)
        except SQLAlchemyError as e:
            logging.error(f"Error adding data: {e}")
            return False

    @logs
    def search_by_text_field(self, request_msg_desc):
        """Поиск по заранее выбранному (вами) текстовому не ключевому полю"""
        query = text(
            "SELECT * FROM delivery_schema.search_products_by_desc(:description);"
        )
        params = {"description": request_msg_desc}

        try:
            with self.engine.connect() as conn:
                logging.debug(f"Searching by text '{request_msg_desc}'")
                result = self.__safe_execute(conn, query, params)
                return result.fetchall()
        except SQLAlchemyError as e:
            logging.error(f"Error searching by text field: {e}")
            return False

    @logs
    def update_row(self, table_name, key, data):
        """Обновление кортежа"""
        if not table_name or not data or not key:
            return False

        if table_name not in ["products", "users", "orderitems", "orders"]:
            logging.error(f"Error updating row: table '{table_name}' not found")
            return False

        if not isinstance(key, int):
            logging.error(f"Error updating row: key '{key}' is not an integer")
            return False

        query = ""
        params = {}
        try:
            logging.debug(
                f"Updating row with key '{key}' in table '{table_name.lower()}'"
            )
            if table_name.lower() == "product":
                params = {
                    "key": key,
                    "name": data["name"],
                    "description": data["description"],
                    "price": data["price"],
                }
                query = text(
                    "SELECT delivery_schema.update_cortege(:key, :name, :description, :price);"
                )
            elif table_name.lower() == "users":
                params = {
                    "key": key,
                    "name": data["name"],
                    "email": data["email"],
                    "phone": data["phone"],
                    "address": data["address"],
                }
                query = text(
                    "SELECT delivery_schema.update_cortege(:key, :name, :email, :phone, :address);"
                )
            elif table_name.lower() == "orderitems":
                params = {
                    "key": key,
                    "order_id": data["order_id"],
                    "product_id": data["product_id"],
                    "quantity": data["quantity"],
                }
                query = text(
                    "SELECT delivery_schema.update_cortege(:key, :order_id, :product_id, :quantity);"
                )
            elif table_name.lower() == "orders":
                params = {
                    "key": key,
                    "user_id": data["user_id"],
                    "status": data["status"],
                }
                query = text(
                    "SELECT delivery_schema.update_cortege(:key, :user_id, :status);"
                )
        except Exception as e:
            logging.error(f"Error updating row: {e}")
            return False

        try:
            with self.engine.connect() as conn:
                logging.debug(
                    f"Updating row with key '{key}' in table '{table_name.lower()}'"
                )
                return self.__safe_execute(conn, query, params)
        except SQLAlchemyError as e:
            logging.error(f"Error updating row: {e}")
            return False

    @logs
    def delete_by_text_field(self, request_msg_desc):
        """Удаление по заранее выбранному текстовому не ключевому полю"""
        query = text("CALL delivery_schema.delete_products_by_desc(:description);")
        params = {"description": request_msg_desc}

        try:
            with self.engine.connect() as conn:
                logging.debug(f"Deleting by text '{request_msg_desc}'")
                self.__safe_execute(conn, query, params)
            return True
        except SQLAlchemyError as e:
            logging.error(f"Error deleting by text field: {e}")
            return False

    @logs
    def delete_specific_record(self, table_name, key):
        """Удаление конкретной записи, выбранной пользователем"""
        if not table_name or not key:
            return False

        if table_name not in ["products", "users", "orderitems", "orders"]:
            logging.error(
                f"Error deleting specific record: table '{table_name}' not found"
            )
            return False

        if not isinstance(key, int):
            logging.error(
                f"Error deleting specific record: key '{key}' is not an integer"
            )
            return False

        query = text("CALL delivery_schema.delete_specific_record(:table_name, :key);")
        params = {"table_name": table_name.lower(), "key": key}
        try:
            with self.engine.connect() as conn:
                logging.debug(
                    f"Deleting record with key '{key}' from table '{table_name.lower()}'"
                )
                self.__safe_execute(conn, query, params)
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

    @logs
    def __safe_execute(self, conn, query, params):
        for k, v in params.items():
            if ";" in v or "--" in v:
                logging.error("Invalid characters in input")
                raise ValueError("Invalid characters in input")
            if k != "description":
                params[k] = v.strip()

        try:
            if params is None:
                return conn.execute(query)
            return conn.execute(query, params)
        except SQLAlchemyError as e:
            logging.error(f"SQL execution failed: {e}")
            return False
