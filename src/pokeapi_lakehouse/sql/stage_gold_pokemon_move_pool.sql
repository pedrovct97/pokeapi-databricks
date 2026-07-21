CREATE OR REPLACE TEMP VIEW gold_pokemon_move_pool_stage AS
SELECT CONCAT_WS('|','pokemon-move','scarlet-violet','singles','level-50','v1',
 CAST(pm.pokemon_id AS STRING),CAST(pm.move_id AS STRING),
 CAST(pm.learn_method_id AS STRING),CAST(pm.level_learned_at AS STRING)) pokemon_move_key,
 CONCAT_WS('|','pokemon',CAST(pm.pokemon_id AS STRING)) pokemon_key,pm.pokemon_id,
 bm.move_key,pm.move_id,bm.move_name,bm.damage_class_name,bm.type_id,bm.type_name,bm.power,
 bm.accuracy_pct,bm.expected_power,bm.priority,pm.learn_method_id,pm.learn_method_name,
 pm.level_learned_at,'ruleset|scarlet-violet|singles|level-50|v1' ruleset_key,
 'scarlet-violet|singles|level-50|v1' ruleset_id,
 CURRENT_TIMESTAMP() gold_transformed_at,{{run_id}} gold_run_id
FROM {{pokemon_move}} pm JOIN {{battle_move}} bm ON bm.move_id=pm.move_id
JOIN {{pokemon_catalog}} p ON p.pokemon_id=pm.pokemon_id
WHERE pm.version_group_name='scarlet-violet'
