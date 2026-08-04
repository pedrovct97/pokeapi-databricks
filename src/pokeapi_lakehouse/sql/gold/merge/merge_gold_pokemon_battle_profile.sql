MERGE INTO {{table}} t USING gold_pokemon_battle_profile_stage s
ON t.pokemon_battle_stats_key=s.pokemon_battle_stats_key
WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT * WHEN NOT MATCHED BY SOURCE THEN DELETE
