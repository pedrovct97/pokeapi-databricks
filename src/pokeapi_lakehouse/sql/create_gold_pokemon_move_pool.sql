CREATE TABLE IF NOT EXISTS {{table}} (
 pokemon_move_key STRING NOT NULL COMMENT 'Chave da relação Pokémon-movimento-método-nível no ruleset',
 pokemon_key STRING NOT NULL COMMENT 'Chave canônica do Pokémon que pode aprender o movimento',
 pokemon_id BIGINT NOT NULL COMMENT 'Identificador PokéAPI do Pokémon que pode aprender o movimento',
 move_key STRING NOT NULL COMMENT 'Chave canônica do movimento disponível',
 move_id BIGINT NOT NULL COMMENT 'Identificador PokéAPI do movimento disponível',
 move_name STRING NOT NULL COMMENT 'Nome em inglês do movimento disponível',
 damage_class_name STRING COMMENT 'Classe de dano do movimento: physical, special ou status',
 type_id BIGINT COMMENT 'Identificador PokéAPI do tipo elemental do movimento',
 type_name STRING COMMENT 'Nome em inglês do tipo elemental do movimento',
 power INT COMMENT 'Poder base do movimento informado pela PokéAPI',
 accuracy_pct INT COMMENT 'Precisão percentual do movimento; nulo quando nunca erra ou não se aplica',
 expected_power DECIMAL(10,2) COMMENT 'Poder esperado simples herdado da dimensão de movimentos',
 priority INT NOT NULL COMMENT 'Prioridade de execução do movimento no turno',
 learn_method_id BIGINT NOT NULL COMMENT 'Identificador PokéAPI do método de aprendizado',
 learn_method_name STRING NOT NULL COMMENT 'Nome em inglês do método de aprendizado',
 level_learned_at INT NOT NULL COMMENT 'Nível de aprendizado do movimento; zero quando não se aplica',
 ruleset_key STRING NOT NULL COMMENT 'Chave canônica do ruleset que filtra a disponibilidade do movimento',
 ruleset_id STRING NOT NULL COMMENT 'Identificador do ruleset que filtra a disponibilidade do movimento',
 gold_transformed_at TIMESTAMP NOT NULL COMMENT 'Momento horário de Brasília (UTC-3) da publicação Gold',
 gold_run_id STRING NOT NULL COMMENT 'UUID da execução Gold responsável pela publicação'
) USING DELTA CLUSTER BY (pokemon_id,move_id)
COMMENT 'Ponte Gold de movimentos disponíveis por Pokémon no ruleset Scarlet/Violet'
