CREATE TABLE IF NOT EXISTS {{table}} (
 ability_key STRING NOT NULL,ability_id BIGINT NOT NULL,ability_name STRING NOT NULL,
 canonical_name STRING NOT NULL,is_main_series BOOLEAN NOT NULL,generation_id BIGINT,
 generation_name STRING,description STRING,gold_transformed_at TIMESTAMP NOT NULL,
 gold_run_id STRING NOT NULL
) USING DELTA COMMENT 'Dimensão Gold de habilidades'
