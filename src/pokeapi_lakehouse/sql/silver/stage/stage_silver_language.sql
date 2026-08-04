CREATE OR REPLACE TEMP VIEW silver_language_stage AS
WITH ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY source_url ORDER BY source_observed_at DESC, ingested_at DESC) rn
  FROM {{bronze_table}}
), decoded AS (
  SELECT source_url, payload_sha256, source_observed_at,
    FROM_JSON(payload_json, 'STRUCT<id:BIGINT,name:STRING,official:BOOLEAN,iso639:STRING,iso3166:STRING>') payload
  FROM ranked WHERE rn = 1
)
SELECT payload.id language_id, payload.name language_code, payload.iso639 iso639_code,
  payload.iso3166 iso3166_code, payload.official is_official, source_url,
  payload_sha256 source_payload_sha256, source_observed_at,
  CURRENT_TIMESTAMP() silver_transformed_at, {{run_id}} silver_run_id,
  payload.id IS NOT NULL AND payload.name = 'en' AND payload.official IS NOT NULL is_valid,
  CONCAT_WS('; ', CASE WHEN payload.id IS NULL THEN 'null_language_id' END,
    CASE WHEN payload.name IS NULL THEN 'null_language_code' END,
    CASE WHEN payload.name <> 'en' THEN 'unsupported_language' END,
    CASE WHEN payload.official IS NULL THEN 'null_is_official' END) validation_errors
FROM decoded WHERE payload.name = 'en' OR payload.name IS NULL
