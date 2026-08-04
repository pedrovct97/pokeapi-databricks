MERGE INTO {{table}} t USING (
 SELECT stat_id,stat_name,game_index,is_battle_only,damage_class_id,damage_class_name,
 source_url,source_payload_sha256,source_observed_at,silver_transformed_at,silver_run_id
 FROM silver_stat_stage WHERE is_valid
) s ON t.stat_id=s.stat_id
WHEN MATCHED AND t.source_payload_sha256<>s.source_payload_sha256 THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE THEN DELETE
