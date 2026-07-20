CREATE TABLE IF NOT EXISTS {{table}} (
  species_id BIGINT NOT NULL, species_name STRING NOT NULL, sort_order BIGINT,
  gender_rate INT, capture_rate INT, base_happiness INT, is_baby BOOLEAN NOT NULL,
  is_legendary BOOLEAN NOT NULL, is_mythical BOOLEAN NOT NULL, hatch_counter INT,
  has_gender_differences BOOLEAN NOT NULL, forms_switchable BOOLEAN NOT NULL,
  generation_id BIGINT, generation_name STRING, growth_rate_id BIGINT, growth_rate_name STRING,
  color_id BIGINT, color_name STRING, shape_id BIGINT, shape_name STRING,
  habitat_id BIGINT, habitat_name STRING, evolves_from_species_id BIGINT,
  evolves_from_species_name STRING, source_url STRING NOT NULL,
  source_payload_sha256 STRING NOT NULL, source_observed_at TIMESTAMP NOT NULL,
  silver_transformed_at TIMESTAMP NOT NULL, silver_run_id STRING NOT NULL
) USING DELTA COMMENT 'Espécies Pokémon tipadas da PokéAPI'
