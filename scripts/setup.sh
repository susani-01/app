#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p data

if [[ ! -f data/construction_classification.jsonl ]]; then
  echo "Downloading construction_classification.jsonl..."
  curl -fsSL -o data/construction_classification.jsonl \
    https://storage.googleapis.com/timwork-hiring-data/construction-price/construction_classification.jsonl
fi

if [[ ! -f data/std_market_price.jsonl ]]; then
  echo "Downloading std_market_price.jsonl..."
  curl -fsSL -o data/std_market_price.jsonl \
    https://storage.googleapis.com/timwork-hiring-data/construction-price/std_market_price.jsonl
fi

echo "Building application image..."
docker compose build api

echo "Starting PostgreSQL..."
docker compose up -d postgres --wait

DB_URL="postgresql+psycopg2://app:app@postgres:5432/construction_price"

run_in_app() {
  docker compose run --rm --no-deps \
    -e DATABASE_URL="$DB_URL" \
    -e CLASSIFICATION_FILE="${CLASSIFICATION_FILE:-data/construction_classification.jsonl}" \
    -e PRICE_FILE="${PRICE_FILE:-data/std_market_price.jsonl}" \
    -v "${ROOT_DIR}/data:/app/data:ro" \
    api "$@"
}

echo "Running migrations..."
run_in_app python -m src.run_migrate

echo "Running ETL..."
run_in_app python -m src.run_etl

echo "Running tests..."
run_in_app pytest tests/ -v

echo "Setup complete."
