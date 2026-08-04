CREATE OR REPLACE TEMP VIEW silver_pokemon_move_stage AS
WITH ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY source_url ORDER BY source_observed_at DESC,ingested_at DESC) rn FROM {{bronze_table}}
), decoded AS (
 SELECT source_url,payload_sha256,source_observed_at,
 FROM_JSON(payload_json,'STRUCT<id:BIGINT,moves:ARRAY<STRUCT<move:STRUCT<name:STRING,url:STRING>,version_group_details:ARRAY<STRUCT<level_learned_at:INT,move_learn_method:STRUCT<name:STRING,url:STRING>,`order`:INT,version_group:STRUCT<name:STRING,url:STRING>>>>>>') payload
 FROM ranked WHERE rn=1
), moves_expanded AS (
 SELECT payload.id pokemon_id,m.move,detail,source_url,
 payload_sha256 AS source_payload_sha256,source_observed_at
 FROM decoded LATERAL VIEW EXPLODE(payload.moves) em AS m
 LATERAL VIEW EXPLODE(m.version_group_details) ed AS detail
), normalized AS (
 SELECT pokemon_id,
 CAST(NULLIF(REGEXP_EXTRACT(move.url,'/([0-9]+)/?$',1),'') AS BIGINT) move_id,
 move.name move_name,
 CAST(NULLIF(REGEXP_EXTRACT(detail.version_group.url,'/([0-9]+)/?$',1),'') AS BIGINT) version_group_id,
 detail.version_group.name version_group_name,
 CAST(NULLIF(REGEXP_EXTRACT(detail.move_learn_method.url,'/([0-9]+)/?$',1),'') AS BIGINT) learn_method_id,
 detail.move_learn_method.name learn_method_name,detail.level_learned_at,
 detail.`order` sort_order,source_url,source_payload_sha256,source_observed_at
 FROM moves_expanded
)
SELECT *,CURRENT_TIMESTAMP() silver_transformed_at,{{run_id}} silver_run_id,
 pokemon_id IS NOT NULL AND move_id IS NOT NULL AND move_name IS NOT NULL
 AND version_group_id IS NOT NULL AND version_group_name IS NOT NULL
 AND learn_method_id IS NOT NULL AND learn_method_name IS NOT NULL
 AND level_learned_at IS NOT NULL AND level_learned_at>=0 is_valid,
 CONCAT_WS('; ',CASE WHEN pokemon_id IS NULL THEN 'null_pokemon_id' END,
 CASE WHEN move_id IS NULL THEN 'null_move_id' END,
 CASE WHEN version_group_id IS NULL THEN 'null_version_group_id' END,
 CASE WHEN learn_method_id IS NULL THEN 'null_learn_method_id' END,
 CASE WHEN level_learned_at IS NULL OR level_learned_at<0 THEN 'invalid_level_learned_at' END)
 validation_errors FROM normalized
