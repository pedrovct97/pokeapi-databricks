MERGE INTO {{table}} t USING gold_pokemon_matchup_stage s ON t.matchup_key=s.matchup_key
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
WHEN NOT MATCHED BY SOURCE
 AND t.version_group_name={{version_group_name}}
 AND t.battle_level=CAST({{battle_level}} AS INT)
THEN DELETE
