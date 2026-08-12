# Dashboard Gold: explorador de matchups por jogo

## Objetivo

Criar uma interface visual para explorar confrontos Pokémon publicados na Gold, priorizando a pergunta do jogador:

> Estou jogando qual versão? Quais Pokémon e golpes estão disponíveis nesse contexto?

O dashboard deve ser claro, visual e explicável. A tela principal deve usar nomes, sprites e rótulos de domínio; IDs técnicos ficam disponíveis apenas em drilldown, auditoria ou tooltip.

## Experiência esperada

### Fluxo principal

1. O usuário seleciona o jogo/versão, por exemplo `emerald`, `yellow`, `firered`, `diamond` ou `scarlet`.
2. A lista de Pokémon atacantes e defensores é restringida ao contexto do jogo selecionado.
3. O usuário escolhe atacante e defensor, ou usa busca textual.
4. O dashboard mostra:
   - card do atacante com sprite, nome, tipos e principais stats;
   - card do defensor com sprite, nome, tipos e principais stats;
   - probabilidade sintética do atacante vencer;
   - melhor golpe disponível para cada lado naquele jogo/ruleset;
   - dano esperado, percentual de HP removido, multiplicadores de tipo, STAB e turnos para KO;
   - explicação textual baseada em `prediction_reason`.
5. O painel lateral mostra ranking de matchups, casos de imunidade e auditoria resumida do run.

### Filtros iniciais

| Filtro | Obrigatório | Observação |
|---|---:|---|
| Jogo/versão | Sim | Deve ser o filtro primário. Substitui o filtro manual de geração na experiência principal. |
| Pokémon atacante | Sim | Lista derivada do jogo/versão selecionado. |
| Pokémon defensor | Sim | Lista derivada do jogo/versão selecionado. |
| Visão | Sim | Resumo do confronto, ranking de melhores matchups, casos de imunidade ou auditoria. |
| Tipo | Futuro | Útil para rankings agregados por tipo. |
| Ruleset | Futuro | Pode aparecer no painel técnico quando houver múltiplos formatos por jogo. |

## Onde a informação existe hoje

A informação de jogo/versão existe na Bronze e parcialmente na Silver/Gold, mas ainda não está modelada como dimensão Gold própria para dashboard.

### Bronze

Estas tabelas existem em `workspace.pokeapi_bronze_dev` e preservam o payload bruto da PokéAPI:

| Tabela | Uso |
|---|---|
| `version` | Uma linha por jogo/versão da PokéAPI, como `emerald`, `yellow`, `firered`, `diamond`. |
| `version_group` | Agrupa versões com regras e disponibilidade semelhantes, como `emerald`, `firered-leafgreen`, `diamond-pearl`. |
| `generation` | Gerações oficiais da PokéAPI. Deve ser derivada do jogo, não filtro principal da UX. |
| `pokedex` | Pode ajudar a derivar disponibilidade regional/local, mas precisa validação de contrato. |

Contagens observadas no ambiente `dev`:

| Endpoint Bronze | Linhas |
|---|---:|
| `version` | 53 |
| `version_group` | 32 |
| `generation` | 9 |
| `pokedex` | 35 |

### Silver

A Silver já expõe disponibilidade de golpes por grupo de versão:

| Tabela | Colunas relevantes |
|---|---|
| `workspace.pokeapi_silver_dev.pokemon_move` | `version_group_id`, `version_group_name`, `pokemon_id`, `move_id`, `learn_method_name`, `level_learned_at` |

Essa tabela é a principal base para restringir os golpes disponíveis por jogo/ruleset.

### Gold atual

A Gold publica contexto de jogo e fundação de batalha por grupo de versão e nível:

| Tabela | Colunas relevantes |
|---|---|
| `workspace.pokeapi_gold_dev.dim_ruleset` | `ruleset_key`, `ruleset_id`, `version_group_name`, `battle_format`, `level` |
| `workspace.pokeapi_gold_dev.bridge_pokemon_move` | `ruleset_key`, `ruleset_id`, `pokemon_id`, `move_id`, `move_name` |
| `workspace.pokeapi_gold_dev.dim_pokemon` | `pokemon_id`, `canonical_name`, `generation_id`, `generation_name`, `official_artwork_url`, `sprite_url`, `types`, `stats` |
| `workspace.pokeapi_gold_dev.mart_game_pokemon_options` | Opções prontas de jogo, nível e Pokémon para filtros/dropdowns da UI. |
| `workspace.pokeapi_gold_dev.mart_matchup_explorer` | Confrontos já enriquecidos com nomes, sprites, tipos, métricas e explicabilidade para a tela principal. |
| `workspace.pokeapi_gold_dev.fact_pokemon_matchup` | `game_version_key`, `version_name`, `game_version_display_name`, `version_group_name`, `battle_level`, métricas finais e `prediction_reason` |

