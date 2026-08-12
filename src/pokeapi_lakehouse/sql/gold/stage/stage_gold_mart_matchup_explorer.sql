CREATE OR REPLACE TEMP VIEW gold_mart_matchup_explorer_stage AS
WITH pokemon_types AS (
 SELECT pokemon_key,
  MAX(CASE WHEN type_info.slot=1 THEN type_info.name END) primary_type_name,
  MAX(CASE WHEN type_info.slot=2 THEN type_info.name END) secondary_type_name
 FROM {{dim_pokemon}}
 LATERAL VIEW EXPLODE(types) exploded AS type_info
 GROUP BY pokemon_key
)
SELECT
 m.matchup_key,
 m.ruleset_key,
 m.ruleset_id,
 m.battle_level,
 m.game_version_key,
 m.version_id,
 m.version_name,
 m.game_version_display_name,
 m.version_group_key,
 m.version_group_name,
 m.attacker_pokemon_key,
 m.attacker_pokemon_id,
 a.canonical_name attacker_canonical_name,
 a.localized_name attacker_display_name,
 at.primary_type_name attacker_primary_type_name,
 at.secondary_type_name attacker_secondary_type_name,
 a.types attacker_types,
 a.sprite_url attacker_sprite_url,
 a.official_artwork_url attacker_official_artwork_url,
 m.defender_pokemon_key,
 m.defender_pokemon_id,
 d.canonical_name defender_canonical_name,
 d.localized_name defender_display_name,
 dt.primary_type_name defender_primary_type_name,
 dt.secondary_type_name defender_secondary_type_name,
 d.types defender_types,
 d.sprite_url defender_sprite_url,
 d.official_artwork_url defender_official_artwork_url,
 m.attacker_best_move_key,
 m.attacker_best_move_name,
 m.attacker_type_multiplier,
 m.attacker_stab_multiplier,
 m.attacker_expected_damage,
 m.attacker_damage_pct,
 m.attacker_turns_to_ko,
 m.defender_best_move_key,
 m.defender_best_move_name,
 m.defender_type_multiplier,
 m.defender_stab_multiplier,
 m.defender_expected_damage,
 m.defender_damage_pct,
 m.defender_turns_to_ko,
 m.attacker_moves_first,
 m.matchup_score,
 m.attacker_win_probability,
 m.predicted_winner_key,
 CASE
  WHEN m.predicted_winner_key=m.attacker_pokemon_key THEN a.localized_name
  WHEN m.predicted_winner_key=m.defender_pokemon_key THEN d.localized_name
  ELSE 'unknown'
 END predicted_winner_display_name,
 m.prediction_reason,
 CURRENT_TIMESTAMP() gold_transformed_at,
 {{run_id}} gold_run_id
FROM {{fact_pokemon_matchup}} m
JOIN {{dim_pokemon}} a ON a.pokemon_key=m.attacker_pokemon_key
JOIN {{dim_pokemon}} d ON d.pokemon_key=m.defender_pokemon_key
LEFT JOIN pokemon_types at ON at.pokemon_key=m.attacker_pokemon_key
LEFT JOIN pokemon_types dt ON dt.pokemon_key=m.defender_pokemon_key
