MERGE INTO {{table}} t USING gold_runs_batch s
ON t.gold_run_id=s.gold_run_id AND t.product=s.product
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
