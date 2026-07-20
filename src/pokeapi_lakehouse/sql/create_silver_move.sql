CREATE TABLE IF NOT EXISTS {{table}} (
  move_id BIGINT NOT NULL COMMENT 'Identificador da PokéAPI; chave lógica',
  move_name STRING NOT NULL COMMENT 'Nome canônico do movimento',
  accuracy_pct INT COMMENT 'Precisão percentual; nula quando o movimento ignora precisão',
  effect_chance_pct INT COMMENT 'Chance percentual do efeito secundário',
  pp INT COMMENT 'Quantidade base de pontos de poder',
  priority INT NOT NULL COMMENT 'Prioridade de execução do movimento',
  power INT COMMENT 'Poder base; nulo para movimentos sem dano direto',
  damage_class_id BIGINT COMMENT 'Identificador da classe de dano',
  damage_class_name STRING COMMENT 'physical, special ou status',
  type_id BIGINT COMMENT 'Identificador do tipo elemental',
  type_name STRING COMMENT 'Nome do tipo elemental',
  generation_id BIGINT COMMENT 'Identificador da geração de introdução',
  generation_name STRING COMMENT 'Nome da geração de introdução',
  source_url STRING NOT NULL COMMENT 'URL do registro Bronze utilizado',
  source_payload_sha256 STRING NOT NULL COMMENT 'Versão do payload Bronze',
  source_observed_at TIMESTAMP NOT NULL COMMENT 'Momento UTC da observação na fonte',
  silver_transformed_at TIMESTAMP NOT NULL COMMENT 'Momento UTC da transformação',
  silver_run_id STRING NOT NULL COMMENT 'UUID da execução Silver'
)
USING DELTA
COMMENT 'Cadastro atual tipado de movimentos derivado exclusivamente da Bronze'
