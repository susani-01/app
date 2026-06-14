.PHONY: analyze phase1 setup run down etl migrate test verify

analyze phase1:
	python3 -m src.run_phase1_analysis

setup:
	chmod +x scripts/setup.sh scripts/down.sh scripts/verify.sh
	./scripts/setup.sh

migrate:
	python3 -m src.run_migrate

etl:
	python3 -m src.run_etl

run:
	docker compose up -d postgres --wait
	docker compose up --build api

down:
	chmod +x scripts/down.sh
	./scripts/down.sh

test:
	docker compose run --rm --no-deps \
		-e DATABASE_URL=postgresql+psycopg2://app:app@postgres:5432/construction_price \
		-v "$(CURDIR)/data:/app/data:ro" \
		api pytest tests/ -v

verify:
	chmod +x scripts/verify.sh
	./scripts/verify.sh
