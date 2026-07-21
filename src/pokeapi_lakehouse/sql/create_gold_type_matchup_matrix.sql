CREATE TABLE IF NOT EXISTS {{table}} (
 matchup_key STRING NOT NULL COMMENT 'PK lógica do ruleset e par de tipos',
 ruleset_key STRING NOT NULL COMMENT 'FK lógica para dim_ruleset',
 attacking_type_key STRING NOT NULL,attacking_type_id BIGINT NOT NULL,attacking_type_name STRING NOT NULL,
 defending_type_key STRING NOT NULL,defending_type_id BIGINT NOT NULL,defending_type_name STRING NOT NULL,
 damage_multiplier DECIMAL(3,1) NOT NULL COMMENT '0, 0.5, 1 ou 2',
 matchup_class STRING NOT NULL COMMENT 'immune, resisted, neutral ou super_effective',
 gold_transformed_at TIMESTAMP NOT NULL,gold_run_id STRING NOT NULL
) USING DELTA COMMENT 'Matriz completa de efetividade entre tipos'
