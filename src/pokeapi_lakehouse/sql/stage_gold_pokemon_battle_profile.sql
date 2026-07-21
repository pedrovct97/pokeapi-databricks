CREATE OR REPLACE TEMP VIEW gold_pokemon_battle_profile_stage AS
WITH stats AS (
 SELECT pokemon_id,
  MAX(CASE WHEN stat_name='hp' THEN base_stat END) hp,
  MAX(CASE WHEN stat_name='attack' THEN base_stat END) attack,
  MAX(CASE WHEN stat_name='defense' THEN base_stat END) defense,
  MAX(CASE WHEN stat_name='special-attack' THEN base_stat END) special_attack,
  MAX(CASE WHEN stat_name='special-defense' THEN base_stat END) special_defense,
  MAX(CASE WHEN stat_name='speed' THEN base_stat END) speed,SUM(base_stat) base_stat_total
 FROM {{pokemon_stat}} GROUP BY pokemon_id
), combined AS (
 SELECT pt.pokemon_id,a.type_id,a.type_name,
  AGGREGATE(COLLECT_LIST(CAST(COALESCE(r.damage_multiplier,1.0) AS DOUBLE)),
   CAST(1.0 AS DOUBLE),(acc,x)->acc*x) multiplier
 FROM {{pokemon_type}} pt CROSS JOIN {{type}} a
 LEFT JOIN {{type_damage_relation}} r
  ON r.source_type_id=a.type_id AND r.target_type_id=pt.type_id
 GROUP BY pt.pokemon_id,a.type_id,a.type_name
), matchups AS (
 SELECT pokemon_id,
  SORT_ARRAY(FILTER(COLLECT_LIST(NAMED_STRUCT('type_id',type_id,'name',type_name,'multiplier',multiplier)),x->x.multiplier>1.0)) weaknesses,
  SORT_ARRAY(FILTER(COLLECT_LIST(NAMED_STRUCT('type_id',type_id,'name',type_name,'multiplier',multiplier)),x->x.multiplier>0.0 AND x.multiplier<1.0)) resistances,
  SORT_ARRAY(FILTER(COLLECT_LIST(NAMED_STRUCT('type_id',type_id,'name',type_name,'multiplier',multiplier)),x->x.multiplier=0.0)) immunities
 FROM combined GROUP BY pokemon_id
)
SELECT CONCAT_WS('|','battle-stats','scarlet-violet','singles','level-50','v1',
 CAST(p.pokemon_id AS STRING)) pokemon_battle_stats_key,
 'ruleset|scarlet-violet|singles|level-50|v1' ruleset_key,
 p.pokemon_key,p.pokemon_id,p.localized_name pokemon_name,s.hp,s.attack,s.defense,
 s.special_attack,s.special_defense,s.speed,s.base_stat_total,
 CASE WHEN s.attack>=s.special_attack THEN 'physical' ELSE 'special' END primary_offense,
 m.weaknesses,m.resistances,m.immunities,CURRENT_TIMESTAMP() gold_transformed_at,{{run_id}} gold_run_id
FROM {{pokemon_catalog}} p JOIN stats s ON s.pokemon_id=p.pokemon_id
JOIN matchups m ON m.pokemon_id=p.pokemon_id
