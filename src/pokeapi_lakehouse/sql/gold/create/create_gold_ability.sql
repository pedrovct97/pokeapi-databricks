CREATE TABLE IF NOT EXISTS {{table}} (
 ability_key STRING NOT NULL COMMENT 'Chave canônica da habilidade no formato ability|id',
 ability_id BIGINT NOT NULL COMMENT 'Identificador PokéAPI da habilidade',
 ability_name STRING NOT NULL COMMENT 'Nome em inglês da habilidade',
 canonical_name STRING NOT NULL COMMENT 'Nome canônico normalizado para consumo analítico',
 is_main_series BOOLEAN NOT NULL COMMENT 'Indica se a habilidade pertence à série principal',
 generation_id BIGINT COMMENT 'Identificador da geração em que a habilidade foi introduzida',
 generation_name STRING COMMENT 'Nome da geração em que a habilidade foi introduzida',
 description STRING COMMENT 'Descrição localizada em inglês usada para interpretação da habilidade',
 gold_transformed_at TIMESTAMP NOT NULL COMMENT 'Momento horário de Brasília (UTC-3) da publicação Gold',
 gold_run_id STRING NOT NULL COMMENT 'UUID da execução Gold responsável pela publicação'
) USING DELTA COMMENT 'Dimensão Gold de habilidades Pokémon'
