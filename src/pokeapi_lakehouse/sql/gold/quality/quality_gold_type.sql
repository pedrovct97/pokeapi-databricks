SELECT SUM(CASE WHEN type_key IS NULL OR type_id IS NULL OR type_name IS NULL OR canonical_name IS NULL
 THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN type_key<>CONCAT_WS('|','type',CAST(type_id AS STRING)) THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COUNT(*) FROM (SELECT type_key FROM {{table}} GROUP BY type_key HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
