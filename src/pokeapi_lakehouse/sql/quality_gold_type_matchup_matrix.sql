SELECT SUM(CASE WHEN matchup_key IS NULL OR ruleset_key IS NULL OR attacking_type_key IS NULL
 OR attacking_type_id IS NULL OR defending_type_key IS NULL OR defending_type_id IS NULL
 OR damage_multiplier IS NULL THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN damage_multiplier NOT IN (0.0,0.5,1.0,2.0) THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COUNT(*) FROM (SELECT matchup_key FROM {{table}} GROUP BY matchup_key HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
