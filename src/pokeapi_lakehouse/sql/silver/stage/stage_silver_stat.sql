CREATE OR REPLACE TEMP VIEW silver_stat_stage AS
WITH ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY source_url ORDER BY source_observed_at DESC, ingested_at DESC) rn
  FROM {{bronze_table}}
), decoded AS (
  SELECT source_url,payload_sha256,source_observed_at,
    FROM_JSON(payload_json,'STRUCT<id:BIGINT,name:STRING,game_index:INT,is_battle_only:BOOLEAN,move_damage_class:STRUCT<name:STRING,url:STRING>>') payload
  FROM ranked WHERE rn=1
)
SELECT payload.id stat_id,payload.name stat_name,payload.game_index,payload.is_battle_only,
  CAST(NULLIF(REGEXP_EXTRACT(payload.move_damage_class.url,'/([0-9]+)/?$' ,1),'') AS BIGINT) damage_class_id,
  payload.move_damage_class.name damage_class_name,source_url,payload_sha256 source_payload_sha256,
  source_observed_at,CURRENT_TIMESTAMP() silver_transformed_at,{{run_id}} silver_run_id,
  payload.id IS NOT NULL AND payload.name IS NOT NULL AND payload.is_battle_only IS NOT NULL is_valid,
  CONCAT_WS('; ',CASE WHEN payload.id IS NULL THEN 'null_stat_id' END,
    CASE WHEN payload.name IS NULL THEN 'null_stat_name' END,
    CASE WHEN payload.is_battle_only IS NULL THEN 'null_is_battle_only' END) validation_errors
FROM decoded
