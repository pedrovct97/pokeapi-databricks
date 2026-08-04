MERGE INTO {{table}} AS target
USING (SELECT * FROM silver_pokemon_stage WHERE is_valid) AS source
  ON target.pokemon_id = source.pokemon_id
WHEN MATCHED AND target.source_payload_sha256 <> source.source_payload_sha256 THEN UPDATE SET
  target.pokemon_name = source.pokemon_name,
  target.base_experience = source.base_experience,
  target.height_dm = source.height_dm,
  target.height_m = source.height_m,
  target.weight_hg = source.weight_hg,
  target.weight_kg = source.weight_kg,
  target.is_default = source.is_default,
  target.sort_order = source.sort_order,
  target.species_id = source.species_id,
  target.species_name = source.species_name,
  target.source_url = source.source_url,
  target.source_payload_sha256 = source.source_payload_sha256,
  target.source_observed_at = source.source_observed_at,
  target.silver_transformed_at = source.silver_transformed_at,
  target.silver_run_id = source.silver_run_id
WHEN NOT MATCHED THEN INSERT (
  pokemon_id, pokemon_name, base_experience, height_dm, height_m, weight_hg, weight_kg,
  is_default, sort_order, species_id, species_name, source_url, source_payload_sha256,
  source_observed_at, silver_transformed_at, silver_run_id
)
VALUES (
  source.pokemon_id, source.pokemon_name, source.base_experience, source.height_dm,
  source.height_m, source.weight_hg, source.weight_kg, source.is_default,
  source.sort_order, source.species_id, source.species_name, source.source_url,
  source.source_payload_sha256, source.source_observed_at,
  source.silver_transformed_at, source.silver_run_id
)
WHEN NOT MATCHED BY SOURCE THEN DELETE
