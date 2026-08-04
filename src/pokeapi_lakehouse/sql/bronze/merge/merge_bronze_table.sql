MERGE INTO {{table}} AS target
USING pokeapi_bronze_batch AS source
  ON target.source_url = source.source_url
 AND target.payload_sha256 = source.payload_sha256
WHEN NOT MATCHED THEN INSERT (
  endpoint,
  resource_id,
  resource_name,
  source_url,
  http_status,
  payload_json,
  payload_sha256,
  source_observed_at,
  response_bytes,
  duration_ms,
  attempt_count,
  etag,
  last_modified,
  ingested_at,
  run_id
)
VALUES (
  source.endpoint,
  source.resource_id,
  source.resource_name,
  source.source_url,
  source.http_status,
  source.payload_json,
  source.payload_sha256,
  source.source_observed_at,
  source.response_bytes,
  source.duration_ms,
  source.attempt_count,
  source.etag,
  source.last_modified,
  source.ingested_at,
  source.run_id
)
