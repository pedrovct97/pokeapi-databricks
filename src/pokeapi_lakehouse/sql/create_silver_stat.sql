CREATE TABLE IF NOT EXISTS {{table}} (
  stat_id BIGINT NOT NULL, stat_name STRING NOT NULL, game_index INT,
  is_battle_only BOOLEAN NOT NULL, damage_class_id BIGINT, damage_class_name STRING,
  source_url STRING NOT NULL, source_payload_sha256 STRING NOT NULL,
  source_observed_at TIMESTAMP NOT NULL, silver_transformed_at TIMESTAMP NOT NULL,
  silver_run_id STRING NOT NULL
) USING DELTA COMMENT 'Estatísticas tipadas da PokéAPI'
