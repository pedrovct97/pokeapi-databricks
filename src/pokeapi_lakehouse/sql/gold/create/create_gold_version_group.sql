CREATE TABLE IF NOT EXISTS {{table}} (
 version_group_key STRING NOT NULL COMMENT 'Chave canônica do grupo de versão no formato version_group|version_group_id',
 version_group_id BIGINT NOT NULL COMMENT 'Identificador do grupo de versão na PokéAPI',
 version_group_name STRING NOT NULL COMMENT 'Nome técnico do grupo de versão, como emerald ou firered-leafgreen',
 generation_id BIGINT NOT NULL COMMENT 'Identificador da geração associada ao grupo de versão',
 generation_name STRING NOT NULL COMMENT 'Nome técnico da geração associada ao grupo de versão',
 order_index INT NOT NULL COMMENT 'Ordem oficial do grupo de versão usada para ordenação no dashboard',
 gold_transformed_at TIMESTAMP NOT NULL COMMENT 'Momento horário de Brasília (UTC-3) da publicação Gold',
 gold_run_id STRING NOT NULL COMMENT 'UUID da execução Gold responsável pela publicação'
) USING DELTA COMMENT 'Dimensão Gold de grupos de versão da PokéAPI para contexto de jogo e rulesets'
