CREATE OR REPLACE TEMP VIEW silver_pokemon_species_translation_stage AS
WITH ranked AS (
 SELECT *, ROW_NUMBER() OVER(PARTITION BY source_url ORDER BY source_observed_at DESC, ingested_at DESC) rn FROM {{bronze_table}}
), decoded AS (
 SELECT source_url, payload_sha256, source_observed_at,
  FROM_JSON(payload_json, 'STRUCT<id:BIGINT,names:ARRAY<STRUCT<name:STRING,language:STRUCT<name:STRING,url:STRING>>>,genera:ARRAY<STRUCT<genus:STRING,language:STRUCT<name:STRING,url:STRING>>>,flavor_text_entries:ARRAY<STRUCT<flavor_text:STRING,language:STRUCT<name:STRING,url:STRING>,version:STRUCT<name:STRING,url:STRING>>>>') payload
 FROM ranked WHERE rn=1
), expanded AS (
 SELECT payload.id species_id,
  CAST(NULLIF(REGEXP_EXTRACT(n.language.url, '/([0-9]+)/?$', 1), '') AS BIGINT) language_id,
  n.language.name language_code, n.name localized_name,
  GET(FILTER(payload.genera, x -> x.language.name = n.language.name), 0).genus genus,
  REGEXP_REPLACE(GET(FILTER(payload.flavor_text_entries, x -> x.language.name = n.language.name), 0).flavor_text, '[\\n\\f\\r]+', ' ') flavor_text,
  source_url, payload_sha256 source_payload_sha256, source_observed_at
 FROM decoded LATERAL VIEW EXPLODE(payload.names) e AS n
 WHERE n.language.name = 'en'
)
SELECT *, CURRENT_TIMESTAMP() silver_transformed_at, {{run_id}} silver_run_id,
 species_id IS NOT NULL AND language_id IS NOT NULL AND language_code = 'en'
 AND localized_name IS NOT NULL is_valid,
 CONCAT_WS('; ', CASE WHEN species_id IS NULL THEN 'null_species_id' END,
  CASE WHEN language_id IS NULL THEN 'null_language_id' END,
  CASE WHEN localized_name IS NULL THEN 'null_localized_name' END) validation_errors
FROM expanded
