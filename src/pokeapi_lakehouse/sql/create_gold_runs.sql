CREATE TABLE IF NOT EXISTS {{table}} (
 gold_run_id STRING NOT NULL COMMENT 'UUID da execução Gold', product STRING NOT NULL COMMENT 'Produto publicado',
 started_at TIMESTAMP NOT NULL COMMENT 'Início horário de Brasília (UTC-3)', finished_at TIMESTAMP NOT NULL COMMENT 'Fim horário de Brasília (UTC-3)',
 status STRING NOT NULL COMMENT 'RUNNING, SUCCESS ou FAILED', published_count BIGINT NOT NULL COMMENT 'Linhas publicadas',
 duration_ms BIGINT NOT NULL COMMENT 'Duração em milissegundos', transformer_version STRING NOT NULL COMMENT 'Versão do pacote',
 error_message STRING COMMENT 'Erro acionável quando houver falha'
) USING DELTA COMMENT 'Auditoria das publicações Gold'
