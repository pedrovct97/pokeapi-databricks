CREATE TABLE IF NOT EXISTS {{table}} (
 pokemon_id BIGINT NOT NULL, slot INT NOT NULL, type_id BIGINT NOT NULL, type_name STRING NOT NULL,
 source_url STRING NOT NULL, source_payload_sha256 STRING NOT NULL,
 source_observed_at TIMESTAMP NOT NULL, silver_transformed_at TIMESTAMP NOT NULL,
 silver_run_id STRING NOT NULL
) USING DELTA COMMENT 'Relação entre Pokémon e tipos elementais'
