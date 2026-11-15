# Planr backend image (needs PLANR_DATABASE_URL)
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

WORKDIR /app

# Dependencies first, so this layer is rebuilt only when pyproject.toml changes.
# The list is read from pyproject.toml (single source of truth); dev dependencies are not installed.
COPY pyproject.toml .
RUN python -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))" > requirements.txt \
    && pip install -r requirements.txt \
    && rm requirements.txt

# Application code and migrations
COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

# Run as an unprivileged user.
RUN useradd --system --uid 10001 --no-create-home planr
USER planr

# Expose backend port
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import socket; socket.create_connection(('127.0.0.1', 8000), 2).close()"]

# Run API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]