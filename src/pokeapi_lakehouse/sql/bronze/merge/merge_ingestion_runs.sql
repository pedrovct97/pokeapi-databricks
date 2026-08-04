MERGE INTO {{table}} AS target
USING pokeapi_ingestion_runs_batch AS source
  ON target.run_id = source.run_id
 AND target.endpoint = source.endpoint
WHEN MATCHED THEN UPDATE SET
  target.started_at = source.started_at,
  target.finished_at = source.finished_at,
  target.status = source.status,
  target.discovered_count = source.discovered_count,
  target.list_count = source.list_count,
  target.page_count = source.page_count,
  target.fetched_count = source.fetched_count,
  target.inserted_count = source.inserted_count,
  target.failed_count = source.failed_count,
  target.duration_ms = source.duration_ms,
  target.collector_version = source.collector_version,
  target.error_message = source.error_message
WHEN NOT MATCHED THEN INSERT (
  run_id, endpoint, started_at, finished_at, status, discovered_count,
  list_count, page_count, fetched_count, inserted_count, failed_count,
  duration_ms, collector_version, error_message
)
VALUES (
  source.run_id, source.endpoint, source.started_at, source.finished_at, source.status,
  source.discovered_count, source.list_count, source.page_count, source.fetched_count,
  source.inserted_count, source.failed_count, source.duration_ms,
  source.collector_version, source.error_message
)
