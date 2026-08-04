CREATE OR REPLACE TEMP VIEW gold_pokemon_move_pool_stage AS
SELECT
 CONCAT_WS('|','pokemon-move',r.version_group_name,'singles',CONCAT('level-',CAST(r.level AS STRING)),'v1',
  CAST(pm.pokemon_id AS STRING),CAST(pm.move_id AS STRING),
  CAST(pm.learn_method_id AS STRING),CAST(pm.level_learned_at AS STRING)) pokemon_move_key,
 CONCAT_WS('|','pokemon',CAST(pm.pokemon_id AS STRING)) pokemon_key,
 pm.pokemon_id,
 bm.move_key,
 pm.move_id,
 bm.move_name,
 bm.damage_class_name,
 bm.type_id,
 bm.type_name,
 bm.power,
 bm.accuracy_pct,
 bm.expected_power,
 bm.priority,
 pm.learn_method_id,
 pm.learn_method_name,
 pm.level_learned_at,
 r.ruleset_key,
 r.ruleset_id,
 r.level battle_level,
 CURRENT_TIMESTAMP() gold_transformed_at,
 {{run_id}} gold_run_id
FROM {{pokemon_move}} pm
JOIN {{battle_move}} bm ON bm.move_id=pm.move_id
JOIN {{pokemon_catalog}} p ON p.pokemon_id=pm.pokemon_id
JOIN {{dim_ruleset}} r ON r.version_group_name=pm.version_group_name