O ruleset de batalha é derivado de `version_group_name` e `battle_level`, no formato
`ruleset|<version_group_name>|singles|level-<battle_level>|v1`.

## Decisão de modelagem

O dashboard consome Gold diretamente para filtros e fatos finais. A dimensão explícita de
jogo/versão evita consultar Bronze na camada visual e mantém a separação Bronze → Silver → Gold.

## Modelo Gold recomendado

### `dim_game_version`

Granularidade: uma linha por jogo/versão da PokéAPI.

| Coluna | Semântica |
|---|---|
| `game_version_key` | Chave canônica no formato `game_version|version_id`. |
| `version_id` | Identificador da versão na PokéAPI. |
| `version_name` | Nome técnico do jogo, como `emerald`, `yellow`, `firered`, `diamond`. |
| `display_name` | Nome amigável para o dashboard, como `Pokémon Emerald`. |
| `version_group_id` | Identificador do grupo de versão associado. |
| `version_group_name` | Nome técnico do grupo, como `emerald` ou `firered-leafgreen`. |
| `generation_id` | Geração derivada do grupo/versão. |
| `generation_name` | Nome técnico da geração, mantido para auditoria e agrupamentos. |
| `region_name` | Região principal quando disponível, como Kanto, Johto, Hoenn ou Sinnoh. |
| `gold_transformed_at` | Momento horário de Brasília (UTC-3) da publicação Gold. |
| `gold_run_id` | UUID da execução Gold responsável pela publicação. |

### `dim_version_group`

Granularidade: uma linha por grupo de versão da PokéAPI.

| Coluna | Semântica |
|---|---|
| `version_group_key` | Chave canônica no formato `version_group|version_group_id`. |
| `version_group_id` | Identificador do grupo de versão na PokéAPI. |
| `version_group_name` | Nome técnico do grupo. |
| `generation_id` | Geração do grupo. |
| `generation_name` | Nome técnico da geração. |
| `order_index` | Ordem oficial usada para ordenação no dashboard. |
| `gold_transformed_at` | Momento horário de Brasília (UTC-3) da publicação Gold. |
| `gold_run_id` | UUID da execução Gold responsável pela publicação. |

## Queries-base do dashboard

### Lista de jogos

```sql
SELECT
  version_name,
  display_name,
  version_group_name,
  generation_name,
  region_name
FROM workspace.pokeapi_gold_dev.dim_game_version
ORDER BY generation_id, version_id;
```

### Lista de Pokémon disponíveis para o jogo

Primeira versão pragmática: consumir a mart Gold `mart_game_pokemon_options`, que considera Pokémon
com perfil de batalha disponível no ruleset do grupo de versão e nível selecionados. Essa mart evita
que a UI precise consultar tabelas técnicas ou escanear a `fact_pokemon_matchup`.

```sql
SELECT
  version_name,
  battle_level,
  pokemon_key,
  pokemon_id,
  localized_name,
  canonical_name,
  display_name,
  primary_type_name,
  secondary_type_name,
  sprite_url,
  official_artwork_url,
  is_legendary,
  is_mythical
FROM workspace.pokeapi_gold_dev.mart_game_pokemon_options
WHERE version_name = :version_name
  AND battle_level = :battle_level
ORDER BY localized_name, pokemon_id;
```

Limitação: essa abordagem usa disponibilidade no perfil de batalha por ruleset como proxy de
disponibilidade do Pokémon. Para disponibilidade fiel por jogo, será necessário modelar
Pokédex/encontros ou outra fonte de presença do Pokémon na versão.

### Confronto selecionado

```sql
SELECT
  attacker_display_name,
  attacker_official_artwork_url,
  attacker_primary_type_name,
  attacker_secondary_type_name,
  defender_display_name,
  defender_official_artwork_url,
  defender_primary_type_name,
  defender_secondary_type_name,
  m.attacker_best_move_name,
  m.attacker_expected_damage,
  m.attacker_damage_pct,
  m.attacker_type_multiplier,
  m.attacker_stab_multiplier,
  m.attacker_turns_to_ko,
  m.defender_best_move_name,
  m.defender_expected_damage,
  m.defender_damage_pct,
  m.defender_type_multiplier,
  m.defender_stab_multiplier,
  m.defender_turns_to_ko,
  m.matchup_score,
  m.attacker_win_probability,
  m.predicted_winner_display_name,
  m.prediction_reason
FROM workspace.pokeapi_gold_dev.mart_matchup_explorer m
WHERE m.version_name = :version_name
  AND m.battle_level = :battle_level
  AND m.attacker_pokemon_key = :attacker_pokemon_key
  AND m.defender_pokemon_key = :defender_pokemon_key;
```

