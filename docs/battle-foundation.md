# Gold: fundação de batalhas

## Ruleset

Os produtos de batalha usam rulesets derivados do grupo de versão e do nível de batalha:

```txt
ruleset|<version_group_name>|singles|level-<battle_level>|v1
```

- todos os `version_group_name` disponíveis em `dim_version_group`;
- batalha individual 1v1;
- níveis publicados `50`, `80` e `100`;
- IV 31;
- EVs e nature neutros;
- sem terastalização, clima, terreno ou condições de status.

O ruleset é uma dimensão semântica do cálculo. Resultados de versões diferentes não devem ser
misturados.

## Produtos

### `dim_ruleset`, `dim_type` e `dim_ability`

Dimensões conformadas para o ruleset, tipos elementais e habilidades. Centralizam descrições e
chaves `ruleset|...`, `type|id` e `ability|id`, evitando repetir atributos descritivos nos fatos.

### `fact_type_matchup`

Uma linha por tipo atacante e tipo defensor. Expande as exceções da Silver com o multiplicador
neutro `1.0`, formando uma matriz completa. A chave é
`attacking_type_id|defending_type_id`.

### `fact_pokemon_battle_stats`

Uma linha por Pokémon publicado em `dim_pokemon`. Contém os seis stats, total de stats,
perfil ofensivo e arrays de fraquezas, resistências e imunidades. Para Pokémon de dois tipos, os
multiplicadores são combinados por produto: por exemplo, `2 × 2 = 4` e `2 × 0.5 = 1`.

Os stats ainda são valores base, não stats finais de combate. EV, IV, nature e nível serão
aplicados pelo motor de simulação posterior.

### `dim_move`

Uma linha por movimento. `expected_power` é um baseline simples:

```text
power × accuracy / 100
```

Precisão nula é tratada como `100` somente nessa métrica de ordenação. O campo não representa a
fórmula oficial completa de dano e não considera STAB, defesa, efeitos, prioridade ou habilidade.

### `bridge_pokemon_move`

Uma linha por Pokémon, movimento, método, nível de aprendizado, grupo de versão e nível de batalha.
A chave inclui `version_group_name`, formato singles, `battle_level`, movimento, método e nível para
preservar as diferentes formas de aprendizado. Esta tabela impede que o motor recomende movimentos
indisponíveis no ruleset escolhido.

### `fact_pokemon_matchup`

Uma linha direcional por jogo/versão, nível de batalha, atacante e defensor elegíveis no movepool,
excluindo o autoconfronto. Para cada lado, seleciona o movimento de dano com maior valor esperado e
calcula stats neutros nos níveis publicados (`50`, `80` e `100`). O dano baseline usa o fator de
nível, poder, ataque/defesa física ou especial, STAB, produto da efetividade dos tipos e fator
aleatório médio `0.925`.

`attacker_win_probability` é uma transformação logística do score determinístico. Ela é um label
sintético para validação e futuro experimento de ML; não representa frequência observada em
batalhas reais. A tabela registra movimento, multiplicadores, dano, percentual de HP, turnos para
KO, ordem esperada, vencedor e justificativa. As métricas finais de dano, percentual,
score e probabilidade são publicadas como `DECIMAL` para evitar ruído visual/binário de
`DOUBLE` em consultas e dashboards.

Principais colunas documentadas no Unity Catalog:

| Coluna | Semântica |
|---|---|
| `matchup_key` | Chave direcional no formato `matchup|version_name|ruleset_id|attacker_id|defender_id`. |
| `version_name` / `game_version_display_name` | Jogo/versão usado como filtro principal do dashboard. |
| `version_group_name` | Grupo de versão usado para regras e disponibilidade de golpes. |
| `battle_level` | Nível de batalha do cálculo (`50`, `80` ou `100`). |
| `attacker_*` | Métricas calculadas do melhor movimento do Pokémon atacante contra o defensor. |
| `defender_*` | Métricas calculadas do melhor movimento do defensor contra o atacante. |
| `*_type_multiplier` | Efetividade combinada do tipo do movimento contra os tipos do alvo. |
| `*_stab_multiplier` | Multiplicador STAB; `1.5` quando movimento e Pokémon compartilham tipo. |
| `*_expected_damage` | Dano esperado arredondado em `DECIMAL(10,2)`. |
| `*_damage_pct` | Percentual de HP removido, publicado como `DECIMAL(10,2)`. |
| `*_turns_to_ko` | Turnos estimados para nocautear; `999` quando o lado não consegue causar dano. |
| `matchup_score` | Score determinístico em `DECIMAL(10,2)` usado como entrada da probabilidade sintética. |
| `attacker_win_probability` | Probabilidade sintética em `DECIMAL(4,2)`, não observacional. |
| `prediction_reason` | Explicação auditável contendo melhor movimento, efetividade, turnos e imunidades. |

