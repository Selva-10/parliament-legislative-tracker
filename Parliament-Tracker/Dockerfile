FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p staticfiles media logs

# Collect static files (will be done at runtime)
# RUN python manage.py collectstatic --noinput

# Run migrations and start server (will be done via command)
CMD ["gunicorn", "parliament.wsgi:application", "--bind", "0.0.0.0:8000"]
