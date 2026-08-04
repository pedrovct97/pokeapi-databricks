SELECT SUM(CASE WHEN move_key IS NULL OR move_id IS NULL OR move_name IS NULL OR priority IS NULL
 THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN accuracy_pct NOT BETWEEN 0 AND 100 OR effect_chance_pct NOT BETWEEN 0 AND 100
  OR power<0 OR pp<0 OR expected_power<0 THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COUNT(*) FROM (SELECT move_key FROM {{table}} GROUP BY move_key HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
