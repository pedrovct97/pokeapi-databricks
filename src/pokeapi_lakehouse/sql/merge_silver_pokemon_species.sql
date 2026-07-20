MERGE INTO {{table}} t USING (
 SELECT species_id,species_name,sort_order,gender_rate,capture_rate,base_happiness,is_baby,
 is_legendary,is_mythical,hatch_counter,has_gender_differences,forms_switchable,
 generation_id,generation_name,growth_rate_id,growth_rate_name,color_id,color_name,
 shape_id,shape_name,habitat_id,habitat_name,evolves_from_species_id,
 evolves_from_species_name,source_url,source_payload_sha256,source_observed_at,
 silver_transformed_at,silver_run_id FROM silver_pokemon_species_stage WHERE is_valid
) s ON t.species_id=s.species_id
WHEN MATCHED AND t.source_payload_sha256<>s.source_payload_sha256 THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE THEN DELETE
