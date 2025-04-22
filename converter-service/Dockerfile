# Stage 1: Build stagee
FROM python:3.10-slim-bullseye AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends --no-install-suggests build-essential libpq-dev python3-dev ffmpeg && pip install --no-cache-dir --upgrade pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

WORKDIR /app
COPY ./requirements.txt /app/
RUN pip install --no-cache-dir --requirement /app/requirements.txt

# Stage 2: Final stage
FROM python:3.10-slim-bullseye

RUN adduser --disabled-password --gecos "" appuser

WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY . /app

USER appuser

CMD ["python", "consumer.py"]
