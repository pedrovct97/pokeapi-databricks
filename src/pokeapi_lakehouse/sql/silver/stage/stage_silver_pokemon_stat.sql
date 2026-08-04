CREATE OR REPLACE TEMP VIEW silver_pokemon_stat_stage AS
WITH ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY source_url ORDER BY source_observed_at DESC,ingested_at DESC) rn FROM {{bronze_table}}
), decoded AS (
 SELECT source_url,payload_sha256,source_observed_at,
 FROM_JSON(payload_json,'STRUCT<id:BIGINT,stats:ARRAY<STRUCT<base_stat:INT,effort:INT,stat:STRUCT<name:STRING,url:STRING>>>>') payload
 FROM ranked WHERE rn=1
), expanded AS (
 SELECT payload.id pokemon_id,
 CAST(NULLIF(REGEXP_EXTRACT(item.stat.url,'/([0-9]+)/?$',1),'') AS BIGINT) stat_id,
 item.stat.name stat_name,item.base_stat,item.effort,source_url,
 payload_sha256 AS source_payload_sha256,source_observed_at
 FROM decoded LATERAL VIEW EXPLODE(payload.stats) e AS item
)
SELECT *,CURRENT_TIMESTAMP() silver_transformed_at,{{run_id}} silver_run_id,
 pokemon_id IS NOT NULL AND stat_id IS NOT NULL AND stat_name IS NOT NULL
 AND base_stat IS NOT NULL AND base_stat>=0 AND effort IS NOT NULL AND effort>=0 is_valid,
 CONCAT_WS('; ',CASE WHEN pokemon_id IS NULL THEN 'null_pokemon_id' END,
 CASE WHEN stat_id IS NULL THEN 'null_stat_id' END,
 CASE WHEN base_stat IS NULL OR base_stat<0 THEN 'invalid_base_stat' END,
 CASE WHEN effort IS NULL OR effort<0 THEN 'invalid_effort' END) validation_errors FROM expanded
