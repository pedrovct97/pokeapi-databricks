CREATE TABLE IF NOT EXISTS {{table}} (
 pokemon_id BIGINT NOT NULL,move_id BIGINT NOT NULL,move_name STRING NOT NULL,
 version_group_id BIGINT NOT NULL,version_group_name STRING NOT NULL,
 learn_method_id BIGINT NOT NULL,learn_method_name STRING NOT NULL,
 level_learned_at INT NOT NULL,sort_order INT,
 source_url STRING NOT NULL,source_payload_sha256 STRING NOT NULL,
 source_observed_at TIMESTAMP NOT NULL,silver_transformed_at TIMESTAMP NOT NULL,
 silver_run_id STRING NOT NULL
) USING DELTA COMMENT 'Movimentos aprendidos por Pokémon, versão e método'
