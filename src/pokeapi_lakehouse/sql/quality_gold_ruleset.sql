SELECT SUM(CASE WHEN ruleset_key IS NULL OR ruleset_id IS NULL OR version_group_name IS NULL
 THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN level<>50 OR iv<>31 OR rule_version<>1 OR terastalization_enabled
 THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COUNT(*) FROM (SELECT ruleset_key FROM {{table}} GROUP BY ruleset_key HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
