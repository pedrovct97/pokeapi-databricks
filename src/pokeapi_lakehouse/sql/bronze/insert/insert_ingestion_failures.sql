INSERT INTO {{table}} (
  endpoint,
  source_url,
  error_type,
  error_message,
  http_status,
  attempt_count,
  duration_ms,
  is_retriable,
  attempted_at,
  run_id
)
SELECT
  endpoint,
  source_url,
  error_type,
  error_message,
  http_status,
  attempt_count,
  duration_ms,
  is_retriable,
  attempted_at,
  run_id
FROM pokeapi_ingestion_failures_batch
