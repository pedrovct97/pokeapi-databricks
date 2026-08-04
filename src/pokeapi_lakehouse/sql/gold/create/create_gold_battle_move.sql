CREATE TABLE IF NOT EXISTS {{table}} (
 move_key STRING NOT NULL COMMENT 'Chave canônica do movimento no formato move|id',
 move_id BIGINT NOT NULL COMMENT 'Identificador PokéAPI do movimento',
 move_name STRING NOT NULL COMMENT 'Nome em inglês do movimento',
 description STRING COMMENT 'Descrição localizada em inglês do efeito do movimento',
 damage_class_name STRING COMMENT 'Classe de dano do movimento: physical, special ou status',
 type_id BIGINT COMMENT 'Identificador PokéAPI do tipo elemental do movimento',
 type_name STRING COMMENT 'Nome em inglês do tipo elemental do movimento',
 power INT COMMENT 'Poder base do movimento informado pela PokéAPI',
 accuracy_pct INT COMMENT 'Precisão percentual do movimento; nulo quando nunca erra ou não se aplica',
 expected_power DECIMAL(10,2) COMMENT 'Poder esperado simples calculado como power vezes accuracy dividido por 100',
 priority INT NOT NULL COMMENT 'Prioridade de execução do movimento no turno',
 pp INT COMMENT 'Quantidade base de usos do movimento',
 effect_chance_pct INT COMMENT 'Chance percentual do efeito secundário, quando aplicável',
 gold_transformed_at TIMESTAMP NOT NULL COMMENT 'Momento horário de Brasília (UTC-3) da publicação Gold',
 gold_run_id STRING NOT NULL COMMENT 'UUID da execução Gold responsável pela publicação'
) USING DELTA CLUSTER BY (move_id)
COMMENT 'Dimensão Gold de movimentos com atributos usados pelo baseline de batalha'
