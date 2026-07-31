CREATE OR REPLACE TEMP VIEW gold_version_group_stage AS
WITH ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY source_url ORDER BY source_observed_at DESC,ingested_at DESC) rn
 FROM {{version_group}}
), decoded AS (
 SELECT FROM_JSON(payload_json,'STRUCT<id:BIGINT,name:STRING,`order`:INT,generation:STRUCT<name:STRING,url:STRING>>') payload
 FROM ranked WHERE rn=1
)
SELECT
 CONCAT_WS('|','version_group',CAST(payload.id AS STRING)) version_group_key,
 payload.id version_group_id,
 payload.name version_group_name,
 CAST(NULLIF(REGEXP_EXTRACT(payload.generation.url,'/([0-9]+)/?$',1),'') AS BIGINT) generation_id,
 payload.generation.name generation_name,
 payload.`order` order_index,
 CURRENT_TIMESTAMP() gold_transformed_at,
 {{run_id}} gold_run_id
FROM decoded
