CREATE TABLE IF NOT EXISTS {{table}} (
 pokemon_id BIGINT NOT NULL,ability_id BIGINT NOT NULL,ability_name STRING NOT NULL,
 slot INT NOT NULL,is_hidden BOOLEAN NOT NULL,source_url STRING NOT NULL,
 source_payload_sha256 STRING NOT NULL,source_observed_at TIMESTAMP NOT NULL,
 silver_transformed_at TIMESTAMP NOT NULL,silver_run_id STRING NOT NULL
) USING DELTA COMMENT 'Relação entre Pokémon e habilidades'
