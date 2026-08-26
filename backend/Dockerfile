FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .
RUN chmod +x scripts/start.sh

CMD ["sh", "scripts/start.sh"]
