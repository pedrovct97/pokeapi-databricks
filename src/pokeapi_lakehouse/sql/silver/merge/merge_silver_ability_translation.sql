MERGE INTO {{table}} t USING (SELECT ability_id,language_id,language_code,localized_name,flavor_text,effect_text,short_effect_text,
 source_url,source_payload_sha256,source_observed_at,silver_transformed_at,silver_run_id FROM silver_ability_translation_stage WHERE is_valid) s
ON t.ability_id=s.ability_id AND t.language_id=s.language_id
WHEN MATCHED AND t.source_payload_sha256<>s.source_payload_sha256 THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE THEN DELETE
