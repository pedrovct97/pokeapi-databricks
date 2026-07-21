CREATE OR REPLACE TEMP VIEW gold_battle_move_stage AS
SELECT CONCAT_WS('|','move',CAST(m.move_id AS STRING)) move_key,m.move_id,
 COALESCE(t.localized_name,m.move_name) move_name,
 COALESCE(t.short_effect_text,t.effect_text,t.flavor_text) description,
 m.damage_class_name,m.type_id,m.type_name,m.power,m.accuracy_pct,
 CAST(CASE WHEN m.power IS NULL THEN NULL
  ELSE m.power*COALESCE(m.accuracy_pct,100)/100.0 END AS DECIMAL(10,2)) expected_power,
 m.priority,m.pp,m.effect_chance_pct,CURRENT_TIMESTAMP() gold_transformed_at,{{run_id}} gold_run_id
FROM {{move}} m LEFT JOIN {{move_translation}} t ON t.move_id=m.move_id AND t.language_code='en'
