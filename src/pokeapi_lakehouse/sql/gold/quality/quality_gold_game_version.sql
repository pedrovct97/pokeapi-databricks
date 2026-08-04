SELECT
 SUM(CASE WHEN game_version_key IS NULL OR version_id IS NULL OR version_name IS NULL
  OR display_name IS NULL OR version_group_key IS NULL OR version_group_id IS NULL
  OR version_group_name IS NULL OR generation_id IS NULL OR generation_name IS NULL
  OR gold_transformed_at IS NULL OR gold_run_id IS NULL THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN game_version_key<>CONCAT_WS('|','game_version',CAST(version_id AS STRING))
  OR version_group_key<>CONCAT_WS('|','version_group',CAST(version_group_id AS STRING))
  OR display_name NOT LIKE 'Pokémon %' THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COUNT(*) FROM (SELECT game_version_key FROM {{table}} GROUP BY game_version_key HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
