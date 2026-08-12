SELECT
 SUM(CASE WHEN option_key IS NULL OR game_version_key IS NULL OR version_id IS NULL
  OR version_name IS NULL OR game_version_display_name IS NULL OR version_group_key IS NULL
  OR version_group_id IS NULL OR version_group_name IS NULL OR generation_id IS NULL
  OR generation_name IS NULL OR battle_level IS NULL OR pokemon_key IS NULL OR pokemon_id IS NULL
  OR canonical_name IS NULL OR localized_name IS NULL OR display_name IS NULL OR types IS NULL
  OR is_default IS NULL OR is_available_for_battle IS NULL OR availability_source IS NULL
  THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN option_key<>CONCAT_WS('|','game_pokemon_option',version_name,CAST(battle_level AS STRING),CAST(pokemon_id AS STRING))
  OR game_version_key<>CONCAT_WS('|','game_version',CAST(version_id AS STRING))
  OR version_group_key<>CONCAT_WS('|','version_group',CAST(version_group_id AS STRING))
  OR pokemon_key<>CONCAT_WS('|','pokemon',CAST(pokemon_id AS STRING))
  OR battle_level NOT IN (50,80,100) OR SIZE(types)=0 OR is_available_for_battle<>TRUE
  OR availability_source<>'fact_pokemon_battle_stats' THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COUNT(*) FROM (SELECT option_key FROM {{table}} GROUP BY option_key HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
