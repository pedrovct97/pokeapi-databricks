MERGE INTO {{table}} t USING gold_mart_game_pokemon_options_stage s
ON t.option_key=s.option_key
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE THEN DELETE
