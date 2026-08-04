CREATE OR REPLACE TEMP VIEW silver_pokemon_ability_stage AS
WITH ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY source_url ORDER BY source_observed_at DESC,ingested_at DESC) rn FROM {{bronze_table}}
), decoded AS (
 SELECT source_url,payload_sha256,source_observed_at,
 FROM_JSON(payload_json,'STRUCT<id:BIGINT,abilities:ARRAY<STRUCT<is_hidden:BOOLEAN,slot:INT,ability:STRUCT<name:STRING,url:STRING>>>>') payload
 FROM ranked WHERE rn=1
), expanded AS (
 SELECT payload.id pokemon_id,
 CAST(NULLIF(REGEXP_EXTRACT(item.ability.url,'/([0-9]+)/?$',1),'') AS BIGINT) ability_id,
 item.ability.name ability_name,item.slot,item.is_hidden,source_url,
 payload_sha256 AS source_payload_sha256,source_observed_at
 FROM decoded LATERAL VIEW EXPLODE(payload.abilities) e AS item
)
SELECT *,CURRENT_TIMESTAMP() silver_transformed_at,{{run_id}} silver_run_id,
 pokemon_id IS NOT NULL AND ability_id IS NOT NULL AND ability_name IS NOT NULL
 AND slot IS NOT NULL AND is_hidden IS NOT NULL is_valid,
 CONCAT_WS('; ',CASE WHEN pokemon_id IS NULL THEN 'null_pokemon_id' END,
 CASE WHEN ability_id IS NULL THEN 'null_ability_id' END,CASE WHEN slot IS NULL THEN 'null_slot' END,
 CASE WHEN is_hidden IS NULL THEN 'null_is_hidden' END) validation_errors FROM expanded
