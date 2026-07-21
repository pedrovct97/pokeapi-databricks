CREATE OR REPLACE TEMP VIEW gold_type_stage AS
SELECT CONCAT_WS('|','type',CAST(t.type_id AS STRING)) type_key,t.type_id,
 COALESCE(x.localized_name,t.type_name) type_name,t.type_name canonical_name,
 t.generation_id,t.generation_name,t.damage_class_id,t.damage_class_name,
 CURRENT_TIMESTAMP() gold_transformed_at,{{run_id}} gold_run_id
FROM {{type}} t LEFT JOIN {{type_translation}} x ON x.type_id=t.type_id AND x.language_code='en'
