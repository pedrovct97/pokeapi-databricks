CREATE OR REPLACE TEMP VIEW silver_ability_stage AS
WITH ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY source_url ORDER BY source_observed_at DESC,ingested_at DESC) rn FROM {{bronze_table}}
), decoded AS (
 SELECT source_url,payload_sha256,source_observed_at,
 FROM_JSON(payload_json,'STRUCT<id:BIGINT,name:STRING,is_main_series:BOOLEAN,generation:STRUCT<name:STRING,url:STRING>>') payload
 FROM ranked WHERE rn=1
)
SELECT payload.id ability_id,payload.name ability_name,payload.is_main_series,
 CAST(NULLIF(REGEXP_EXTRACT(payload.generation.url,'/([0-9]+)/?$',1),'') AS BIGINT) generation_id,
 payload.generation.name generation_name,source_url,payload_sha256 source_payload_sha256,
 source_observed_at,CURRENT_TIMESTAMP() silver_transformed_at,{{run_id}} silver_run_id,
 payload.id IS NOT NULL AND payload.name IS NOT NULL AND payload.is_main_series IS NOT NULL is_valid,
 CONCAT_WS('; ',CASE WHEN payload.id IS NULL THEN 'null_ability_id' END,
 CASE WHEN payload.name IS NULL THEN 'null_ability_name' END,
 CASE WHEN payload.is_main_series IS NULL THEN 'null_is_main_series' END) validation_errors
FROM decoded
