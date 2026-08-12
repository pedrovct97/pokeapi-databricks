CREATE OR REPLACE TEMP VIEW gold_mart_game_pokemon_options_stage AS
WITH eligible AS (
 SELECT DISTINCT ruleset_key,ruleset_id,battle_level,pokemon_key,pokemon_id
 FROM {{fact_pokemon_battle_stats}}
), parsed AS (
 SELECT *,SPLIT(ruleset_key,'\\|')[1] version_group_name
 FROM eligible
), game_options AS (
 SELECT gv.game_version_key,gv.version_id,gv.version_name,gv.display_name game_version_display_name,
  gv.version_group_key,gv.version_group_id,gv.version_group_name,gv.generation_id,gv.generation_name,
  gv.region_name,p.battle_level,p.pokemon_key,p.pokemon_id
 FROM parsed p
 JOIN {{dim_game_version}} gv ON gv.version_group_name=p.version_group_name
), pokemon_types AS (
 SELECT pokemon_key,
  MAX(CASE WHEN type_info.slot=1 THEN type_info.name END) primary_type_name,
  MAX(CASE WHEN type_info.slot=2 THEN type_info.name END) secondary_type_name
 FROM {{dim_pokemon}}
 LATERAL VIEW EXPLODE(types) exploded AS type_info
 GROUP BY pokemon_key
)
SELECT CONCAT_WS('|','game_pokemon_option',g.version_name,CAST(g.battle_level AS STRING),CAST(g.pokemon_id AS STRING)) option_key,
 g.game_version_key,g.version_id,g.version_name,g.game_version_display_name,
 g.version_group_key,g.version_group_id,g.version_group_name,g.generation_id,g.generation_name,g.region_name,
 g.battle_level,p.pokemon_key,p.pokemon_id,p.canonical_name,p.localized_name,p.localized_name display_name,
 p.species_id,p.generation_id pokemon_generation_id,p.generation_name pokemon_generation_name,
 pt.primary_type_name,pt.secondary_type_name,p.types,p.sprite_url,p.official_artwork_url,
 p.is_default,p.is_baby,p.is_legendary,p.is_mythical,
 TRUE is_available_for_battle,'fact_pokemon_battle_stats' availability_source,
 CURRENT_TIMESTAMP() gold_transformed_at,{{run_id}} gold_run_id
FROM game_options g
JOIN {{dim_pokemon}} p ON p.pokemon_key=g.pokemon_key
LEFT JOIN pokemon_types pt ON pt.pokemon_key=p.pokemon_key
