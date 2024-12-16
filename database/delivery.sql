SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

DROP SCHEMA IF EXISTS delivery_schema CASCADE;

DROP DATABASE IF EXISTS delivery;

DROP ROLE IF EXISTS chill_user;

-- Создаем пользователя с ограниченными правами для использования (до этого работает от chill_owner)
CREATE USER chill_user WITH PASSWORD 'im_just_chill_guy';

-- Создаем базу данных
CREATE DATABASE delivery;

-- Подключаемся к базе данных
\c delivery

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

-- Создаем схему
CREATE SCHEMA delivery_schema AUTHORIZATION chill_owner;

-- Добавляем в search_path
SET search_path TO delivery_schema;

-- Установим search_path на уровне базы данных
ALTER DATABASE delivery SET search_path TO delivery_schema, public;

-- Таблица Users
CREATE TABLE delivery_schema.Users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(50) UNIQUE,
    phone VARCHAR(15) NOT NULL,
    address VARCHAR(100) NOT NULL
);

-- Таблица Products
CREATE TABLE delivery_schema.Products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price INT NOT NULL CONSTRAINT positive_price CHECK (price > 0),
    stock INT NOT NULL CONSTRAINT positive_stock CHECK (stock > 0)
);

-- Таблица Orders
CREATE TABLE delivery_schema.Orders (
    order_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_cost INT DEFAULT 0,
    status VARCHAR(20) NOT NULL
);

-- Таблица OrderItems
CREATE TABLE delivery_schema.OrderItems (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES Orders(order_id) ON DELETE CASCADE,
    product_id INT REFERENCES Products(product_id) ON DELETE CASCADE,
    quantity INT NOT NULL CONSTRAINT positive_quantity CHECK (quantity > 0)
);

-- Индекс по полю name в таблице Products
CREATE INDEX lower_idx_product_name ON Products(lower(name));

-- Индекс по полю name в таблице Users
CREATE INDEX lower_idx_username ON Users(lower(name));

-- Триггер для вычисления общей стоимости заказа
CREATE OR REPLACE FUNCTION delivery_schema.calculate_total_cost() RETURNS TRIGGER AS $$
DECLARE
    current_total_cost INT;
BEGIN
    -- Пересчитываем общую стоимость
    SELECT COALESCE(SUM(p.price * oi.quantity), 0)
    INTO current_total_cost
    FROM delivery_schema.OrderItems oi
    JOIN delivery_schema.Products p ON oi.product_id = p.product_id
    WHERE oi.order_id = COALESCE(NEW.order_id, OLD.order_id); -- Для корректной работы с UPDATE и DELETE

    -- Обновляем поле total_cost
    UPDATE delivery_schema.Orders
    SET total_cost = current_total_cost
    WHERE order_id = COALESCE(NEW.order_id, OLD.order_id);

    -- Обновляем статус заказа в зависимости от total_cost
    IF current_total_cost > 0 THEN
        UPDATE delivery_schema.Orders
        SET status = 'Pending'
        WHERE order_id = COALESCE(NEW.order_id, OLD.order_id);
    ELSE
        UPDATE delivery_schema.Orders
        SET status = 'Created'
        WHERE order_id = COALESCE(NEW.order_id, OLD.order_id);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS calculate_total_cost_trigger ON delivery_schema.OrderItems;

CREATE TRIGGER calculate_total_cost_trigger
AFTER INSERT OR UPDATE OR DELETE ON delivery_schema.OrderItems
FOR EACH ROW
EXECUTE FUNCTION delivery_schema.calculate_total_cost();

-- Триггер для уменьшения количества товара на складе
CREATE OR REPLACE FUNCTION delivery_schema.decrease_product_stock() RETURNS TRIGGER AS $$
BEGIN
    UPDATE Products
    SET stock = stock - NEW.quantity
    WHERE product_id = NEW.product_id;

    -- Проверяем, что stock не стал отрицательным
    IF (SELECT stock FROM Products WHERE product_id = NEW.product_id) < 0 THEN
        RAISE EXCEPTION 'Insufficient stock for product_id %', NEW.product_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER decrease_product_stock_trigger
AFTER INSERT ON delivery_schema.OrderItems
FOR EACH ROW
EXECUTE FUNCTION delivery_schema.decrease_product_stock();

-- Триггер для обновления количества товара на складе
CREATE OR REPLACE FUNCTION delivery_schema.update_product_stock() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.quantity = 0 THEN
        -- Возвращаем товар на склад перед удалением строки
        UPDATE Products
        SET stock = stock + OLD.quantity
        WHERE product_id = OLD.product_id;

        -- Удаляем строку из OrderItems
        DELETE FROM OrderItems WHERE order_item_id = OLD.order_item_id;

        RETURN NULL; -- Указывает, что строка должна быть удалена
    END IF;

    -- Обновляем запасы на складе, если quantity изменилось
    UPDATE Products
    SET stock = stock + OLD.quantity - NEW.quantity
    WHERE product_id = NEW.product_id;

    -- Проверяем, что stock не стал отрицательным
    IF (SELECT stock FROM Products WHERE product_id = NEW.product_id) < 0 THEN
        RAISE EXCEPTION 'Insufficient stock for product_id %', NEW.product_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_product_stock_trigger ON delivery_schema.OrderItems;

