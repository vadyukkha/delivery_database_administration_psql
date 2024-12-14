# Delivery database project

## How to run

1. Создайте виртуальное окружение `.venv` из корня проекта и запустите его:

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2. Установите зависимости из `requirements.txt`:

    ```bash
    pip install -r requirements.txt
    ```

3. В папке `streamlit` создайте файл .env с следующим содержимым:

    ```
    DB_INIT_SCRIPT="database/delivery.sql"
    DB_NAME="delivery"
    LOG_PATH="logging_data/delivery_connection.log"
    ADMIN_PASSWORD=ВВЕДИТЕ_ЗДЕСЬ_СВОЙ_ПАРОЛЬ_ОТ_ПОЛЬЗОВАТЕЛЯ_ПОСТГРЕС
    ```

4. Чтобы запустить проект пропишите:

    ``` bash
    poetry run streamlit run streamlit/app.py
    ```
