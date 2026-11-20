
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --home-dir /app appuser

COPY requirements.lock .

RUN pip install \
    --no-cache-dir \
    --only-binary=:all: \
    --require-hashes \
    -r requirements.lock

COPY app.py models.py forms.py init_db.py ./
COPY templates/ ./templates/
COPY static/ ./static/

RUN mkdir -p /app/instance && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

CMD ["sh", "-c", "python init_db.py && exec gunicorn --bind 0.0.0.0:5000 --workers 2 app:app"]
