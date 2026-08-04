MERGE INTO {{table}} t USING (
  SELECT type_id,type_name,generation_id,generation_name,damage_class_id,damage_class_name,
    source_url,source_payload_sha256,source_observed_at,silver_transformed_at,silver_run_id
  FROM silver_type_stage WHERE is_valid
) s ON t.type_id=s.type_id
WHEN MATCHED AND t.source_payload_sha256<>s.source_payload_sha256 THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE THEN DELETE
