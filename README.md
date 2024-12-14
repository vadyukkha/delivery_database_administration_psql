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

3. Чтобы запустить проект пропишите:

    ``` bash
    poetry run streamlit run streamlit/app.py
    ```
