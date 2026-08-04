CREATE TABLE IF NOT EXISTS {{table}} (
 move_id BIGINT NOT NULL COMMENT 'Identificador do movimento', language_id BIGINT NOT NULL COMMENT 'Identificador do idioma',
 language_code STRING NOT NULL COMMENT 'Código do idioma', localized_name STRING NOT NULL COMMENT 'Nome localizado',
 flavor_text STRING COMMENT 'Descrição localizada', effect_text STRING COMMENT 'Efeito completo localizado',
 short_effect_text STRING COMMENT 'Resumo do efeito localizado', source_url STRING NOT NULL COMMENT 'URL Bronze',
 source_payload_sha256 STRING NOT NULL COMMENT 'Hash Bronze', source_observed_at TIMESTAMP NOT NULL COMMENT 'Observação da origem',
 silver_transformed_at TIMESTAMP NOT NULL COMMENT 'Transformação horário de Brasília (UTC-3)', silver_run_id STRING NOT NULL COMMENT 'Execução Silver'
) USING DELTA COMMENT 'Textos localizados de movimentos; uma linha por movimento e idioma'
