# Mullm: nlp2cmd HTTP API (build context = parent dir wronai, see docker-compose).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    NLP2CMD_HOST=0.0.0.0 \
    NLP2CMD_PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY nlp2cmd/pyproject.toml nlp2cmd/README.md nlp2cmd/LICENSE ./
COPY nlp2cmd/src ./src/

RUN pip install --no-cache-dir -e ".[service]"

EXPOSE 8000
HEALTHCHECK CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["python", "-c", "from nlp2cmd.service import NLP2CMDService, ServiceConfig; NLP2CMDService(ServiceConfig()).run(host='0.0.0.0', port=8000)"]
