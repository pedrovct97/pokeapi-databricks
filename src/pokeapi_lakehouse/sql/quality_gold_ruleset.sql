SELECT SUM(CASE WHEN ruleset_key IS NULL OR ruleset_id IS NULL OR version_group_name IS NULL
 OR battle_format IS NULL OR level IS NULL OR iv IS NULL OR ev_policy IS NULL OR nature_policy IS NULL
 OR terastalization_enabled IS NULL OR rule_version IS NULL THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN level NOT IN (50,80,100) OR iv<>31 OR rule_version<>1 OR terastalization_enabled
  OR ruleset_key<>CONCAT_WS('|','ruleset',version_group_name,'singles',CONCAT('level-',CAST(level AS STRING)),'v1')
 THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COUNT(*) FROM (SELECT ruleset_key FROM {{table}} GROUP BY ruleset_key HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
