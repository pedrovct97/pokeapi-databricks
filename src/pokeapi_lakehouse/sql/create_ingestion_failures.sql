CREATE TABLE IF NOT EXISTS {{table}} (
  endpoint STRING NOT NULL COMMENT 'Endpoint processado',
  source_url STRING NOT NULL COMMENT 'URL cuja coleta falhou',
  error_type STRING NOT NULL COMMENT 'Classe técnica da exceção',
  error_message STRING NOT NULL COMMENT 'Mensagem truncada, sem payload',
  attempted_at TIMESTAMP NOT NULL COMMENT 'Timestamp UTC da tentativa',
  run_id STRING NOT NULL COMMENT 'UUID da execução'
)
USING DELTA
COMMENT 'Falhas individuais observadas durante a ingestão Bronze'
