CREATE TABLE IF NOT EXISTS {{table}} (
  pokemon_id BIGINT NOT NULL COMMENT 'Identificador da PokéAPI; chave lógica',
  pokemon_name STRING NOT NULL COMMENT 'Nome canônico do Pokémon',
  base_experience BIGINT COMMENT 'Experiência base concedida ao derrotar o Pokémon',
  height_dm BIGINT NOT NULL COMMENT 'Altura original em decímetros',
  height_m DECIMAL(10,2) NOT NULL COMMENT 'Altura derivada em metros',
  weight_hg BIGINT NOT NULL COMMENT 'Peso original em hectogramas',
  weight_kg DECIMAL(10,2) NOT NULL COMMENT 'Peso derivado em quilogramas',
  is_default BOOLEAN NOT NULL COMMENT 'Indica a variedade padrão da espécie',
  sort_order BIGINT COMMENT 'Ordem definida pela origem',
  species_id BIGINT COMMENT 'Identificador da espécie relacionada',
  species_name STRING COMMENT 'Nome da espécie relacionada',
  source_url STRING NOT NULL COMMENT 'URL do registro Bronze utilizado',
  source_payload_sha256 STRING NOT NULL COMMENT 'Versão do payload Bronze',
  source_observed_at TIMESTAMP NOT NULL COMMENT 'Momento horário de Brasília (UTC-3) da observação na fonte',
  silver_transformed_at TIMESTAMP NOT NULL COMMENT 'Momento horário de Brasília (UTC-3) da transformação',
  silver_run_id STRING NOT NULL COMMENT 'UUID da execução Silver'
)
USING DELTA
COMMENT 'Cadastro atual tipado de Pokémon derivado exclusivamente da Bronze'
