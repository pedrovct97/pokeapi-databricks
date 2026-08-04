SELECT SUM(CASE WHEN pokemon_id IS NULL OR move_id IS NULL OR version_group_id IS NULL
 OR learn_method_id IS NULL OR level_learned_at IS NULL THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN level_learned_at<0 THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COALESCE(SUM(c-1),0) FROM (SELECT COUNT(*) c FROM {{table}}
 GROUP BY pokemon_id,move_id,version_group_id,learn_method_id,level_learned_at HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
