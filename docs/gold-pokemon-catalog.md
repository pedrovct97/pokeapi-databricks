# Gold: catálogo de Pokémon em inglês

## Objetivo

`dim_pokemon` é a dimensão Gold de Pokémon para consultas SQL e para a futura API web.
A PokéAPI não disponibiliza `pt-BR` no conjunto ingerido, portanto o contrato publica somente
os textos oficiais em inglês, sem criar traduções artificiais.

## Chaves e granularidade

- Granularidade: uma linha por `pokemon_id`.
- PK lógica: `pokemon_key`.
- Formato determinístico: `pokemon|pokemon_id`.
- Exemplo: `pokemon|25`.

A tabela usa `CLUSTER BY (pokemon_id)`. Como constraints Delta podem ser informativas, a
execução também verifica a unicidade da chave lógica.

A dimensão também expõe arte oficial e sprites provenientes de `silver.pokemon_media`. URLs
ausentes permanecem nulas e nunca são construídas artificialmente.

## Conteúdo

O catálogo reúne cadastro, espécie, descrição, geração, unidades normalizadas, flags, tipos,
estatísticas e habilidades. Tipos e habilidades são arrays de structs ordenados e seus nomes
usam a tradução `en`, com nome técnico como fallback quando o texto localizado estiver ausente.
Movimentos continuam em tabelas relacionais Silver para evitar uma linha Gold excessivamente
grande; a futura API poderá consultá-los sob demanda.

Pokémon sem habilidades informadas pela origem permanecem preservados na Silver, mas não são
publicados neste produto Gold. A regra evita registros incompletos sem inventar ou herdar
habilidades de outra forma.

## Migração do contrato bilíngue legado

A versão `0.8.0` publica primeiro `dim_pokemon` e, após validar o novo objeto, substitui a tabela
legada `pokemon_catalog` por uma view de compatibilidade. Bronze, Silver e `_gold_runs` não são
removidas. Execuções subsequentes usam `MERGE` idempotente na dimensão.

## Qualidade e operação

O job valida nulos técnicos, formato da chave, coleções vazias e duplicatas. `_gold_runs`
registra status, volume, duração, versão e erro. O `MERGE` remove do snapshot registros que
deixaram de existir na Silver.

Ordem de execução após build e deploy:

```powershell
databricks bundle run -t dev -p pokeapi-free silver_transformation
databricks bundle run -t dev -p pokeapi-free gold_transformation
```

Consulta de controle:

```sql
SELECT
  COUNT(*) AS records,
  COUNT(DISTINCT pokemon_id) AS pokemon,
  COUNT(DISTINCT pokemon_key) AS keys
FROM workspace.pokeapi_gold_dev.dim_pokemon;
```
