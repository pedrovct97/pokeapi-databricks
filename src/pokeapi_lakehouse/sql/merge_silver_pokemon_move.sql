MERGE INTO {{table}} t USING (
 SELECT pokemon_id,move_id,move_name,version_group_id,version_group_name,learn_method_id,
 learn_method_name,level_learned_at,sort_order,source_url,source_payload_sha256,
 source_observed_at,silver_transformed_at,silver_run_id
 FROM silver_pokemon_move_stage WHERE is_valid
) s ON t.pokemon_id=s.pokemon_id AND t.move_id=s.move_id
 AND t.version_group_id=s.version_group_id AND t.learn_method_id=s.learn_method_id
 AND t.level_learned_at=s.level_learned_at
WHEN MATCHED AND t.source_payload_sha256<>s.source_payload_sha256 THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE THEN DELETE