CREATE TRIGGER update_product_stock_trigger
BEFORE UPDATE ON delivery_schema.OrderItems
FOR EACH ROW
EXECUTE FUNCTION delivery_schema.update_product_stock();

-- Триггер для удаления позиции в заказе
CREATE OR REPLACE FUNCTION delivery_schema.delete_order_item() RETURNS TRIGGER AS $$
BEGIN
    -- Возвращаем товар на склад перед удалением строки
    UPDATE Products
    SET stock = stock + OLD.quantity
    WHERE product_id = OLD.product_id;

    -- Обновляем общую стоимость заказа
    UPDATE Orders 
    SET total_cost = total_cost - OLD.quantity * (SELECT price FROM Products WHERE product_id = OLD.product_id)
    WHERE order_id = OLD.order_id;

    -- Возвращаем NULL, чтобы позволить стандартное удаление строки
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS delete_order_item_trigger ON delivery_schema.OrderItems;

CREATE TRIGGER delete_order_item_trigger
BEFORE DELETE ON delivery_schema.OrderItems
FOR EACH ROW
EXECUTE FUNCTION delivery_schema.delete_order_item();

-- Даем пользователю chill_user доступ только к чтению и записи данных в схеме
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA delivery_schema TO chill_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA delivery_schema TO chill_user;
GRANT USAGE ON SCHEMA delivery_schema TO chill_user;

-- TO-DO Процедуры для работы с данными

-- Удаление базы данных
CREATE OR REPLACE PROCEDURE drop_delivery_tables()
LANGUAGE plpgsql AS $$
BEGIN
    EXECUTE 'DROP SCHEMA IF EXISTS delivery_schema CASCADE';
END;
$$;

-- Вывод содержимого всех таблиц
CREATE OR REPLACE FUNCTION show_tables_content()
RETURNS TABLE(table_name TEXT, row_content JSON) AS $$
DECLARE
    tbl_name TEXT;
BEGIN
    FOR tbl_name IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'delivery_schema'
    LOOP
        RETURN QUERY EXECUTE FORMAT(
            'SELECT %L AS table_name, row_to_json(t) AS row_content FROM %I t',
            tbl_name,
            tbl_name
        );
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Очистка одной из таблиц(название задается пользователем)
CREATE OR REPLACE PROCEDURE clear_sertain_table(t_name TEXT)
LANGUAGE plpgsql AS $$
DECLARE
  request TEXT;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE TABLE_NAME = t_name) THEN
    RAISE EXCEPTION 'Таблица % не существует.', t_name;
  END IF;

  request := format('DELETE FROM %I;', t_name);
  EXECUTE request;
  RAISE NOTICE 'Таблица % очищена.', t_name;
EXCEPTION
  WHEN OTHERS THEN
    RAISE EXCEPTION 'Ошибка при очистке таблицы %: %', t_name, SQLERRM;
END;
$$;

