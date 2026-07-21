CREATE TABLE IF NOT EXISTS {{table}} (
 move_key STRING NOT NULL,move_id BIGINT NOT NULL,move_name STRING NOT NULL,
 description STRING,damage_class_name STRING,type_id BIGINT,type_name STRING,
 power INT,accuracy_pct INT,expected_power DECIMAL(10,2),priority INT NOT NULL,pp INT,
 effect_chance_pct INT,gold_transformed_at TIMESTAMP NOT NULL,gold_run_id STRING NOT NULL
) USING DELTA CLUSTER BY (move_id)
COMMENT 'Movimentos preparados para o ruleset Scarlet/Violet singles 1v1'
