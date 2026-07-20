CREATE TABLE IF NOT EXISTS {{table}} (
  type_id BIGINT NOT NULL COMMENT 'Identificador da PokéAPI', type_name STRING NOT NULL,
  generation_id BIGINT, generation_name STRING, damage_class_id BIGINT,
  damage_class_name STRING, source_url STRING NOT NULL,
  source_payload_sha256 STRING NOT NULL, source_observed_at TIMESTAMP NOT NULL,
  silver_transformed_at TIMESTAMP NOT NULL, silver_run_id STRING NOT NULL
) USING DELTA COMMENT 'Tipos elementais tipados da PokéAPI'
