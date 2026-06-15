# Construction Standard Price API

Backend assignment: a reference system for construction estimators to browse classification hierarchies and look up standard market prices for quantity calculation items.

## Quick start

```bash
make setup    # download data, start PostgreSQL, migrate, load ETL
make run      # start API at http://localhost:8080
make verify   # smoke-test endpoints (in another terminal while API runs)
make test     # run pytest suite (requires setup first)
make down     # stop containers and remove volumes
```

Expected flow for reviewers: **`setup → run → down`** with no extra configuration.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/openapi.json` | OpenAPI specification |
| GET | `/docs` | Swagger UI |
| GET | `/api/v1/items` | Search items (`cnstwk_div_cd`, `lvl1_code`…`lvl5_code`, `q`, `page`, `size`) |
| GET | `/api/v1/items/{id}` | Get one item |
| GET | `/classification` | Browse hierarchy (`cnstwk_div_cd`, optional `parent_code`) |
| GET | `/work_division` | List work divisions |
| GET | `/health` | Liveness |
| GET | `/ready` | Database load check |

All JSON responses use HTTP 200 with a legacy envelope:

```json
{ "status": "success", "data": { ... }, "message": null }
```

## Examples

```bash
curl "http://localhost:8080/api/v1/items?cnstwk_div_cd=A&q=가설울타리&size=5"
curl "http://localhost:8080/api/v1/items/AAA162303500"
curl "http://localhost:8080/classification?cnstwk_div_cd=A"
curl "http://localhost:8080/classification?cnstwk_div_cd=A&parent_code=AA"
```

## Project structure

```
src/
├── analysis/      Phase 1 data exploration
├── domain/        Unit normalization rules
├── db/            SQLAlchemy models
├── etl/           JSONL → PostgreSQL loader
├── repository/    SQL queries
├── service/       Business logic
├── api/           HTTP routes and schemas
└── main.py        FastAPI app
docs/
├── DESIGN_NOTES.md    Design decisions (required submission)
└── reports/           Generated analysis reports
```

## Design documentation

See [`docs/DESIGN_NOTES.md`](docs/DESIGN_NOTES.md) for domain analysis, schema design, API decisions, scalability notes, and bonus proposals.

Domain background: [`docs/DOMAIN.md`](docs/DOMAIN.md)  
Data schema: [`docs/DATA_SCHEMA.md`](docs/DATA_SCHEMA.md)

## Submission

Zip the project folder excluding:

- `data/` (downloaded automatically by `make setup`)
- `.venv/`, `node_modules/`, build artifacts

Include:

- Source code and `Makefile`
- Completed `docs/DESIGN_NOTES.md`
- OpenAPI spec (served live at `/openapi.json`)
