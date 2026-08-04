CREATE OR REPLACE TEMP VIEW gold_ability_stage AS
SELECT CONCAT_WS('|','ability',CAST(a.ability_id AS STRING)) ability_key,a.ability_id,
 COALESCE(x.localized_name,a.ability_name) ability_name,a.ability_name canonical_name,
 a.is_main_series,a.generation_id,a.generation_name,
 COALESCE(x.short_effect_text,x.effect_text,x.flavor_text) description,
 CURRENT_TIMESTAMP() gold_transformed_at,{{run_id}} gold_run_id
FROM {{ability}} a LEFT JOIN {{ability_translation}} x
 ON x.ability_id=a.ability_id AND x.language_code='en'
