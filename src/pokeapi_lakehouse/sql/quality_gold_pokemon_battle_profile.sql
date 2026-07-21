SELECT SUM(CASE WHEN pokemon_battle_stats_key IS NULL OR ruleset_key IS NULL
 OR pokemon_key IS NULL OR pokemon_id IS NULL OR hp IS NULL OR attack IS NULL
 OR defense IS NULL OR special_attack IS NULL OR special_defense IS NULL OR speed IS NULL
 OR weaknesses IS NULL OR resistances IS NULL OR immunities IS NULL THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN hp<=0 OR attack<=0 OR defense<=0 OR special_attack<=0 OR special_defense<=0
 OR speed<=0 OR base_stat_total<>hp+attack+defense+special_attack+special_defense+speed THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COUNT(*) FROM (SELECT pokemon_battle_stats_key FROM {{table}}
  GROUP BY pokemon_battle_stats_key HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
