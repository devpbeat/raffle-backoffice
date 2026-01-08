
# Use official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY pyproject.toml .
# We use pip to install from pyproject.toml, but we also need psycopg2 and gunicorn for production
RUN pip install --upgrade pip
RUN pip install .
RUN pip install psycopg2-binary dj-database-url gunicorn

# Copy project
COPY . .

# Run entrypoint.sh
COPY ./entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
