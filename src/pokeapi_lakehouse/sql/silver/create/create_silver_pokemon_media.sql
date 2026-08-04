CREATE TABLE IF NOT EXISTS {{table}} (
 pokemon_id BIGINT NOT NULL COMMENT 'Identificador do Pokémon',
 pokemon_name STRING NOT NULL COMMENT 'Nome técnico da PokéAPI',
 official_artwork_url STRING COMMENT 'Imagem oficial padrão fornecida pela origem',
 official_artwork_shiny_url STRING COMMENT 'Imagem oficial shiny fornecida pela origem',
 sprite_url STRING COMMENT 'Sprite frontal padrão',sprite_shiny_url STRING COMMENT 'Sprite frontal shiny',
 source_url STRING NOT NULL,source_payload_sha256 STRING NOT NULL,
 source_observed_at TIMESTAMP NOT NULL,silver_transformed_at TIMESTAMP NOT NULL,
 silver_run_id STRING NOT NULL
) USING DELTA COMMENT 'Mídias oficiais de Pokémon preservadas separadamente dos atributos de batalha'