### Ranking visual

```sql
SELECT
  attacker_display_name,
  defender_display_name,
  m.attacker_best_move_name,
  m.defender_best_move_name,
  m.attacker_win_probability,
  m.matchup_score,
  m.prediction_reason
FROM workspace.pokeapi_gold_dev.mart_matchup_explorer m
WHERE m.version_name = :version_name
  AND m.battle_level = :battle_level
ORDER BY m.attacker_win_probability DESC, m.matchup_score DESC
LIMIT :limit;
```

## Critérios de aceite do dashboard

- O filtro primário é jogo/versão, não geração.
- O dashboard não consulta Bronze diretamente.
- Cards principais mostram nomes, tipos e imagens; não mostram IDs por padrão.
- A seleção de jogo restringe Pokémon, golpes, ranking e casos de imunidade.
- Métricas numéricas usam os contratos `DECIMAL` já publicados na Gold.
- `prediction_reason` aparece como explicação em linguagem natural.
- Um painel técnico mostra `_gold_runs`, `transformer_version`, `ruleset_key` e horário de Brasília.

## Status da implementação

A fundação atual do dashboard está implementada na Gold:

- `dim_version_group`: dimensão de grupos de versão da PokéAPI;
- `dim_game_version`: dimensão de jogos/versões para o filtro primário do dashboard;
- `mart_game_pokemon_options`: mart leve de opções por jogo, nível e Pokémon para alimentar filtros
  sem escanear a fact de matchups;
- `mart_matchup_explorer`: mart principal da tela de confronto, derivada da `fact_pokemon_matchup`
  com nomes, tipos, sprites, vencedor previsto e explicabilidade prontos para consumo;
- `fact_pokemon_matchup`: fato de confrontos com colunas de jogo/versão para filtro direto
  (`game_version_key`, `version_id`, `version_name`, `game_version_display_name`,
  `version_group_key`, `version_group_name`) e particionamento por `version_name` e
  `battle_level`.

A fundação de batalha passa a gerar rulesets para todos os grupos de versão disponíveis na Gold e
para os níveis fixos `50`, `80` e `100`, permitindo brincar com mais dados e comparar matchups por
jogo e nível. O dashboard deve expor `Jogo / versão` como filtro primário e `Nível` como filtro
secundário.

O cálculo da `fact_pokemon_matchup` é executado por workers de partição no job
`gold_transformation`: a fundação menor roda primeiro e, depois, `publish_matchup_partitions` usa
`for_each_task` com estratégia híbrida. Grupos leves são processados por `version_group_name` e
calculam os níveis `50`, `80` e `100` juntos; grupos pesados são processados por
`version_group_name|battle_level` para reduzir o tamanho de cada task. Em ambos os casos,
`battle_level` segue presente na fact e no `ruleset_id` usado pela `matchup_key`, então a UI continua
filtrando níveis sem colisão de chave.

Não há mais execução full/global da `fact_pokemon_matchup` dentro da foundation. O job usa somente
os SQLs particionados de matchup, preservando a retomada manual de partições faltantes ou falhadas.
A `mart_game_pokemon_options` roda na task `gold_transform`, depois da fundação de batalha e antes
dos workers pesados de matchup. A `mart_matchup_explorer` roda em uma task posterior,
`publish_matchup_serving_marts`, porque depende da `fact_pokemon_matchup` já consolidada pelos
workers.

Grupos splitados por nível na configuração inicial de performance:
`ultra-sun-ultra-moon`, `sun-moon`, `scarlet-violet`, `omega-ruby-alpha-sapphire`, `x-y`,
`sword-shield`, `black-2-white-2`, `black-white`, `heartgold-soulsilver` e `diamond-pearl`.

## Riscos e decisões abertas

- A PokéAPI não representa diretamente todos os Pokémon capturáveis por versão em uma dimensão única simples. A primeira versão pode usar movepool por `version_group_name` como proxy, mas isso deve ser declarado no dashboard.
- Alguns jogos compartilham `version_group_name`; por exemplo, FireRed e LeafGreen podem ter o mesmo grupo. A UX pode permitir escolher o jogo, mas o cálculo de golpes pode usar o grupo.
- O background visual deve ser original ou gerado; não devemos copiar assets proprietários dos jogos.
- Se no futuro o dashboard virar aplicação web pública, será necessário revisar cache de sprites, CORS, disponibilidade dos assets e direitos de uso.
