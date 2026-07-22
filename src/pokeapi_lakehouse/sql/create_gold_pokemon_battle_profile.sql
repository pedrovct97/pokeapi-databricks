CREATE TABLE IF NOT EXISTS {{table}} (
 pokemon_battle_stats_key STRING NOT NULL COMMENT 'Chave canônica do perfil de batalha do Pokémon no ruleset',
 ruleset_key STRING NOT NULL COMMENT 'Chave do ruleset aplicado ao perfil de batalha',
 pokemon_key STRING NOT NULL COMMENT 'Chave canônica do Pokémon',
 pokemon_id BIGINT NOT NULL COMMENT 'Identificador PokéAPI do Pokémon',
 pokemon_name STRING NOT NULL COMMENT 'Nome em inglês do Pokémon',
 hp INT NOT NULL COMMENT 'HP base publicado na Silver',
 attack INT NOT NULL COMMENT 'Ataque físico base publicado na Silver',
 defense INT NOT NULL COMMENT 'Defesa física base publicada na Silver',
 special_attack INT NOT NULL COMMENT 'Ataque especial base publicado na Silver',
 special_defense INT NOT NULL COMMENT 'Defesa especial base publicada na Silver',
 speed INT NOT NULL COMMENT 'Velocidade base publicada na Silver',
 base_stat_total INT NOT NULL COMMENT 'Soma dos seis stats base',
 primary_offense STRING NOT NULL COMMENT 'Classe ofensiva dominante do Pokémon no baseline: physical ou special',
 weaknesses ARRAY<STRUCT<type_id:BIGINT,name:STRING,multiplier:DOUBLE>> NOT NULL COMMENT 'Tipos que causam dano aumentado ao Pokémon e seus multiplicadores combinados',
 resistances ARRAY<STRUCT<type_id:BIGINT,name:STRING,multiplier:DOUBLE>> NOT NULL COMMENT 'Tipos que causam dano reduzido ao Pokémon e seus multiplicadores combinados',
 immunities ARRAY<STRUCT<type_id:BIGINT,name:STRING,multiplier:DOUBLE>> NOT NULL COMMENT 'Tipos que não causam dano ao Pokémon no baseline de efetividade',
 gold_transformed_at TIMESTAMP NOT NULL COMMENT 'Momento horário de Brasília (UTC-3) da publicação Gold',
 gold_run_id STRING NOT NULL COMMENT 'UUID da execução Gold responsável pela publicação'
) USING DELTA CLUSTER BY (pokemon_id)
COMMENT 'Perfil Gold de batalha com stats base e efetividades defensivas por Pokémon'
