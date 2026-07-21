CREATE TABLE IF NOT EXISTS {{table}} (
 pokemon_battle_stats_key STRING NOT NULL,ruleset_key STRING NOT NULL,
 pokemon_key STRING NOT NULL,pokemon_id BIGINT NOT NULL,pokemon_name STRING NOT NULL,
 hp INT NOT NULL,attack INT NOT NULL,defense INT NOT NULL,special_attack INT NOT NULL,
 special_defense INT NOT NULL,speed INT NOT NULL,base_stat_total INT NOT NULL,
 primary_offense STRING NOT NULL COMMENT 'physical ou special',
 weaknesses ARRAY<STRUCT<type_id:BIGINT,name:STRING,multiplier:DOUBLE>> NOT NULL,
 resistances ARRAY<STRUCT<type_id:BIGINT,name:STRING,multiplier:DOUBLE>> NOT NULL,
 immunities ARRAY<STRUCT<type_id:BIGINT,name:STRING,multiplier:DOUBLE>> NOT NULL,
 gold_transformed_at TIMESTAMP NOT NULL,gold_run_id STRING NOT NULL
) USING DELTA CLUSTER BY (pokemon_id)
COMMENT 'Perfil de batalha base sem EV, nature, clima, terreno ou terastalização'
