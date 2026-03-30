FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y build-essential libffi-dev libssl-dev gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install python deps
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt gunicorn

# copy application (both backend + frontend)
COPY backend /app/backend
COPY frontend /app/frontend

WORKDIR /app/backend

# persistent sqlite storage (optional mount)
RUN mkdir -p /data && chown -R root:root /data

EXPOSE 5000

CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]
