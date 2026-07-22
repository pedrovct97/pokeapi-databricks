CREATE TABLE IF NOT EXISTS {{table}} (
 type_key STRING NOT NULL COMMENT 'Chave canônica do tipo elemental no formato type|id',
 type_id BIGINT NOT NULL COMMENT 'Identificador PokéAPI do tipo elemental',
 type_name STRING NOT NULL COMMENT 'Nome em inglês do tipo elemental',
 canonical_name STRING NOT NULL COMMENT 'Nome canônico normalizado para consumo analítico',
 generation_id BIGINT COMMENT 'Identificador da geração em que o tipo foi introduzido',
 generation_name STRING COMMENT 'Nome da geração em que o tipo foi introduzido',
 damage_class_id BIGINT COMMENT 'Identificador da classe de dano associada ao tipo, quando aplicável',
 damage_class_name STRING COMMENT 'Nome da classe de dano associada ao tipo, quando aplicável',
 gold_transformed_at TIMESTAMP NOT NULL COMMENT 'Momento horário de Brasília (UTC-3) da publicação Gold',
 gold_run_id STRING NOT NULL COMMENT 'UUID da execução Gold responsável pela publicação'
) USING DELTA COMMENT 'Dimensão Gold de tipos elementais da PokéAPI'
