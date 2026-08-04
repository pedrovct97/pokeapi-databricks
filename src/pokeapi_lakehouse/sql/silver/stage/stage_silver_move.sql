CREATE OR REPLACE TEMP VIEW silver_move_stage AS
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
      'STRUCT<id: BIGINT, name: STRING, accuracy: INT, effect_chance: INT, pp: INT, priority: INT, power: INT, damage_class: STRUCT<name: STRING, url: STRING>, type: STRUCT<name: STRING, url: STRING>, generation: STRUCT<name: STRING, url: STRING>>'
    ) AS payload
  FROM ranked
  WHERE version_rank = 1
),
normalized AS (
  SELECT *, COUNT(*) OVER (PARTITION BY payload.id) AS id_occurrences
  FROM parsed
)
SELECT
  payload.id AS move_id,
  payload.name AS move_name,
  payload.accuracy AS accuracy_pct,
  payload.effect_chance AS effect_chance_pct,
  payload.pp,
  payload.priority,
  payload.power,
  CAST(NULLIF(REGEXP_EXTRACT(payload.damage_class.url, '/([0-9]+)/?$', 1), '') AS BIGINT)
    AS damage_class_id,
  payload.damage_class.name AS damage_class_name,
  CAST(NULLIF(REGEXP_EXTRACT(payload.type.url, '/([0-9]+)/?$', 1), '') AS BIGINT) AS type_id,
  payload.type.name AS type_name,
  CAST(NULLIF(REGEXP_EXTRACT(payload.generation.url, '/([0-9]+)/?$', 1), '') AS BIGINT)
    AS generation_id,
  payload.generation.name AS generation_name,
  source_url,
  payload_sha256 AS source_payload_sha256,
  source_observed_at,
  CURRENT_TIMESTAMP() AS silver_transformed_at,
  {{run_id}} AS silver_run_id,
  payload IS NOT NULL
    AND payload.id IS NOT NULL
    AND payload.name IS NOT NULL
    AND payload.priority IS NOT NULL
    AND id_occurrences = 1
    AND (payload.accuracy IS NULL OR payload.accuracy BETWEEN 0 AND 100)
    AND (payload.effect_chance IS NULL OR payload.effect_chance BETWEEN 0 AND 100)
    AND (payload.pp IS NULL OR payload.pp >= 0)
    AND (payload.power IS NULL OR payload.power >= 0) AS is_valid,
  CONCAT_WS('; ',
    CASE WHEN payload IS NULL THEN 'invalid_json_contract' END,
    CASE WHEN payload.id IS NULL THEN 'null_move_id' END,
    CASE WHEN payload.name IS NULL THEN 'null_move_name' END,
    CASE WHEN payload.priority IS NULL THEN 'null_priority' END,
    CASE WHEN id_occurrences > 1 THEN 'duplicate_move_id' END,
    CASE WHEN payload.accuracy NOT BETWEEN 0 AND 100 THEN 'invalid_accuracy_pct' END,
    CASE WHEN payload.effect_chance NOT BETWEEN 0 AND 100 THEN 'invalid_effect_chance_pct' END,
    CASE WHEN payload.pp < 0 THEN 'negative_pp' END,
    CASE WHEN payload.power < 0 THEN 'negative_power' END
  ) AS validation_errors
FROM normalized
