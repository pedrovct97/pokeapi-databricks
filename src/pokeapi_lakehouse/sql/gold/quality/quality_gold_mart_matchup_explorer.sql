SELECT
 SUM(CASE WHEN matchup_key IS NULL OR ruleset_key IS NULL OR ruleset_id IS NULL
  OR battle_level IS NULL OR game_version_key IS NULL OR version_id IS NULL OR version_name IS NULL
  OR game_version_display_name IS NULL OR version_group_key IS NULL OR version_group_name IS NULL
  OR attacker_pokemon_key IS NULL OR attacker_pokemon_id IS NULL OR attacker_canonical_name IS NULL
  OR attacker_display_name IS NULL OR attacker_types IS NULL OR defender_pokemon_key IS NULL
  OR defender_pokemon_id IS NULL OR defender_canonical_name IS NULL OR defender_display_name IS NULL
  OR defender_types IS NULL OR attacker_best_move_key IS NULL OR attacker_best_move_name IS NULL
  OR attacker_type_multiplier IS NULL OR attacker_stab_multiplier IS NULL OR attacker_expected_damage IS NULL
  OR attacker_damage_pct IS NULL OR attacker_turns_to_ko IS NULL OR defender_best_move_key IS NULL
  OR defender_best_move_name IS NULL OR defender_type_multiplier IS NULL OR defender_stab_multiplier IS NULL
  OR defender_expected_damage IS NULL OR defender_damage_pct IS NULL OR defender_turns_to_ko IS NULL
  OR attacker_moves_first IS NULL OR matchup_score IS NULL OR attacker_win_probability IS NULL
  OR predicted_winner_key IS NULL OR predicted_winner_display_name IS NULL OR prediction_reason IS NULL
  THEN 1 ELSE 0 END) technical_null_count,
 SUM(CASE WHEN battle_level NOT IN (50,80,100)
  OR attacker_pokemon_key=defender_pokemon_key
  OR attacker_type_multiplier<0 OR defender_type_multiplier<0
  OR attacker_stab_multiplier NOT IN (1.0,1.5) OR defender_stab_multiplier NOT IN (1.0,1.5)
  OR attacker_expected_damage<0 OR defender_expected_damage<0
  OR attacker_damage_pct<0 OR defender_damage_pct<0
  OR attacker_turns_to_ko<1 OR defender_turns_to_ko<1
  OR attacker_win_probability<0 OR attacker_win_probability>1
  OR predicted_winner_key NOT IN (attacker_pokemon_key,defender_pokemon_key)
  OR SIZE(attacker_types)=0 OR SIZE(defender_types)=0
  THEN 1 ELSE 0 END) range_violation_count,
 (SELECT COUNT(*) FROM (SELECT matchup_key FROM {{table}} GROUP BY matchup_key HAVING COUNT(*)>1)) duplicate_count
FROM {{table}}
