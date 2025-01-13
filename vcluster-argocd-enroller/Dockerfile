# Build stage
FROM python:3.13-slim AS builder

WORKDIR /app

# Install Pipenv and system dependencies
RUN pip install pipenv
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install project dependencies
RUN pipenv install --system --deploy

# Runtime stage
FROM python:3.13-slim

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

# Copy the application code
COPY . .

# Set the entry point
CMD ["python", "app.py"]
