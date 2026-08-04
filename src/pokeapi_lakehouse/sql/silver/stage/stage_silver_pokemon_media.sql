CREATE OR REPLACE TEMP VIEW silver_pokemon_media_stage AS
WITH ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY source_url ORDER BY source_observed_at DESC,ingested_at DESC) rn
 FROM {{bronze_table}}
), decoded AS (
 SELECT source_url,payload_sha256,source_observed_at,
 FROM_JSON(payload_json,'STRUCT<id:BIGINT,name:STRING,sprites:STRUCT<front_default:STRING,front_shiny:STRING,`other`:STRUCT<`official-artwork`:STRUCT<front_default:STRING,front_shiny:STRING>>>>') payload
 FROM ranked WHERE rn=1
)
SELECT payload.id pokemon_id,payload.name pokemon_name,
 payload.sprites.`other`.`official-artwork`.front_default official_artwork_url,
 payload.sprites.`other`.`official-artwork`.front_shiny official_artwork_shiny_url,
 payload.sprites.front_default sprite_url,payload.sprites.front_shiny sprite_shiny_url,
 source_url,payload_sha256 source_payload_sha256,source_observed_at,
 CURRENT_TIMESTAMP() silver_transformed_at,{{run_id}} silver_run_id,
 payload.id IS NOT NULL AND payload.name IS NOT NULL is_valid,
 CONCAT_WS('; ',CASE WHEN payload.id IS NULL THEN 'null_pokemon_id' END,
 CASE WHEN payload.name IS NULL THEN 'null_pokemon_name' END) validation_errors
FROM decoded
