CREATE OR REPLACE TEMP VIEW silver_pokemon_type_stage AS
WITH ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY source_url ORDER BY source_observed_at DESC,ingested_at DESC) rn FROM {{bronze_table}}
), decoded AS (
 SELECT source_url,payload_sha256,source_observed_at,
 FROM_JSON(payload_json,'STRUCT<id:BIGINT,types:ARRAY<STRUCT<slot:INT,type:STRUCT<name:STRING,url:STRING>>>>') payload
 FROM ranked WHERE rn=1
), expanded AS (
 SELECT payload.id pokemon_id,item.slot,
 CAST(NULLIF(REGEXP_EXTRACT(item.type.url,'/([0-9]+)/?$',1),'') AS BIGINT) type_id,
 item.type.name type_name,source_url,payload_sha256 AS source_payload_sha256,source_observed_at
 FROM decoded LATERAL VIEW EXPLODE(payload.types) e AS item
)
SELECT *,CURRENT_TIMESTAMP() silver_transformed_at,{{run_id}} silver_run_id,
 pokemon_id IS NOT NULL AND slot IS NOT NULL AND type_id IS NOT NULL AND type_name IS NOT NULL is_valid,
 CONCAT_WS('; ',CASE WHEN pokemon_id IS NULL THEN 'null_pokemon_id' END,
 CASE WHEN slot IS NULL THEN 'null_slot' END,CASE WHEN type_id IS NULL THEN 'null_type_id' END)
 validation_errors FROM expanded
