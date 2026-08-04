MERGE INTO {{table}} t USING gold_game_version_stage s ON t.game_version_key=s.game_version_key
WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT * WHEN NOT MATCHED BY SOURCE THEN DELETE
