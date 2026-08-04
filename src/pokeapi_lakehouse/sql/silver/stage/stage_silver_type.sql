CREATE OR REPLACE TEMP VIEW silver_type_stage AS
WITH ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY source_url ORDER BY source_observed_at DESC, ingested_at DESC) rn
  FROM {{bronze_table}}
), decoded AS (
  SELECT source_url, payload_sha256, source_observed_at,
    FROM_JSON(payload_json, 'STRUCT<id:BIGINT,name:STRING,generation:STRUCT<name:STRING,url:STRING>,move_damage_class:STRUCT<name:STRING,url:STRING>>') payload
  FROM ranked WHERE rn = 1
)
SELECT payload.id type_id, payload.name type_name,
  CAST(NULLIF(REGEXP_EXTRACT(payload.generation.url, '/([0-9]+)/?$', 1), '') AS BIGINT) generation_id,
  payload.generation.name generation_name,
  CAST(NULLIF(REGEXP_EXTRACT(payload.move_damage_class.url, '/([0-9]+)/?$', 1), '') AS BIGINT) damage_class_id,
  payload.move_damage_class.name damage_class_name, source_url,
  payload_sha256 source_payload_sha256, source_observed_at,
  CURRENT_TIMESTAMP() silver_transformed_at, {{run_id}} silver_run_id,
  payload.id IS NOT NULL AND payload.name IS NOT NULL is_valid,
  CONCAT_WS('; ', CASE WHEN payload.id IS NULL THEN 'null_type_id' END,
    CASE WHEN payload.name IS NULL THEN 'null_type_name' END) validation_errors
FROM decoded
