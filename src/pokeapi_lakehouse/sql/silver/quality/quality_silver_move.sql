SELECT
  SUM(CASE WHEN move_id IS NULL OR move_name IS NULL OR priority IS NULL
    OR source_url IS NULL OR source_payload_sha256 IS NULL OR source_observed_at IS NULL
    OR silver_transformed_at IS NULL OR silver_run_id IS NULL THEN 1 ELSE 0 END)
    AS technical_null_count,
  SUM(CASE WHEN accuracy_pct NOT BETWEEN 0 AND 100
    OR effect_chance_pct NOT BETWEEN 0 AND 100 OR pp < 0 OR power < 0 THEN 1 ELSE 0 END)
    AS range_violation_count,
  (
    SELECT COALESCE(SUM(row_count - 1), 0)
    FROM (SELECT COUNT(*) AS row_count FROM {{table}} GROUP BY move_id HAVING COUNT(*) > 1)
  ) AS duplicate_count
FROM {{table}}