--Добавление новых данных в таблицу
--Обязательно указывать типы данных(idk why)
--EXAMPLE: SELECT add_info('Levchik'::varchar, 'lew.cherezow@gmail.com'::varchar, '228'::varchar, 'sormovo'::varchar)
CREATE OR REPLACE FUNCTION add_info(p_name VARCHAR(50), p_email VARCHAR(50), p_phone VARCHAR(15), p_address VARCHAR(100))
RETURNS VOID AS $$
BEGIN
    INSERT INTO delivery_schema.Users(name, email, phone, address) VALUES (p_name, p_email, p_phone, p_address);
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Ошибка при добавлении пользователя: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION add_info(p_name VARCHAR(100),p_description TEXT,p_price INT,p_stock INT)
RETURNS VOID AS $$
BEGIN
    INSERT INTO delivery_schema.Products(name, description, price, stock) VALUES (p_name, p_description, p_price, p_stock);
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Ошибка при добавлении пользователя: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION add_info(p_user_id INT, p_status VARCHAR(20), p_total_cost INT DEFAULT 0)
RETURNS VOID AS $$
BEGIN
    INSERT INTO delivery_schema.Orders(user_id, total_cost, status) VALUES (p_user_id, p_total_cost, p_status);
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Ошибка при добавлении пользователя: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION add_info(p_order_id INT, p_product_id INT, p_quantity INT)
RETURNS VOID AS $$
BEGIN
    INSERT INTO delivery_schema.Orderitems(order_id, product_id, quantity) VALUES (p_order_id, p_product_id, p_quantity);
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Ошибка при добавлении пользователя: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Поиск по заданному полю description в таблице Products
CREATE OR REPLACE FUNCTION search_products_by_desc(p_desc TEXT)
RETURNS TABLE(product_id INT, name VARCHAR(100), description TEXT, price INT, stock INT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.product_id,
        p.name,
        p.description,
        p.price,
        p.stock
    FROM 
        delivery_schema.Products p
    WHERE 
        p.description ILIKE '%' || p_desc || '%';
END;
$$ LANGUAGE plpgsql;

--Обновление кортежа
CREATE OR REPLACE FUNCTION update_cortege(p_user_id INT, p_name VARCHAR(50), p_email VARCHAR(50), p_phone VARCHAR(15),p_address VARCHAR(100))
RETURNS VOID AS $$
BEGIN
    UPDATE delivery_schema.Users
    SET name = p_name, email = p_email, phone = p_phone, address = p_address
    WHERE user_id = p_user_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Пользователь с ID % не найден', p_user_id;
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Ошибка при изменении пользователя: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_cortege(p_order_id INT, p_user_id INT, p_status VARCHAR(20))
RETURNS VOID AS $$
BEGIN
    UPDATE delivery_schema.Orders
    SET status = p_status
    WHERE order_id = p_order_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Заказ с ID % не найден', p_order_id;
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Ошибка при изменении заказа: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_cortege(p_order_item_id INT, p_order_id INT, p_product_id INT, p_quantity INT)
RETURNS VOID AS $$
BEGIN
    UPDATE delivery_schema.OrderItems
    SET product_id = p_product_id, quantity = p_quantity
    WHERE order_item_id = p_order_item_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Продукт в заказе с ID % не найден', p_user_item_id;
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Ошибка при добавлении продукта в заказе: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_cortege(p_product_id INT, p_name TEXT, p_description TEXT, p_stock INT)
RETURNS VOID AS $$
BEGIN
    UPDATE delivery_schema.Products
    SET name = p_name, description = p_description, stock = p_stock
    WHERE product_id = p_product_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Продукт с ID % не найден', p_product_id;
    END IF;
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Ошибка при добавлении продукта: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Очистка всех таблиц
CREATE OR REPLACE PROCEDURE clear_all_tables()
LANGUAGE plpgsql AS $$
BEGIN
  DELETE FROM delivery_schema.users;
  DELETE FROM delivery_schema.orders;
  DELETE FROM delivery_schema.orderitems;
  DELETE FROM delivery_schema.products;
  RAISE NOTICE 'Таблицы в схеме delivery_schema очищены.';
EXCEPTION WHEN OTHERS THEN
  RAISE EXCEPTION 'Ошибка при очистке таблиц в схеме delivery_schema: %', SQLERRM;
END;
$$;

-- Удаление по заданному полю description в таблице Products
CREATE OR REPLACE PROCEDURE delete_products_by_desc(p_desc TEXT)
LANGUAGE plpgsql AS $$
DECLARE
  v_desc TEXT;
  rec RECORD;
BEGIN
  v_desc:= '%' || p_desc || '%';

  FOR rec IN SELECT product_id, name, description, price, stock
  FROM delivery_schema.Products
  WHERE description ILIKE v_desc
  LOOP
    DELETE FROM delivery_schema.Products
    WHERE product_id = rec.product_id;
  END LOOP;

EXCEPTION WHEN OTHERS THEN
  RAISE EXCEPTION 'Ошибка при поиске товаров: %', SQLERRM;
END;
$$;

-- Удаление записи по имени таблицы и айди записи
CREATE OR REPLACE PROCEDURE delete_specific_record(t_name TEXT, id INT)
LANGUAGE plpgsql AS $$
BEGIN
    IF t_name = 'users' THEN
        DELETE FROM delivery_schema.Users WHERE user_id = id;
    ELSIF t_name = 'products' THEN
        DELETE FROM delivery_schema.Products WHERE product_id = id;
    ELSIF t_name = 'orderitems' THEN
        DELETE FROM delivery_schema.OrderItems WHERE order_item_id = id;
    ELSIF t_name = 'orders' THEN
        DELETE FROM delivery_schema.Orders WHERE order_id = id;
    ELSE
        RAISE EXCEPTION 'Table "%s" is not allowed for deletion.', t_name;
    END IF;

    RAISE NOTICE 'Record with id % from table % successfully deleted.', id, t_name;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error while deleting record: %', SQLERRM;
END;
$$;


-- Заполнение таблиц

-- Добавляем пользователя в таблицу Users
INSERT INTO delivery_schema.Users (name, email, phone, address)
VALUES ('vadim', 'mvarodi@main.ru', '911', 'kirov');

-- Добавляем продукт в таблицу Products
INSERT INTO delivery_schema.Products (name, description, price, stock)
VALUES ('BanAna', 'Банан 1кг', 200, 5);

-- Добавляем заказ в таблицу Orders
INSERT INTO delivery_schema.Orders (user_id, status)
VALUES (1, 'Created');

-- Добавляем элемент заказа в таблицу OrderItems
INSERT INTO delivery_schema.OrderItems (order_id, product_id, quantity)
VALUES (1, 1, 2);
