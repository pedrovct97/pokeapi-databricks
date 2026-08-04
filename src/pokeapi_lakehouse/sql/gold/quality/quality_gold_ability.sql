SELECT SUM(CASE WHEN ability_key IS NULL OR ability_id IS NULL OR ability_name IS NULL
 OR canonical_name IS NULL OR is_main_series IS NULL THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN ability_key<>CONCAT_WS('|','ability',CAST(ability_id AS STRING)) THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COUNT(*) FROM (SELECT ability_key FROM {{table}} GROUP BY ability_key HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
