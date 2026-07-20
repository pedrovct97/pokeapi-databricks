# Fase 2 — Silver do domínio de batalhas

## Objetivo

Aplicar o padrão SQL-first aprovado no piloto às entidades e relações necessárias para
análises e futuras simulações de batalha. Toda transformação lê exclusivamente tabelas Bronze, seleciona a versão
mais recente de cada `source_url`, aplica um contrato JSON explícito e publica tabelas
Delta tipadas.

## Objetos

### `workspace.pokeapi_silver_dev.pokemon`

- Granularidade: uma linha por `pokemon_id` na fotografia atual.
- Chave lógica: `pokemon_id`.
- Unidades originais: `height_dm` em decímetros e `weight_hg` em hectogramas.
- Unidades derivadas: `height_m = height_dm / 10` e `weight_kg = weight_hg / 10`.
- Nuláveis por contrato: `base_experience`, `sort_order`, `species_id` e `species_name`.

### `workspace.pokeapi_silver_dev.move`

- Granularidade: uma linha por `move_id` na fotografia atual.
- Chave lógica: `move_id`.
- `accuracy_pct` é nula quando o movimento ignora o teste de precisão.
- `power` é nulo para movimentos sem dano direto.
- `effect_chance_pct` pode ser nula quando não há efeito secundário probabilístico.
- Tipo, classe de dano e geração são preservados como ID e nome para leitura e futura
  integridade referencial.

Ambas mantêm `source_url`, `source_payload_sha256`, `source_observed_at`,
`silver_transformed_at` e `silver_run_id` para linhagem completa.

### Dimensões adicionais

- `type`: tipos elementais, geração e classe de dano.
- `stat`: definição das estatísticas e indicação de uso em batalha.
- `ability`: habilidades, geração e indicador de série principal.
- `pokemon_species`: espécie, geração, crescimento, habitat, cor, formato e atributos
  biológicos relevantes.

### Relações

- `pokemon_type`: uma linha por Pokémon e slot de tipo.
- `pokemon_stat`: uma linha por Pokémon e estatística, com `base_stat` e `effort`.
- `pokemon_ability`: uma linha por Pokémon, habilidade e slot.
- `pokemon_move`: uma linha por Pokémon, movimento, versão, método e nível de aprendizado.
- `type_damage_relation`: exceções à efetividade neutra. Armazena multiplicadores `0.0`,
  `0.5` e `2.0`; a ausência de relação significa `1.0`.

Depois da publicação completa, 14 regras SQL verificam integridade referencial entre
dimensões e relações, presença de tipos/estatísticas e os seis stats esperados para
Pokémon padrão. O resultado aparece em `_silver_runs` como
`_referential_integrity`.

## Qualidade e falhas

Antes do `MERGE`, registros com JSON incompatível, chave nula, chave duplicada ou faixa
inválida são direcionados para `workspace.pokeapi_silver_dev._quarantine`. Eles não são
publicados silenciosamente.

`_silver_runs` registra uma linha por entidade e execução, começando em `RUNNING` e
terminando em `SUCCESS` ou `FAILED`, com:

- `source_count`;
- `valid_count`;
- `quarantined_count`;
- `inserted_count`;
- `published_count`;
- duração e versão do transformador.

O job falha quando há nulos técnicos, duplicatas, faixas inválidas ou quando
`published_count <> valid_count`.

## Queries versionadas

As queries ficam em `src/pokeapi_lakehouse/sql/`:

- `stage_silver_pokemon.sql` e `stage_silver_move.sql`;
- `create_silver_pokemon.sql` e `create_silver_move.sql`;
- `merge_silver_pokemon.sql` e `merge_silver_move.sql`;
- `quality_silver_pokemon.sql` e `quality_silver_move.sql`;
- queries técnicas de `_silver_runs` e `_quarantine`.

## Execução

Gere a versão que evita cache serverless de pacotes anteriores:

```powershell
python -m pip wheel . --no-deps --no-build-isolation --no-cache-dir --wheel-dir .artifacts
databricks bundle validate -t dev -p pokeapi-free
databricks bundle deploy -t dev -p pokeapi-free
databricks bundle run -t dev -p pokeapi-free silver_transformation
```

## Validação

```sql
SELECT *
FROM workspace.pokeapi_silver_dev._silver_runs
ORDER BY started_at DESC;

SELECT entity, validation_errors, COUNT(*) AS rejected_count
FROM workspace.pokeapi_silver_dev._quarantine
GROUP BY entity, validation_errors
ORDER BY entity, rejected_count DESC;

SELECT pokemon_id, pokemon_name, height_m, weight_kg, species_name
FROM workspace.pokeapi_silver_dev.pokemon
ORDER BY pokemon_id
LIMIT 20;

SELECT move_id, move_name, power, accuracy_pct, damage_class_name, type_name
FROM workspace.pokeapi_silver_dev.move
ORDER BY move_id
LIMIT 20;
```

O domínio é aprovado quando as 11 entidades e `_referential_integrity` terminam em
`SUCCESS`, quarentena é zero ou explicada, as contagens reconciliam com a versão atual da Bronze e uma segunda
execução apresenta `inserted_count = 0`.
