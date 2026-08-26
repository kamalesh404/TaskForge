FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

ENV TASKFORGE_CONFIG=/app/taskforge.yml
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["taskforge", "worker", "start", "--backend", "redis://redis:6379"]