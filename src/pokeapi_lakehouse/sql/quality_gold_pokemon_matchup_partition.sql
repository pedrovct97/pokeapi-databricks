WITH scoped AS (
 SELECT * FROM {{table}}
 WHERE version_group_name={{version_group_name}}
)
SELECT SUM(CASE WHEN matchup_key IS NULL OR ruleset_key IS NULL OR ruleset_id IS NULL
 OR battle_level IS NULL OR game_version_key IS NULL OR version_id IS NULL OR version_name IS NULL
 OR game_version_display_name IS NULL OR version_group_key IS NULL OR version_group_name IS NULL
 OR attacker_pokemon_key IS NULL OR defender_pokemon_key IS NULL OR attacker_best_move_key IS NULL
 OR defender_best_move_key IS NULL OR predicted_winner_key IS NULL THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN attacker_pokemon_id=defender_pokemon_id OR attacker_win_probability NOT BETWEEN 0 AND 1
  OR battle_level NOT IN (50,80,100)
  OR version_group_name<>{{version_group_name}}
  OR game_version_key<>CONCAT_WS('|','game_version',CAST(version_id AS STRING))
  OR ruleset_id<>CONCAT_WS('|',version_group_name,'singles',CONCAT('level-',CAST(battle_level AS STRING)),'v1')
  OR ruleset_key<>CONCAT_WS('|','ruleset',version_group_name,'singles',CONCAT('level-',CAST(battle_level AS STRING)),'v1')
  OR attacker_turns_to_ko<1 OR defender_turns_to_ko<1 OR attacker_expected_damage<0
  OR defender_expected_damage<0
  OR (attacker_expected_damage=0 AND (attacker_type_multiplier<>0 OR attacker_turns_to_ko<>999))
  OR (defender_expected_damage=0 AND (defender_type_multiplier<>0 OR defender_turns_to_ko<>999))
  OR (attacker_expected_damage>0 AND attacker_turns_to_ko=999)
  OR (defender_expected_damage>0 AND defender_turns_to_ko=999) THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COUNT(*) FROM (SELECT matchup_key FROM scoped GROUP BY matchup_key HAVING COUNT(*)>1)) duplicate_count
FROM scoped
