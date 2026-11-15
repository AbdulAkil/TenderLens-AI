FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .[dev]
COPY alembic.ini ./
COPY alembic ./alembic
COPY tests ./tests
RUN useradd --create-home --uid 10001 tenderlens
USER tenderlens
CMD ["uvicorn", "tenderlens.main:app", "--host", "0.0.0.0", "--port", "8000"]
