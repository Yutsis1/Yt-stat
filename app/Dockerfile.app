# syntax=docker/dockerfile:1.4
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY app/requirements-app.txt requirements-app.txt
COPY requirements-common.txt /requirements-common.txt

RUN --mount=type=cache,id=pip-cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
        -r /requirements-common.txt \
        -r requirements-app.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
