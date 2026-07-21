CREATE OR REPLACE TEMP VIEW gold_pokemon_catalog_stage AS
WITH localized_types AS (
 SELECT pt.pokemon_id,
  SORT_ARRAY(COLLECT_LIST(NAMED_STRUCT('slot',pt.slot,'type_id',pt.type_id,
   'name',COALESCE(te.localized_name,pt.type_name)))) types
 FROM {{pokemon_type}} pt
 LEFT JOIN {{type_translation}} te ON te.type_id=pt.type_id AND te.language_code='en'
 GROUP BY pt.pokemon_id
), localized_abilities AS (
 SELECT pa.pokemon_id,
  SORT_ARRAY(COLLECT_LIST(NAMED_STRUCT('slot',pa.slot,'ability_id',pa.ability_id,
   'name',COALESCE(ae.localized_name,pa.ability_name),'is_hidden',pa.is_hidden))) abilities
 FROM {{pokemon_ability}} pa
 LEFT JOIN {{ability_translation}} ae ON ae.ability_id=pa.ability_id AND ae.language_code='en'
 GROUP BY pa.pokemon_id
), aggregated_stats AS (
 SELECT pokemon_id,SORT_ARRAY(COLLECT_LIST(NAMED_STRUCT('stat_id',stat_id,'name',stat_name,
  'base_stat',base_stat,'effort',effort))) stats
 FROM {{pokemon_stat}} GROUP BY pokemon_id
)
SELECT CONCAT_WS('|','pokemon',CAST(p.pokemon_id AS STRING)) pokemon_key,
 p.pokemon_id,COALESCE(english.localized_name,p.pokemon_name) localized_name,
 p.pokemon_name canonical_name,p.species_id,english.genus,english.flavor_text description,
 ps.generation_id,ps.generation_name,p.height_m,p.weight_kg,p.base_experience,p.is_default,
 ps.is_baby,ps.is_legendary,ps.is_mythical,lt.types,st.stats,la.abilities,
 GREATEST(p.source_observed_at,ps.source_observed_at) source_max_observed_at,
 CURRENT_TIMESTAMP() gold_transformed_at,{{run_id}} gold_run_id
FROM {{pokemon}} p
LEFT JOIN {{pokemon_species}} ps ON ps.species_id=p.species_id
LEFT JOIN {{pokemon_species_translation}} english
 ON english.species_id=p.species_id AND english.language_code='en'
LEFT JOIN localized_types lt ON lt.pokemon_id=p.pokemon_id
LEFT JOIN aggregated_stats st ON st.pokemon_id=p.pokemon_id
LEFT JOIN localized_abilities la ON la.pokemon_id=p.pokemon_id
WHERE la.abilities IS NOT NULL
