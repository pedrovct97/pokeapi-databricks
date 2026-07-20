MERGE INTO {{table}} t USING (
 SELECT ability_id,ability_name,is_main_series,generation_id,generation_name,source_url,
 source_payload_sha256,source_observed_at,silver_transformed_at,silver_run_id
 FROM silver_ability_stage WHERE is_valid
) s ON t.ability_id=s.ability_id
WHEN MATCHED AND t.source_payload_sha256<>s.source_payload_sha256 THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE THEN DELETE
