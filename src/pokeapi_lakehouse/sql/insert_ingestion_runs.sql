INSERT INTO {{table}} (
  run_id,
  endpoint,
  started_at,
  finished_at,
  status,
  discovered_count,
  fetched_count,
  inserted_count,
  failed_count,
  error_message
)
SELECT
  run_id,
  endpoint,
  started_at,
  finished_at,
  status,
  discovered_count,
  fetched_count,
  inserted_count,
  failed_count,
  error_message
FROM pokeapi_ingestion_runs_batch
