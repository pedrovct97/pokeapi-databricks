CREATE OR REPLACE TEMP VIEW gold_pokemon_matchup_stage AS
WITH eligible AS (
 SELECT DISTINCT mp.ruleset_key,mp.ruleset_id,mp.battle_level,p.pokemon_key,p.pokemon_id
 FROM {{dim_pokemon}} p JOIN {{bridge_pokemon_move}} mp ON mp.pokemon_id=p.pokemon_id
 WHERE mp.ruleset_key LIKE CONCAT('ruleset|',{{version_group_name}},'|singles|level-%|v1')
  AND mp.battle_level IN (50,80,100)
), level_stats AS (
 SELECT e.ruleset_key,e.ruleset_id,e.battle_level,s.pokemon_key,s.pokemon_id,
  CAST(FLOOR(((2*s.hp+31)*e.battle_level)/100)+e.battle_level+10 AS INT) hp,
  CAST(FLOOR(((2*s.attack+31)*e.battle_level)/100)+5 AS INT) attack,
  CAST(FLOOR(((2*s.defense+31)*e.battle_level)/100)+5 AS INT) defense,
  CAST(FLOOR(((2*s.special_attack+31)*e.battle_level)/100)+5 AS INT) special_attack,
  CAST(FLOOR(((2*s.special_defense+31)*e.battle_level)/100)+5 AS INT) special_defense,
  CAST(FLOOR(((2*s.speed+31)*e.battle_level)/100)+5 AS INT) speed
 FROM {{fact_pokemon_battle_stats}} s JOIN eligible e
  ON e.pokemon_id=s.pokemon_id AND e.ruleset_key=s.ruleset_key
), moves AS (
 SELECT DISTINCT mp.ruleset_key,mp.ruleset_id,mp.battle_level,mp.pokemon_id,mp.move_key,
  mp.move_name,mp.damage_class_name,mp.type_id,mp.power,mp.accuracy_pct,mp.priority
 FROM {{bridge_pokemon_move}} mp
 WHERE mp.power>0 AND mp.damage_class_name IN ('physical','special')
  AND mp.ruleset_key LIKE CONCAT('ruleset|',{{version_group_name}},'|singles|level-%|v1')
  AND mp.battle_level IN (50,80,100)
), moves_with_stab AS (
 SELECT m.ruleset_key,m.ruleset_id,m.battle_level,m.pokemon_id,m.move_key,m.move_name,
  m.damage_class_name,m.type_id,m.power,m.accuracy_pct,m.priority,
  CASE WHEN MAX(CASE WHEN pt.type_id=m.type_id THEN 1 ELSE 0 END)=1 THEN 1.5 ELSE 1.0 END stab
 FROM moves m LEFT JOIN {{pokemon_type}} pt ON pt.pokemon_id=m.pokemon_id
 GROUP BY m.ruleset_key,m.ruleset_id,m.battle_level,m.pokemon_id,m.move_key,m.move_name,
  m.damage_class_name,m.type_id,m.power,m.accuracy_pct,m.priority
), options AS (
 SELECT a.ruleset_key,a.ruleset_id,a.battle_level,a.pokemon_id attacker_id,d.pokemon_id defender_id,
  m.move_key,m.move_name,m.damage_class_name,m.power,m.accuracy_pct,m.priority,m.stab,
  AGGREGATE(COLLECT_LIST(CAST(COALESCE(r.damage_multiplier,1.0) AS DOUBLE)),
   CAST(1.0 AS DOUBLE),(acc,x)->acc*x) type_multiplier
 FROM eligible a
 JOIN moves_with_stab m ON m.ruleset_key=a.ruleset_key AND m.pokemon_id=a.pokemon_id
 JOIN eligible d ON d.ruleset_key=a.ruleset_key AND d.pokemon_id<>a.pokemon_id
 JOIN {{pokemon_type}} dt ON dt.pokemon_id=d.pokemon_id
 LEFT JOIN {{type_damage_relation}} r ON r.source_type_id=m.type_id AND r.target_type_id=dt.type_id
 GROUP BY a.ruleset_key,a.ruleset_id,a.battle_level,a.pokemon_id,d.pokemon_id,m.move_key,m.move_name,
  m.damage_class_name,m.power,m.accuracy_pct,m.priority,m.stab
), damage AS (
 SELECT o.*,a.speed attacker_speed,d.hp defender_hp,
  CASE WHEN o.damage_class_name='physical' THEN a.attack ELSE a.special_attack END offense_stat,
  CASE WHEN o.damage_class_name='physical' THEN d.defense ELSE d.special_defense END defense_stat
 FROM options o
 JOIN level_stats a ON a.ruleset_key=o.ruleset_key AND a.pokemon_id=o.attacker_id
 JOIN level_stats d ON d.ruleset_key=o.ruleset_key AND d.pokemon_id=o.defender_id
), calculated AS (
 SELECT ruleset_key,ruleset_id,battle_level,attacker_id,defender_id,move_key,move_name,
  accuracy_pct,priority,attacker_speed,defender_hp,stab,type_multiplier,
  CAST((((((2.0*battle_level)/5.0)+2.0)*power*offense_stat/defense_stat)/50.0+2.0)*stab*type_multiplier*0.925 AS DOUBLE)
   expected_damage
 FROM damage
), ranked AS (
 SELECT ruleset_key,ruleset_id,battle_level,attacker_id,defender_id,move_key,move_name,
  accuracy_pct,priority,attacker_speed,defender_hp,stab,type_multiplier,expected_damage,
  ROW_NUMBER() OVER(PARTITION BY ruleset_key,attacker_id,defender_id
   ORDER BY expected_damage*COALESCE(accuracy_pct,100)/100.0 DESC,priority DESC,move_key) move_rank
 FROM calculated
), best AS (
 SELECT ruleset_key,ruleset_id,battle_level,attacker_id,defender_id,move_key,move_name,priority,
  attacker_speed,defender_hp,stab,type_multiplier,expected_damage,expected_damage/defender_hp*100.0 damage_pct,
  CASE WHEN type_multiplier=0 THEN 999 ELSE CAST(CEIL(defender_hp/expected_damage) AS INT) END turns_to_ko
 FROM ranked WHERE move_rank=1
), duels AS (
 SELECT a.ruleset_key,a.ruleset_id,a.battle_level,a.attacker_id,a.defender_id,
  a.move_key attacker_move_key,a.move_name attacker_move_name,a.priority attacker_priority,
  a.attacker_speed,a.stab attacker_stab,a.type_multiplier attacker_type,
  a.expected_damage attacker_damage,a.damage_pct attacker_damage_pct,a.turns_to_ko attacker_turns,
  d.move_key defender_move_key,d.move_name defender_move_name,d.priority defender_priority,
  d.attacker_speed defender_speed,d.stab defender_stab,d.type_multiplier defender_type,
  d.expected_damage defender_damage,d.damage_pct defender_damage_pct,d.turns_to_ko defender_turns
 FROM best a JOIN best d ON d.ruleset_key=a.ruleset_key AND d.attacker_id=a.defender_id
  AND d.defender_id=a.attacker_id
), scored AS (
 SELECT ruleset_key,ruleset_id,battle_level,attacker_id,defender_id,attacker_move_key,
  attacker_move_name,attacker_priority,attacker_speed,attacker_stab,attacker_type,attacker_damage,
  attacker_damage_pct,attacker_turns,defender_move_key,defender_move_name,defender_priority,
  defender_speed,defender_stab,defender_type,defender_damage,defender_damage_pct,defender_turns,
  attacker_priority>defender_priority OR
  (attacker_priority=defender_priority AND attacker_speed>=defender_speed) attacker_first,
  (defender_turns-attacker_turns)*20.0+(attacker_damage_pct-defender_damage_pct)*0.25+
  CASE WHEN attacker_priority>defender_priority OR
   (attacker_priority=defender_priority AND attacker_speed>=defender_speed) THEN 5.0 ELSE -5.0 END score
 FROM duels
), game_versions AS (
 SELECT game_version_key,version_id,version_name,display_name game_version_display_name,
  version_group_key,version_group_name
 FROM {{dim_game_version}}
 WHERE version_group_name={{version_group_name}}
)
SELECT CONCAT_WS('|','matchup',gv.version_name,s.ruleset_id,
 CAST(attacker_id AS STRING),CAST(defender_id AS STRING)) matchup_key,
 s.ruleset_key,s.ruleset_id,s.battle_level,
 gv.game_version_key,gv.version_id,gv.version_name,gv.game_version_display_name,
 gv.version_group_key,gv.version_group_name,
 CONCAT_WS('|','pokemon',CAST(attacker_id AS STRING)) attacker_pokemon_key,attacker_id attacker_pokemon_id,
 CONCAT_WS('|','pokemon',CAST(defender_id AS STRING)) defender_pokemon_key,defender_id defender_pokemon_id,
 attacker_move_key attacker_best_move_key,attacker_move_name attacker_best_move_name,
 attacker_type attacker_type_multiplier,attacker_stab attacker_stab_multiplier,
 CAST(ROUND(attacker_damage,2) AS DECIMAL(10,2)) attacker_expected_damage,
 CAST(ROUND(attacker_damage_pct,2) AS DECIMAL(10,2)) attacker_damage_pct,attacker_turns attacker_turns_to_ko,
 defender_move_key defender_best_move_key,defender_move_name defender_best_move_name,
 defender_type defender_type_multiplier,defender_stab defender_stab_multiplier,
 CAST(ROUND(defender_damage,2) AS DECIMAL(10,2)) defender_expected_damage,
 CAST(ROUND(defender_damage_pct,2) AS DECIMAL(10,2)) defender_damage_pct,defender_turns defender_turns_to_ko,
 attacker_first attacker_moves_first,CAST(ROUND(score,2) AS DECIMAL(10,2)) matchup_score,
 CAST(ROUND(1.0/(1.0+EXP(-score/15.0)),2) AS DECIMAL(4,2)) attacker_win_probability,
 CASE WHEN attacker_turns<defender_turns OR (attacker_turns=defender_turns AND attacker_first)
  THEN CONCAT_WS('|','pokemon',CAST(attacker_id AS STRING))
  ELSE CONCAT_WS('|','pokemon',CAST(defender_id AS STRING)) END predicted_winner_key,
 CONCAT_WS('; ',CONCAT('best_move=',attacker_move_name),
  CONCAT('effectiveness=',CAST(attacker_type AS STRING)),
  CONCAT('turns_to_ko=',CAST(attacker_turns AS STRING)),
  CONCAT('opponent_turns=',CAST(defender_turns AS STRING)),
  CASE WHEN attacker_damage=0 THEN 'attacker_cannot_damage' END,
  CASE WHEN defender_damage=0 THEN 'defender_cannot_damage' END) prediction_reason,
 CURRENT_TIMESTAMP() gold_transformed_at,{{run_id}} gold_run_id
FROM scored s JOIN game_versions gv ON gv.version_group_name={{version_group_name}}
