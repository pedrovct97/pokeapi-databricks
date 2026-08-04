CREATE OR REPLACE TEMP VIEW silver_type_damage_relation_stage AS
WITH ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY source_url ORDER BY source_observed_at DESC,ingested_at DESC) rn FROM {{bronze_table}}
), decoded AS (
 SELECT source_url,payload_sha256,source_observed_at,
 FROM_JSON(payload_json,'STRUCT<id:BIGINT,name:STRING,damage_relations:STRUCT<double_damage_to:ARRAY<STRUCT<name:STRING,url:STRING>>,half_damage_to:ARRAY<STRUCT<name:STRING,url:STRING>>,no_damage_to:ARRAY<STRUCT<name:STRING,url:STRING>>>>') payload
 FROM ranked WHERE rn=1
), relations AS (
 SELECT payload.id source_type_id,payload.name source_type_name,target,CAST(2.0 AS DECIMAL(3,1)) damage_multiplier,source_url,payload_sha256,source_observed_at
 FROM decoded LATERAL VIEW EXPLODE(payload.damage_relations.double_damage_to) e AS target
 UNION ALL
 SELECT payload.id,payload.name,target,CAST(0.5 AS DECIMAL(3,1)),source_url,payload_sha256,source_observed_at
 FROM decoded LATERAL VIEW EXPLODE(payload.damage_relations.half_damage_to) e AS target
 UNION ALL
 SELECT payload.id,payload.name,target,CAST(0.0 AS DECIMAL(3,1)),source_url,payload_sha256,source_observed_at
 FROM decoded LATERAL VIEW EXPLODE(payload.damage_relations.no_damage_to) e AS target
)
SELECT source_type_id,source_type_name,
 CAST(NULLIF(REGEXP_EXTRACT(target.url,'/([0-9]+)/?$',1),'') AS BIGINT) target_type_id,
 target.name target_type_name,damage_multiplier,source_url,payload_sha256 source_payload_sha256,
 source_observed_at,CURRENT_TIMESTAMP() silver_transformed_at,{{run_id}} silver_run_id,
 source_type_id IS NOT NULL AND source_type_name IS NOT NULL AND target.url IS NOT NULL
 AND target.name IS NOT NULL is_valid,
 CONCAT_WS('; ',CASE WHEN source_type_id IS NULL THEN 'null_source_type_id' END,
 CASE WHEN target.url IS NULL THEN 'null_target_type_id' END) validation_errors FROM relations
