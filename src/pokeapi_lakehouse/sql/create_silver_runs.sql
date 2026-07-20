CREATE TABLE IF NOT EXISTS {{table}} (
  silver_run_id STRING NOT NULL COMMENT 'UUID da execução Silver',
  entity STRING NOT NULL COMMENT 'Entidade processada',
  started_at TIMESTAMP NOT NULL COMMENT 'Início UTC da transformação',
  finished_at TIMESTAMP NOT NULL COMMENT 'Fim UTC ou último checkpoint',
  status STRING NOT NULL COMMENT 'RUNNING, SUCCESS ou FAILED',
  source_count BIGINT NOT NULL COMMENT 'Versões atuais encontradas na Bronze',
  valid_count BIGINT NOT NULL COMMENT 'Registros aprovados para publicação',
  quarantined_count BIGINT NOT NULL COMMENT 'Registros rejeitados',
  inserted_count BIGINT NOT NULL COMMENT 'Novas chaves inseridas na Silver',
  published_count BIGINT NOT NULL COMMENT 'Total atual da entidade na Silver',
  duration_ms BIGINT NOT NULL COMMENT 'Duração da entidade em milissegundos',
  transformer_version STRING NOT NULL COMMENT 'Versão do transformador Silver',
  error_message STRING COMMENT 'Resumo técnico da falha'
)
USING DELTA
COMMENT 'Reconciliação das transformações da camada Silver'
