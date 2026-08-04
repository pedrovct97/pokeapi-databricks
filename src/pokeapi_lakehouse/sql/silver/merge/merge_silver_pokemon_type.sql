MERGE INTO {{table}} t USING (
 SELECT pokemon_id,slot,type_id,type_name,source_url,source_payload_sha256,source_observed_at,
 silver_transformed_at,silver_run_id FROM silver_pokemon_type_stage WHERE is_valid
) s ON t.pokemon_id=s.pokemon_id AND t.slot=s.slot
WHEN MATCHED AND t.source_payload_sha256<>s.source_payload_sha256 THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE THEN DELETE
