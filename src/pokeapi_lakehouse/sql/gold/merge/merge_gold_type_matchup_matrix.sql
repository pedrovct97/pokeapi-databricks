MERGE INTO {{table}} t USING gold_type_matchup_matrix_stage s ON t.matchup_key=s.matchup_key
WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT * WHEN NOT MATCHED BY SOURCE THEN DELETE
