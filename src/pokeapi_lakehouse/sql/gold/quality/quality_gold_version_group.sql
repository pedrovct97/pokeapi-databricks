SELECT
 SUM(CASE WHEN version_group_key IS NULL OR version_group_id IS NULL OR version_group_name IS NULL
  OR generation_id IS NULL OR generation_name IS NULL OR order_index IS NULL
  OR gold_transformed_at IS NULL OR gold_run_id IS NULL THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN version_group_key<>CONCAT_WS('|','version_group',CAST(version_group_id AS STRING))
  OR order_index<0 THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COUNT(*) FROM (SELECT version_group_key FROM {{table}} GROUP BY version_group_key HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
