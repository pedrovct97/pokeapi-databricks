CREATE TABLE IF NOT EXISTS {{table}} (
 game_version_key STRING NOT NULL COMMENT 'Chave canônica do jogo/versão no formato game_version|version_id',
 version_id BIGINT NOT NULL COMMENT 'Identificador do jogo/versão na PokéAPI',
 version_name STRING NOT NULL COMMENT 'Nome técnico do jogo/versão, como emerald, yellow, firered ou diamond',
 display_name STRING NOT NULL COMMENT 'Nome amigável do jogo exibido no dashboard',
 version_group_key STRING NOT NULL COMMENT 'Chave canônica do grupo de versão associado ao jogo',
 version_group_id BIGINT NOT NULL COMMENT 'Identificador do grupo de versão associado ao jogo',
 version_group_name STRING NOT NULL COMMENT 'Nome técnico do grupo de versão associado ao jogo',
 generation_id BIGINT NOT NULL COMMENT 'Identificador da geração derivada do grupo de versão',
 generation_name STRING NOT NULL COMMENT 'Nome técnico da geração derivada do grupo de versão',
 region_name STRING COMMENT 'Nome técnico da região principal da geração quando disponível na PokéAPI',
 gold_transformed_at TIMESTAMP NOT NULL COMMENT 'Momento horário de Brasília (UTC-3) da publicação Gold',
 gold_run_id STRING NOT NULL COMMENT 'UUID da execução Gold responsável pela publicação'
) USING DELTA COMMENT 'Dimensão Gold de jogos e versões para filtros de dashboard e contexto de ruleset'
