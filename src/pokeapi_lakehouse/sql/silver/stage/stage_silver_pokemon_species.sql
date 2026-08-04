CREATE OR REPLACE TEMP VIEW silver_pokemon_species_stage AS
WITH ranked AS (
 SELECT *,ROW_NUMBER() OVER(PARTITION BY source_url ORDER BY source_observed_at DESC,ingested_at DESC) rn FROM {{bronze_table}}
), decoded AS (
 SELECT source_url,payload_sha256,source_observed_at,
 FROM_JSON(payload_json,'STRUCT<id:BIGINT,name:STRING,`order`:BIGINT,gender_rate:INT,capture_rate:INT,base_happiness:INT,is_baby:BOOLEAN,is_legendary:BOOLEAN,is_mythical:BOOLEAN,hatch_counter:INT,has_gender_differences:BOOLEAN,forms_switchable:BOOLEAN,generation:STRUCT<name:STRING,url:STRING>,growth_rate:STRUCT<name:STRING,url:STRING>,color:STRUCT<name:STRING,url:STRING>,shape:STRUCT<name:STRING,url:STRING>,habitat:STRUCT<name:STRING,url:STRING>,evolves_from_species:STRUCT<name:STRING,url:STRING>>') payload
 FROM ranked WHERE rn=1
)
SELECT payload.id species_id,payload.name species_name,payload.`order` sort_order,
 payload.gender_rate,payload.capture_rate,payload.base_happiness,payload.is_baby,
 payload.is_legendary,payload.is_mythical,payload.hatch_counter,
 payload.has_gender_differences,payload.forms_switchable,
 CAST(NULLIF(REGEXP_EXTRACT(payload.generation.url,'/([0-9]+)/?$',1),'') AS BIGINT) generation_id,payload.generation.name generation_name,
 CAST(NULLIF(REGEXP_EXTRACT(payload.growth_rate.url,'/([0-9]+)/?$',1),'') AS BIGINT) growth_rate_id,payload.growth_rate.name growth_rate_name,
 CAST(NULLIF(REGEXP_EXTRACT(payload.color.url,'/([0-9]+)/?$',1),'') AS BIGINT) color_id,payload.color.name color_name,
 CAST(NULLIF(REGEXP_EXTRACT(payload.shape.url,'/([0-9]+)/?$',1),'') AS BIGINT) shape_id,payload.shape.name shape_name,
 CAST(NULLIF(REGEXP_EXTRACT(payload.habitat.url,'/([0-9]+)/?$',1),'') AS BIGINT) habitat_id,payload.habitat.name habitat_name,
 CAST(NULLIF(REGEXP_EXTRACT(payload.evolves_from_species.url,'/([0-9]+)/?$',1),'') AS BIGINT) evolves_from_species_id,
 payload.evolves_from_species.name evolves_from_species_name,source_url,
 payload_sha256 source_payload_sha256,source_observed_at,CURRENT_TIMESTAMP() silver_transformed_at,
 {{run_id}} silver_run_id,
 payload.id IS NOT NULL AND payload.name IS NOT NULL AND payload.is_baby IS NOT NULL
 AND payload.is_legendary IS NOT NULL AND payload.is_mythical IS NOT NULL
 AND payload.has_gender_differences IS NOT NULL AND payload.forms_switchable IS NOT NULL
 AND (payload.capture_rate IS NULL OR payload.capture_rate BETWEEN 0 AND 255)
 AND (payload.base_happiness IS NULL OR payload.base_happiness BETWEEN 0 AND 255) is_valid,
 CONCAT_WS('; ',CASE WHEN payload.id IS NULL THEN 'null_species_id' END,
 CASE WHEN payload.name IS NULL THEN 'null_species_name' END,
 CASE WHEN payload.capture_rate NOT BETWEEN 0 AND 255 THEN 'invalid_capture_rate' END,
 CASE WHEN payload.base_happiness NOT BETWEEN 0 AND 255 THEN 'invalid_base_happiness' END)
 validation_errors
FROM decoded
