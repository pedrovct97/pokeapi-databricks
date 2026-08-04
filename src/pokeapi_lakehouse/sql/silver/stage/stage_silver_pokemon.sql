CREATE OR REPLACE TEMP VIEW silver_pokemon_stage AS
WITH ranked AS (
  SELECT
    source_url,
    payload_json,
    payload_sha256,
    source_observed_at,
    ROW_NUMBER() OVER (
      PARTITION BY source_url
      ORDER BY source_observed_at DESC, ingested_at DESC, payload_sha256 DESC
    ) AS version_rank
  FROM {{bronze_table}}
),
parsed AS (
  SELECT
    source_url,
    payload_sha256,
    source_observed_at,
    FROM_JSON(
      payload_json,
      'STRUCT<id: BIGINT, name: STRING, base_experience: BIGINT, height: BIGINT, weight: BIGINT, is_default: BOOLEAN, `order`: BIGINT, species: STRUCT<name: STRING, url: STRING>>'
    ) AS payload
  FROM ranked
  WHERE version_rank = 1
),
normalized AS (
  SELECT *, COUNT(*) OVER (PARTITION BY payload.id) AS id_occurrences
  FROM parsed
)
SELECT
  payload.id AS pokemon_id,
  payload.name AS pokemon_name,
  payload.base_experience,
  payload.height AS height_dm,
  CAST(payload.height / 10.0 AS DECIMAL(10,2)) AS height_m,
  payload.weight AS weight_hg,
  CAST(payload.weight / 10.0 AS DECIMAL(10,2)) AS weight_kg,
  payload.is_default,
  payload.`order` AS sort_order,
  CAST(NULLIF(REGEXP_EXTRACT(payload.species.url, '/([0-9]+)/?$', 1), '') AS BIGINT) AS species_id,
  payload.species.name AS species_name,
  source_url,
  payload_sha256 AS source_payload_sha256,
  source_observed_at,
  CURRENT_TIMESTAMP() AS silver_transformed_at,
  {{run_id}} AS silver_run_id,
  payload IS NOT NULL
    AND payload.id IS NOT NULL
    AND payload.name IS NOT NULL
    AND payload.height IS NOT NULL AND payload.height >= 0
    AND payload.weight IS NOT NULL AND payload.weight >= 0
    AND payload.is_default IS NOT NULL
    AND id_occurrences = 1
    AND (payload.base_experience IS NULL OR payload.base_experience >= 0) AS is_valid,
  CONCAT_WS('; ',
    CASE WHEN payload IS NULL THEN 'invalid_json_contract' END,
    CASE WHEN payload.id IS NULL THEN 'null_pokemon_id' END,
    CASE WHEN payload.name IS NULL THEN 'null_pokemon_name' END,
    CASE WHEN payload.height IS NULL OR payload.height < 0 THEN 'invalid_height_dm' END,
    CASE WHEN payload.weight IS NULL OR payload.weight < 0 THEN 'invalid_weight_hg' END,
    CASE WHEN payload.is_default IS NULL THEN 'null_is_default' END,
    CASE WHEN id_occurrences > 1 THEN 'duplicate_pokemon_id' END,
    CASE WHEN payload.base_experience < 0 THEN 'negative_base_experience' END
  ) AS validation_errors
FROM normalized
