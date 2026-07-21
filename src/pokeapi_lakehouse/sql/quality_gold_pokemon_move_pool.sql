SELECT SUM(CASE WHEN pokemon_move_key IS NULL OR pokemon_key IS NULL OR pokemon_id IS NULL
 OR move_key IS NULL OR move_id IS NULL
 OR move_name IS NULL OR learn_method_id IS NULL OR ruleset_key IS NULL OR ruleset_id IS NULL
 THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN level_learned_at<0 OR ruleset_id<>'scarlet-violet|singles|level-50|v1'
 THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COUNT(*) FROM (SELECT pokemon_move_key FROM {{table}} GROUP BY pokemon_move_key HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
