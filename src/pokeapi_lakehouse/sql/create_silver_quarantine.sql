CREATE TABLE IF NOT EXISTS {{table}} (
  silver_run_id STRING NOT NULL COMMENT 'UUID da execução Silver',
  entity STRING NOT NULL COMMENT 'Entidade Silver rejeitada',
  source_url STRING NOT NULL COMMENT 'URL do registro Bronze rejeitado',
  source_payload_sha256 STRING NOT NULL COMMENT 'Versão do payload Bronze rejeitado',
  validation_errors STRING NOT NULL COMMENT 'Regras de qualidade violadas',
  quarantined_at TIMESTAMP NOT NULL COMMENT 'Momento horário de Brasília (UTC-3) da quarentena'
)
USING DELTA
COMMENT 'Registros Bronze que não atenderam ao contrato de publicação Silver'
