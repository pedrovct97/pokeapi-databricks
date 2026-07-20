CREATE TABLE IF NOT EXISTS {{table}} (
  run_id STRING NOT NULL COMMENT 'UUID da execução',
  endpoint STRING NOT NULL COMMENT 'Endpoint processado',
  started_at TIMESTAMP NOT NULL COMMENT 'Início UTC do processamento do endpoint',
  finished_at TIMESTAMP NOT NULL COMMENT 'Fim UTC do processamento do endpoint',
  status STRING NOT NULL COMMENT 'SUCCESS, PARTIAL ou FAILED',
  discovered_count BIGINT NOT NULL COMMENT 'Quantidade de URLs descobertas',
  fetched_count BIGINT NOT NULL COMMENT 'Quantidade de respostas válidas',
  inserted_count BIGINT NOT NULL COMMENT 'Quantidade de novas versões inseridas',
  failed_count BIGINT NOT NULL COMMENT 'Quantidade de recursos com falha',
  error_message STRING COMMENT 'Resumo técnico da falha, sem payload'
)
USING DELTA
COMMENT 'Reconciliação das execuções de ingestão Bronze por endpoint'
