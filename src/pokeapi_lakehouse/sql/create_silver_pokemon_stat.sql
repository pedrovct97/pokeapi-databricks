CREATE TABLE IF NOT EXISTS {{table}} (
 pokemon_id BIGINT NOT NULL,stat_id BIGINT NOT NULL,stat_name STRING NOT NULL,
 base_stat INT NOT NULL,effort INT NOT NULL,source_url STRING NOT NULL,
 source_payload_sha256 STRING NOT NULL,source_observed_at TIMESTAMP NOT NULL,
 silver_transformed_at TIMESTAMP NOT NULL,silver_run_id STRING NOT NULL
) USING DELTA COMMENT 'Valores base de estatísticas por Pokémon'
