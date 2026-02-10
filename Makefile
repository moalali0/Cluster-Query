.PHONY: up down logs generate ingest

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

generate:
	docker compose exec backend python scripts/generate_mock_csv.py

ingest:
	docker compose exec backend python scripts/ingest_mock_csv.py --csv /data/mock_clusters.csv
