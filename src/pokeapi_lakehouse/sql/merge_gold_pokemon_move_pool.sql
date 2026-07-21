MERGE INTO {{table}} t USING gold_pokemon_move_pool_stage s ON t.pokemon_move_key=s.pokemon_move_key
WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT * WHEN NOT MATCHED BY SOURCE THEN DELETE
