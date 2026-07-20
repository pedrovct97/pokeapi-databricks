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
  source.ingested_at,
  source.run_id
)
