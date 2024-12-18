# Delivery database project

## How to run

1. В папке `streamlit` создайте файл .env с следующим содержимым:

    ```
    DB_INIT_SCRIPT="database/delivery.sql"
    DB_NAME="delivery"
    LOG_PATH="logging_data/delivery_connection.log"
    ADMIN_PASSWORD="chill_owner"
    ADMIN_USERNAME="chill_owner"
    ```

2. Чтобы запустить проект пропишите:

    ``` bash
    sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    sudo docker compose up --build
    ```
