CREATE OR REPLACE TEMP VIEW gold_game_version_stage AS
WITH version_ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY source_url ORDER BY source_observed_at DESC,ingested_at DESC) rn
 FROM {{version}}
), version_decoded AS (
 SELECT FROM_JSON(payload_json,'STRUCT<id:BIGINT,name:STRING,version_group:STRUCT<name:STRING,url:STRING>>') payload
 FROM version_ranked WHERE rn=1
), version_group_ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY source_url ORDER BY source_observed_at DESC,ingested_at DESC) rn
 FROM {{version_group}}
), version_group_decoded AS (
 SELECT FROM_JSON(payload_json,'STRUCT<id:BIGINT,name:STRING,`order`:INT,generation:STRUCT<name:STRING,url:STRING>>') payload
 FROM version_group_ranked WHERE rn=1
), generation_ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY source_url ORDER BY source_observed_at DESC,ingested_at DESC) rn
 FROM {{generation}}
), generation_decoded AS (
 SELECT FROM_JSON(payload_json,'STRUCT<id:BIGINT,name:STRING,main_region:STRUCT<name:STRING,url:STRING>>') payload
 FROM generation_ranked WHERE rn=1
), normalized AS (
 SELECT
  v.payload.id version_id,
  v.payload.name version_name,
  CAST(NULLIF(REGEXP_EXTRACT(v.payload.version_group.url,'/([0-9]+)/?$',1),'') AS BIGINT) version_group_id,
  v.payload.version_group.name version_group_name,
  vg.payload.generation.name generation_name,
  CAST(NULLIF(REGEXP_EXTRACT(vg.payload.generation.url,'/([0-9]+)/?$',1),'') AS BIGINT) generation_id,
  g.payload.main_region.name region_name
 FROM version_decoded v
 LEFT JOIN version_group_decoded vg
  ON vg.payload.id=CAST(NULLIF(REGEXP_EXTRACT(v.payload.version_group.url,'/([0-9]+)/?$',1),'') AS BIGINT)
 LEFT JOIN generation_decoded g
  ON g.payload.id=CAST(NULLIF(REGEXP_EXTRACT(vg.payload.generation.url,'/([0-9]+)/?$',1),'') AS BIGINT)
)
SELECT
 CONCAT_WS('|','game_version',CAST(version_id AS STRING)) game_version_key,
 version_id,
 version_name,
 CASE version_name
  WHEN 'red' THEN 'Pokémon Red'
  WHEN 'blue' THEN 'Pokémon Blue'
  WHEN 'yellow' THEN 'Pokémon Yellow'
  WHEN 'gold' THEN 'Pokémon Gold'
  WHEN 'silver' THEN 'Pokémon Silver'
  WHEN 'crystal' THEN 'Pokémon Crystal'
  WHEN 'ruby' THEN 'Pokémon Ruby'
  WHEN 'sapphire' THEN 'Pokémon Sapphire'
  WHEN 'emerald' THEN 'Pokémon Emerald'
  WHEN 'firered' THEN 'Pokémon FireRed'
  WHEN 'leafgreen' THEN 'Pokémon LeafGreen'
  WHEN 'diamond' THEN 'Pokémon Diamond'
  WHEN 'pearl' THEN 'Pokémon Pearl'
  WHEN 'platinum' THEN 'Pokémon Platinum'
  ELSE CONCAT('Pokémon ',INITCAP(REPLACE(version_name,'-',' ')))
 END display_name,
 CONCAT_WS('|','version_group',CAST(version_group_id AS STRING)) version_group_key,
 version_group_id,
 version_group_name,
 generation_id,
 generation_name,
 region_name,
 CURRENT_TIMESTAMP() gold_transformed_at,
 {{run_id}} gold_run_id
FROM normalized
