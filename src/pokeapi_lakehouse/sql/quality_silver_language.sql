SELECT
  SUM(CASE WHEN language_id IS NULL OR language_code IS NULL OR is_official IS NULL THEN 1 ELSE 0 END) technical_null_count,
  SUM(CASE WHEN language_code <> 'en' THEN 1 ELSE 0 END) range_violation_count,
  (SELECT COUNT(*) FROM (SELECT language_id FROM {{table}} GROUP BY language_id HAVING COUNT(*) > 1)) duplicate_count
FROM {{table}}
