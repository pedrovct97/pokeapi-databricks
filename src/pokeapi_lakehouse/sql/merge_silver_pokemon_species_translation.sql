MERGE INTO {{table}} t USING (
 SELECT species_id,language_id,language_code,localized_name,genus,flavor_text,source_url,
  source_payload_sha256,source_observed_at,silver_transformed_at,silver_run_id
 FROM silver_pokemon_species_translation_stage WHERE is_valid
) s ON t.species_id=s.species_id AND t.language_id=s.language_id
WHEN MATCHED AND t.source_payload_sha256<>s.source_payload_sha256 THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE THEN DELETE
