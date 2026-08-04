CREATE TABLE IF NOT EXISTS {{table}} (
  language_id BIGINT NOT NULL COMMENT 'Identificador do idioma na PokéAPI',
  language_code STRING NOT NULL COMMENT 'Código usado pela PokéAPI; contrato atual: en',
  iso639_code STRING COMMENT 'Código ISO 639 informado pela origem',
  iso3166_code STRING COMMENT 'Código ISO 3166 informado pela origem',
  is_official BOOLEAN NOT NULL COMMENT 'Indica idioma oficial nos jogos',
  source_url STRING NOT NULL COMMENT 'URL do recurso Bronze',
  source_payload_sha256 STRING NOT NULL COMMENT 'Hash da versão Bronze',
  source_observed_at TIMESTAMP NOT NULL COMMENT 'Momento de observação na origem',
  silver_transformed_at TIMESTAMP NOT NULL COMMENT 'Momento horário de Brasília (UTC-3) da transformação',
  silver_run_id STRING NOT NULL COMMENT 'Execução Silver responsável'
) USING DELTA COMMENT 'Idiomas de consumo suportados, normalizados da PokéAPI'
