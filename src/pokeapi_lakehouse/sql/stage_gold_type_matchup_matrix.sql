CREATE OR REPLACE TEMP VIEW gold_type_matchup_matrix_stage AS
SELECT CONCAT_WS('|','matchup','scarlet-violet','singles','level-50','v1',
 CAST(a.type_id AS STRING),CAST(d.type_id AS STRING)) matchup_key,
 'ruleset|scarlet-violet|singles|level-50|v1' ruleset_key,
 CONCAT_WS('|','type',CAST(a.type_id AS STRING)) attacking_type_key,
 a.type_id attacking_type_id,a.type_name attacking_type_name,
 CONCAT_WS('|','type',CAST(d.type_id AS STRING)) defending_type_key,
 d.type_id defending_type_id,d.type_name defending_type_name,
 CAST(COALESCE(r.damage_multiplier,1.0) AS DECIMAL(3,1)) damage_multiplier,
 CASE COALESCE(r.damage_multiplier,1.0) WHEN 0.0 THEN 'immune' WHEN 0.5 THEN 'resisted'
  WHEN 2.0 THEN 'super_effective' ELSE 'neutral' END matchup_class,
 CURRENT_TIMESTAMP() gold_transformed_at,{{run_id}} gold_run_id
FROM {{type}} a CROSS JOIN {{type}} d
LEFT JOIN {{type_damage_relation}} r
 ON r.source_type_id=a.type_id AND r.target_type_id=d.type_id
