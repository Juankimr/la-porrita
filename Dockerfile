FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy project files
COPY . .

# Make scripts executable
RUN chmod +x /app/entrypoint.sh
RUN chmod +x /app/cronjob

# Install cron job
RUN crontab /app/cronjob

# Collect static files
RUN .venv/bin/python manage.py collectstatic --noinput

# Create log directory
RUN mkdir -p /var/log/cron && touch /var/log/cron/pool-sync.log

# Expose port
EXPOSE 8000

# Use entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Start cron in background and run gunicorn
CMD ["sh", "-c", "cron && .venv/bin/gunicorn porrita.wsgi:application --bind 0.0.0.0:8000"]
