SELECT
  (
    SELECT COUNT(*)
    FROM {{table}}
    WHERE endpoint IS NULL
       OR source_url IS NULL
       OR http_status IS NULL
       OR payload_json IS NULL
       OR payload_sha256 IS NULL
       OR source_observed_at IS NULL
       OR ingested_at IS NULL
       OR run_id IS NULL
  ) AS technical_null_count,
  (
    SELECT COALESCE(SUM(version_count - 1), 0)
    FROM (
      SELECT COUNT(*) AS version_count
      FROM {{table}}
      GROUP BY source_url, payload_sha256
      HAVING COUNT(*) > 1
    ) AS duplicated_versions
  ) AS duplicate_count
