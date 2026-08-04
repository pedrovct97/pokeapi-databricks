CREATE TABLE IF NOT EXISTS {{table}} (
  ability_id BIGINT NOT NULL, ability_name STRING NOT NULL, is_main_series BOOLEAN NOT NULL,
  generation_id BIGINT, generation_name STRING, source_url STRING NOT NULL,
  source_payload_sha256 STRING NOT NULL, source_observed_at TIMESTAMP NOT NULL,
  silver_transformed_at TIMESTAMP NOT NULL, silver_run_id STRING NOT NULL
) USING DELTA COMMENT 'Habilidades tipadas da PokéAPI'
