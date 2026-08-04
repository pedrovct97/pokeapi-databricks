MERGE INTO {{table}} t USING (SELECT type_id,language_id,language_code,localized_name,source_url,source_payload_sha256,
 source_observed_at,silver_transformed_at,silver_run_id FROM silver_type_translation_stage WHERE is_valid) s
ON t.type_id=s.type_id AND t.language_id=s.language_id
WHEN MATCHED AND t.source_payload_sha256<>s.source_payload_sha256 THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE THEN DELETE