## Qualidade e linhagem

Cada produto possui DDL, staging, `MERGE` idempotente e consulta de qualidade. `_gold_runs`
registra uma linha por produto e execução. Nulos técnicos, faixas inválidas ou chaves duplicadas
fazem a task falhar.

Para `fact_pokemon_matchup`, o DDL da tabela continua centralizado, mas os SQLs de staging,
`MERGE` e qualidade são apenas os particionados por `version_group_name` ou
`version_group_name|battle_level`. O caminho full/global foi removido para evitar uma rota pesada
não usada pelo job atual.

O job `gold_transformation` separa a fundação Gold do fato pesado de matchup:

1. `publish_gold_products` publica contexto de jogo, `dim_pokemon` e produtos de batalha menores.
2. `publish_matchup_partitions` usa `for_each_task` para calcular `fact_pokemon_matchup` com
   estratégia híbrida de partições:
   - grupos leves usam uma entrada `version_group_name` e cada task calcula os níveis `50`, `80` e
     `100` do grupo;
   - grupos pesados usam entradas `version_group_name|battle_level`, reduzindo o tamanho de cada
     task sem remover `battle_level` da fact ou da chave via `ruleset_id`.

Spark distribui cada partição em tasks nos executors disponíveis; o job não fixa literalmente “um
worker por partição Delta”. A estratégia híbrida evita um único DAG global com todos os pares
atacante/defensor, preserva menos overhead que particionar tudo por nível e quebra os maiores grupos
para reduzir stragglers.

Grupos inicialmente splitados por nível por serem mais pesados nos testes de performance:

- `ultra-sun-ultra-moon`;
- `sun-moon`;
- `scarlet-violet`;
- `omega-ruby-alpha-sapphire`;
- `x-y`;
- `sword-shield`;
- `black-2-white-2`;
- `black-white`;
- `heartgold-soulsilver`;
- `diamond-pearl`.

O parâmetro `matchup_partitions` lista os grupos de versão com movepool disponível no ambiente atual.
Se a Silver passar a publicar golpes para novos grupos, essa lista deve ser atualizada ou substituída
por geração dinâmica antes do run.

## Modelo dimensional e compatibilidade

Os objetos canônicos seguem os prefixos `dim_`, `fact_` e `bridge_`. Depois da publicação e da
qualidade, o job substitui os nomes anteriores por views somente leitura:

| View legada | Objeto canônico |
|---|---|
| `pokemon_catalog` | `dim_pokemon` |
| `type_matchup_matrix` | `fact_type_matchup` |
| `pokemon_battle_profile` | `fact_pokemon_battle_stats` |
| `battle_move` | `dim_move` |
| `pokemon_move_pool` | `bridge_pokemon_move` |

Novos pipelines devem usar os objetos canônicos. As views existem apenas para transição e não
recebem `MERGE`.

## Validação no Databricks

```sql
SELECT product, status, published_count, error_message
FROM workspace.pokeapi_gold_dev._gold_runs
ORDER BY started_at DESC;

SELECT damage_multiplier, COUNT(*) AS matchups
FROM workspace.pokeapi_gold_dev.fact_type_matchup
GROUP BY damage_multiplier
ORDER BY damage_multiplier;

SELECT pokemon_id, pokemon_name, base_stat_total, weaknesses, resistances, immunities
FROM workspace.pokeapi_gold_dev.fact_pokemon_battle_stats
WHERE pokemon_id IN (1, 6, 25)
ORDER BY pokemon_id;

SELECT COUNT(*) AS move_pool_rows, COUNT(DISTINCT pokemon_id) AS pokemon
FROM workspace.pokeapi_gold_dev.bridge_pokemon_move;

SELECT attacker_pokemon_id, defender_pokemon_id, attacker_best_move_name,
 attacker_win_probability, predicted_winner_key, prediction_reason
FROM workspace.pokeapi_gold_dev.fact_pokemon_matchup
WHERE version_name='scarlet'
 AND battle_level=50
 AND attacker_pokemon_id=25
 AND defender_pokemon_id=6;
```

O notebook `notebooks/pokemon_matchup_dashboard.py` fornece seletores, imagens e a explicação do
baseline. O treinamento de ML só deve começar depois da reconciliação deste fato no Databricks.
