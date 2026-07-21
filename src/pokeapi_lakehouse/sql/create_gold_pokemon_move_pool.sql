CREATE TABLE IF NOT EXISTS {{table}} (
 pokemon_move_key STRING NOT NULL,pokemon_key STRING NOT NULL,pokemon_id BIGINT NOT NULL,
 move_key STRING NOT NULL,move_id BIGINT NOT NULL,
 move_name STRING NOT NULL,damage_class_name STRING,type_id BIGINT,type_name STRING,power INT,
 accuracy_pct INT,expected_power DECIMAL(10,2),priority INT NOT NULL,
 learn_method_id BIGINT NOT NULL,learn_method_name STRING NOT NULL,level_learned_at INT NOT NULL,
 ruleset_key STRING NOT NULL COMMENT 'FK lógica para dim_ruleset',
 ruleset_id STRING NOT NULL COMMENT 'scarlet-violet|singles|level-50|v1',
 gold_transformed_at TIMESTAMP NOT NULL,gold_run_id STRING NOT NULL
) USING DELTA CLUSTER BY (pokemon_id,move_id)
COMMENT 'Movepool disponível em Scarlet/Violet para recomendação de batalha'
