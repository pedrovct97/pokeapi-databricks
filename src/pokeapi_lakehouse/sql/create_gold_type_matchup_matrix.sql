CREATE TABLE IF NOT EXISTS {{table}} (
 matchup_key STRING NOT NULL COMMENT 'Chave canônica do confronto entre tipo atacante e tipo defensor',
 ruleset_key STRING NOT NULL COMMENT 'Chave do ruleset aplicado à matriz de efetividade',
 attacking_type_key STRING NOT NULL COMMENT 'Chave canônica do tipo atacante',
 attacking_type_id BIGINT NOT NULL COMMENT 'Identificador PokéAPI do tipo atacante',
 attacking_type_name STRING NOT NULL COMMENT 'Nome em inglês do tipo atacante',
 defending_type_key STRING NOT NULL COMMENT 'Chave canônica do tipo defensor',
 defending_type_id BIGINT NOT NULL COMMENT 'Identificador PokéAPI do tipo defensor',
 defending_type_name STRING NOT NULL COMMENT 'Nome em inglês do tipo defensor',
 damage_multiplier DOUBLE NOT NULL COMMENT 'Multiplicador de efetividade do tipo atacante contra o tipo defensor',
 matchup_class STRING NOT NULL COMMENT 'Classe semântica da efetividade: immune, resisted, neutral ou super_effective',
 gold_transformed_at TIMESTAMP NOT NULL COMMENT 'Momento horário de Brasília (UTC-3) da publicação Gold',
 gold_run_id STRING NOT NULL COMMENT 'UUID da execução Gold responsável pela publicação'
) USING DELTA COMMENT 'Matriz completa de efetividade entre tipos'
