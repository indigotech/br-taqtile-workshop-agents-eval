# data/ — Data Layer

All access to SQLite (and, later, to external APIs) lives here. No agent logic. Imports only from `core/`.

## Schema and seed

`schema.sql` is the source of truth for the database layout and `seed.sql` its fixture data; `reset_database` deletes the file and replays both. There are no migrations — change the SQL files and run `make reset-db`. Seed data is deliberately varied (a tight budget, a generous one, dietary restrictions, a user with a dog) so different users exercise different agent paths; keep that property when editing it, and update the counts in `tests/data/test_database.py`.

Money is `REAL` in reais — precision is irrelevant for a trip planner and it keeps tools and prompts free of cents conversions.

## Connections

`connect(path)` returns a `sqlite3.Connection` with `Row` rows and foreign keys on (SQLite ships with them off). The caller owns the connection and closes it; datasources never open their own.

## Datasources

One class per aggregate (`UserDataSource`), taking the connection in its constructor, one method per query. Each datasource:

- **Returns row models from `models.py`, never `sqlite3.Row`** — convert with `Model.model_validate(dict(row))`.
- Names the columns it selects. `SELECT *` couples the model to the table layout.
- Uses `?` placeholders, never string formatting, for every value.
- Returns `None` for a missing row and an empty list for an empty result — never raises for "not found".

## External API clients

Clients for keyless public APIs (Open-Meteo, Nominatim, Nager.Date) go under `data/` too, one module per API, using `httpx`. Validate each response into a model right here, at the boundary that receives it.
