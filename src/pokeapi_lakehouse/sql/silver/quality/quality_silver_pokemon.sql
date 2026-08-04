SELECT
  SUM(CASE WHEN pokemon_id IS NULL OR pokemon_name IS NULL OR source_url IS NULL
    OR source_payload_sha256 IS NULL OR source_observed_at IS NULL
    OR silver_transformed_at IS NULL OR silver_run_id IS NULL THEN 1 ELSE 0 END)
    AS technical_null_count,
  SUM(CASE WHEN height_dm < 0 OR weight_hg < 0 OR base_experience < 0 THEN 1 ELSE 0 END)
    AS range_violation_count,
  (
    SELECT COALESCE(SUM(row_count - 1), 0)
    FROM (SELECT COUNT(*) AS row_count FROM {{table}} GROUP BY pokemon_id HAVING COUNT(*) > 1)
  ) AS duplicate_count
FROM {{table}}
