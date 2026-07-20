SELECT SUM(CASE WHEN type_id IS NULL OR type_name IS NULL OR source_url IS NULL OR source_payload_sha256 IS NULL THEN 1 ELSE 0 END) technical_null_count,
  CAST(0 AS BIGINT) range_violation_count,
  (SELECT COALESCE(SUM(c-1),0) FROM (SELECT COUNT(*) c FROM {{table}} GROUP BY type_id HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
