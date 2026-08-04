SELECT SUM(CASE WHEN pokemon_id IS NULL OR slot IS NULL OR type_id IS NULL OR type_name IS NULL THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN slot<1 THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COALESCE(SUM(c-1),0) FROM (SELECT COUNT(*) c FROM {{table}} GROUP BY pokemon_id,slot HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
