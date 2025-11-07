# Dockerfile
FROM python:3.10-slim

# Install ffmpeg and system deps
RUN apt-get update && apt-get install -y ffmpeg git gcc libsndfile1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
