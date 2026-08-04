CREATE TABLE IF NOT EXISTS {{table}} (
 pokemon_key STRING NOT NULL COMMENT 'PK lógica determinística: pokemon|id',
 pokemon_id BIGINT NOT NULL COMMENT 'Identificador do Pokémon',
 localized_name STRING NOT NULL COMMENT 'Nome oficial em inglês',
 canonical_name STRING NOT NULL COMMENT 'Nome técnico estável da PokéAPI',
 species_id BIGINT COMMENT 'Identificador da espécie',
 genus STRING COMMENT 'Classificação da espécie em inglês',
 description STRING COMMENT 'Descrição da espécie em inglês',
 generation_id BIGINT COMMENT 'Geração de origem',
 generation_name STRING COMMENT 'Nome técnico da geração',
 height_m DECIMAL(10,2) NOT NULL COMMENT 'Altura em metros',
 weight_kg DECIMAL(10,2) NOT NULL COMMENT 'Peso em quilogramas',
 base_experience BIGINT COMMENT 'Experiência base',
 is_default BOOLEAN NOT NULL COMMENT 'Indica variedade padrão',
 is_baby BOOLEAN COMMENT 'Indica estágio bebê',
 is_legendary BOOLEAN COMMENT 'Indica Pokémon lendário',
 is_mythical BOOLEAN COMMENT 'Indica Pokémon mítico',
 official_artwork_url STRING COMMENT 'Imagem oficial padrão da PokéAPI',
 official_artwork_shiny_url STRING COMMENT 'Imagem oficial shiny da PokéAPI',
 sprite_url STRING COMMENT 'Sprite frontal padrão',sprite_shiny_url STRING COMMENT 'Sprite frontal shiny',
 types ARRAY<STRUCT<slot:INT,type_id:BIGINT,name:STRING>> NOT NULL COMMENT 'Tipos ordenados em inglês',
 stats ARRAY<STRUCT<stat_id:BIGINT,name:STRING,base_stat:INT,effort:INT>> NOT NULL COMMENT 'Estatísticas base',
 abilities ARRAY<STRUCT<slot:INT,ability_id:BIGINT,name:STRING,is_hidden:BOOLEAN>> NOT NULL COMMENT 'Habilidades ordenadas em inglês',
 source_max_observed_at TIMESTAMP NOT NULL COMMENT 'Maior observação Silver utilizada',
 gold_transformed_at TIMESTAMP NOT NULL COMMENT 'Momento horário de Brasília (UTC-3) da publicação',
 gold_run_id STRING NOT NULL COMMENT 'Execução Gold responsável'
) USING DELTA
CLUSTER BY (pokemon_id)
COMMENT 'Catálogo em inglês de Pokémon pronto para SQL e futura API web'
