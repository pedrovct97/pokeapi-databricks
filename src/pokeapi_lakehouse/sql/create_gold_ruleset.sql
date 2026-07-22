CREATE TABLE IF NOT EXISTS {{table}} (
 ruleset_key STRING NOT NULL COMMENT 'Chave canônica do ruleset de batalha',
 ruleset_id STRING NOT NULL COMMENT 'Identificador legível do ruleset',
 version_group_name STRING NOT NULL COMMENT 'Grupo de versão da PokéAPI usado para disponibilidade de movimentos',
 battle_format STRING NOT NULL COMMENT 'Formato de batalha considerado pelo baseline',
 level INT NOT NULL COMMENT 'Nível fixo usado nos cálculos de batalha',
 iv INT NOT NULL COMMENT 'Valor de IV assumido para todos os stats',
 ev_policy STRING NOT NULL COMMENT 'Política de EV aplicada pelo ruleset',
 nature_policy STRING NOT NULL COMMENT 'Política de nature aplicada pelo ruleset',
 terastalization_enabled BOOLEAN NOT NULL COMMENT 'Indica se terastalização é considerada no baseline',
 rule_version INT NOT NULL COMMENT 'Versão semântica interna das premissas do ruleset',
 gold_transformed_at TIMESTAMP NOT NULL COMMENT 'Momento horário de Brasília (UTC-3) da publicação Gold',
 gold_run_id STRING NOT NULL COMMENT 'UUID da execução Gold responsável pela publicação'
) USING DELTA COMMENT 'Rulesets versionados usados pelos fatos de batalha'
