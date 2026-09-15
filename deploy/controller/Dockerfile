FROM python:3.12-slim

WORKDIR /app

COPY main.py .
COPY reconcilers/ ./reconcilers/

RUN pip install --no-cache-dir kopf kubernetes

CMD ["kopf", "run", "/app/main.py"]
