CREATE TABLE IF NOT EXISTS {{table}} (
  endpoint STRING NOT NULL COMMENT 'Endpoint processado',
  source_url STRING NOT NULL COMMENT 'URL cuja coleta falhou',
  error_type STRING NOT NULL COMMENT 'Classe técnica da exceção',
  error_message STRING NOT NULL COMMENT 'Mensagem truncada, sem payload',
  http_status INT COMMENT 'Status HTTP final, quando disponível',
  attempt_count INT NOT NULL COMMENT 'Quantidade de tentativas realizadas',
  duration_ms BIGINT NOT NULL COMMENT 'Duração total das tentativas em milissegundos',
  is_retriable BOOLEAN NOT NULL COMMENT 'Indica se a categoria da falha permite retry',
  attempted_at TIMESTAMP NOT NULL COMMENT 'Timestamp UTC da tentativa',
  run_id STRING NOT NULL COMMENT 'UUID da execução'
)
USING DELTA
COMMENT 'Falhas individuais observadas durante a ingestão Bronze'
