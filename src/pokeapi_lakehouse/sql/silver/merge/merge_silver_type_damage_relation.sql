MERGE INTO {{table}} t USING (
 SELECT source_type_id,source_type_name,target_type_id,target_type_name,damage_multiplier,
 source_url,source_payload_sha256,source_observed_at,silver_transformed_at,silver_run_id
 FROM silver_type_damage_relation_stage WHERE is_valid
) s ON t.source_type_id=s.source_type_id AND t.target_type_id=s.target_type_id
WHEN MATCHED AND t.source_payload_sha256<>s.source_payload_sha256 THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE THEN DELETE
