SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE delivery;

DROP ROLE chill_user;

-- Создаем пользователя с ограниченными правами для использования (до этого работает от postgres)
CREATE USER chill_user WITH PASSWORD 'im_just_chill_guy';

-- Создаем базу данных
CREATE DATABASE delivery OWNER chill_user;

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
CREATE SCHEMA delivery_schema AUTHORIZATION chill_user;

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
    price INT NOT NULL,
    stock INT NOT NULL
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
    product_id INT REFERENCES Products(product_id),
    quantity INT NOT NULL
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


-- TO-DO Процедуры для работы с данными


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
