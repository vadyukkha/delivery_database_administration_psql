FROM python:3.11.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get clean \
    && pip install --no-cache-dir poetry poetry==1.8.3

COPY ./pyproject.toml ./poetry.lock /app/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

COPY streamlit /app/streamlit
COPY .streamlit /app/.streamlit
COPY database /app/database

CMD ["sh", "-c", \
     "poetry run streamlit run streamlit/app.py --server.port=8502 --server.address=0.0.0.0"]
