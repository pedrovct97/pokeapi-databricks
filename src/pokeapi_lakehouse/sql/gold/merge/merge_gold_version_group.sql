MERGE INTO {{table}} t USING gold_version_group_stage s ON t.version_group_key=s.version_group_key
WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT * WHEN NOT MATCHED BY SOURCE THEN DELETE
