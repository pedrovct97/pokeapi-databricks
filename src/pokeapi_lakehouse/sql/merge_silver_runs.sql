MERGE INTO {{table}} AS target
USING silver_runs_batch AS source
  ON target.silver_run_id = source.silver_run_id
 AND target.entity = source.entity
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
