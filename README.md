# Delivery database project

## How to run

1. В папке `streamlit` создайте файл .env с следующим содержимым:

    ```
    DB_INIT_SCRIPT="database/delivery.sql"
    DB_NAME="delivery"
    DB_HOST="db"
    DB_PORT="5432"
    LOG_PATH="logging_data/delivery_connection.log"
    ADMIN_PASSWORD="chill_owner"
    ADMIN_USERNAME="chill_owner"
    ```

2. Чтобы запустить проект пропишите, скачайте Docker и запустите команду:

    ``` bash
    sudo docker compose up --build
    ```
