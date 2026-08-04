SELECT SUM(CASE WHEN source_type_id IS NULL OR target_type_id IS NULL OR damage_multiplier IS NULL THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN damage_multiplier NOT IN (0.0,0.5,2.0) THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COALESCE(SUM(c-1),0) FROM (SELECT COUNT(*) c FROM {{table}}
 GROUP BY source_type_id,target_type_id HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
