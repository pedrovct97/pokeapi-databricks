SELECT SUM(CASE WHEN pokemon_id IS NULL OR stat_id IS NULL OR stat_name IS NULL OR base_stat IS NULL OR effort IS NULL THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN base_stat<0 OR effort<0 THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COALESCE(SUM(c-1),0) FROM (SELECT COUNT(*) c FROM {{table}} GROUP BY pokemon_id,stat_id HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
