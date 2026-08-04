MERGE INTO {{table}} AS target
USING (SELECT * FROM silver_move_stage WHERE is_valid) AS source
  ON target.move_id = source.move_id
WHEN MATCHED AND target.source_payload_sha256 <> source.source_payload_sha256 THEN UPDATE SET
  target.move_name = source.move_name,
  target.accuracy_pct = source.accuracy_pct,
  target.effect_chance_pct = source.effect_chance_pct,
  target.pp = source.pp,
  target.priority = source.priority,
  target.power = source.power,
  target.damage_class_id = source.damage_class_id,
  target.damage_class_name = source.damage_class_name,
  target.type_id = source.type_id,
  target.type_name = source.type_name,
  target.generation_id = source.generation_id,
  target.generation_name = source.generation_name,
  target.source_url = source.source_url,
  target.source_payload_sha256 = source.source_payload_sha256,
  target.source_observed_at = source.source_observed_at,
  target.silver_transformed_at = source.silver_transformed_at,
  target.silver_run_id = source.silver_run_id
WHEN NOT MATCHED THEN INSERT (
  move_id, move_name, accuracy_pct, effect_chance_pct, pp, priority, power,
  damage_class_id, damage_class_name, type_id, type_name, generation_id,
  generation_name, source_url, source_payload_sha256, source_observed_at,
  silver_transformed_at, silver_run_id
)
VALUES (
  source.move_id, source.move_name, source.accuracy_pct, source.effect_chance_pct,
  source.pp, source.priority, source.power, source.damage_class_id,
  source.damage_class_name, source.type_id, source.type_name, source.generation_id,
  source.generation_name, source.source_url, source.source_payload_sha256,
  source.source_observed_at, source.silver_transformed_at, source.silver_run_id
)
WHEN NOT MATCHED BY SOURCE THEN DELETE
