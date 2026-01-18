# syntax=docker/dockerfile:1.4
FROM python:3.14-slim

# Prevent Python from writing pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies with cache mount for faster rebuilds
COPY app/requirements-app.txt requirements-app.txt
COPY requirements-common.txt /requirements-common.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir \
        -r /requirements-common.txt \
        -r requirements-app.txt

# Copy application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
