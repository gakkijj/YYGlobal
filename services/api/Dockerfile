FROM python:3.12-slim

ARG PIP_INDEX_URL=https://pypi.org/simple

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY services/api/pyproject.toml ./pyproject.toml
RUN mkdir -p app \
    && touch app/__init__.py \
    && pip install --no-cache-dir --retries 5 --timeout 60 --index-url ${PIP_INDEX_URL} . \
    && find app -depth -delete
COPY services/api/app ./app
COPY services/api/alembic.ini ./alembic.ini
COPY services/api/alembic ./alembic

RUN mkdir -p /data/uploads
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
