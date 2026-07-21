CREATE TABLE IF NOT EXISTS {{table}} (
  species_id BIGINT NOT NULL COMMENT 'Identificador da espécie', language_id BIGINT NOT NULL COMMENT 'Identificador do idioma',
  language_code STRING NOT NULL COMMENT 'Código do idioma', localized_name STRING NOT NULL COMMENT 'Nome localizado',
  genus STRING COMMENT 'Classificação localizada', flavor_text STRING COMMENT 'Descrição localizada da espécie',
  source_url STRING NOT NULL COMMENT 'URL Bronze', source_payload_sha256 STRING NOT NULL COMMENT 'Hash Bronze',
  source_observed_at TIMESTAMP NOT NULL COMMENT 'Observação da origem', silver_transformed_at TIMESTAMP NOT NULL COMMENT 'Transformação UTC',
  silver_run_id STRING NOT NULL COMMENT 'Execução Silver'
) USING DELTA COMMENT 'Textos localizados de espécies Pokémon; uma linha por espécie e idioma'
