# Dockerfile for building_maintenance_agents FastAPI server
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./

RUN pip install --upgrade pip && pip install --no-cache-dir .

COPY . /app

RUN mkdir -p /app/server_logs

EXPOSE 80

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "80"]
