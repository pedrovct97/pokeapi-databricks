CREATE TABLE IF NOT EXISTS {{table}} (
  endpoint STRING NOT NULL COMMENT 'Recurso REST v2 de origem',
  resource_id BIGINT COMMENT 'Identificador numérico extraído da URL, quando disponível',
  resource_name STRING COMMENT 'Nome presente no payload, quando disponível',
  source_url STRING NOT NULL COMMENT 'URL canônica do recurso coletado',
  http_status INT NOT NULL COMMENT 'Status HTTP observado na coleta',
  payload_json STRING NOT NULL COMMENT 'Resposta JSON integral, sem regras de negócio',
  payload_sha256 STRING NOT NULL COMMENT 'Hash SHA-256 usado para versão e idempotência',
  source_observed_at TIMESTAMP NOT NULL COMMENT 'Timestamp horário de Brasília (UTC-3) de recebimento da resposta',
  response_bytes BIGINT NOT NULL COMMENT 'Tamanho da resposta HTTP em bytes',
  duration_ms BIGINT NOT NULL COMMENT 'Duração total da requisição em milissegundos',
  attempt_count INT NOT NULL COMMENT 'Quantidade de tentativas da requisição',
  etag STRING COMMENT 'ETag retornado pela fonte, quando disponível',
  last_modified STRING COMMENT 'Last-Modified retornado pela fonte, quando disponível',
  ingested_at TIMESTAMP NOT NULL COMMENT 'Timestamp horário de Brasília (UTC-3) de formação do lote Bronze',
  run_id STRING NOT NULL COMMENT 'UUID da execução de ingestão'
)
USING DELTA
COMMENT 'Payloads JSON imutáveis da PokéAPI REST v2'
