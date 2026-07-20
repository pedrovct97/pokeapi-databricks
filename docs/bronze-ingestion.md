# Fase 1 — Ingestão Bronze

## Escopo e fonte

A ingestão cobre os 48 endpoints de lista/detalhe documentados na API REST v2 da
PokéAPI em `https://pokeapi.co/api/v2`. O GraphQL beta e o sub-recurso de encontros
por Pokémon não fazem parte deste contrato. O registro versionado está em
`src/pokeapi_lakehouse/endpoints.py`.

A fonte é pública, somente leitura e não exige autenticação. Cada endpoint é descoberto
pela paginação `limit`/`offset`; em seguida, cada URL canônica de detalhe é coletada.
O cliente limita a concorrência a oito requisições e aplica timeout e retry com backoff.
Contrato observado em 20 de julho de 2026; mudanças futuras no catálogo oficial devem
ser incorporadas por revisão explícita do registro de endpoints.

## Modelo físico

Cada endpoint materializa uma tabela Delta em
`workspace.pokeapi_bronze_dev.<endpoint_em_snake_case>`. A granularidade é uma versão
observada de um recurso da API. A chave lógica é `(source_url, payload_sha256)`:
reexecuções do mesmo conteúdo não duplicam dados, enquanto mudanças no payload são
preservadas historicamente.

| Coluna | Tipo | Nulável | Semântica |
|---|---|---:|---|
| `endpoint` | string | não | Recurso REST v2 de origem. |
| `resource_id` | long | sim | ID extraído da URL, quando numérico. |
| `resource_name` | string | sim | Campo `name` do payload, quando existente. |
| `source_url` | string | não | URL canônica coletada. |
| `http_status` | int | não | Status HTTP; somente 200 entra na tabela de dados. |
| `payload_json` | string | não | Resposta integral, sem regra de negócio. |
| `payload_sha256` | string | não | Hash do payload usado para versão e idempotência. |
| `source_observed_at` | timestamp | não | Momento UTC em que a resposta foi recebida. |
| `ingested_at` | timestamp | não | Momento UTC de formação do lote Spark. |
| `run_id` | string | não | UUID da execução que observou a versão. |

As tabelas técnicas `_ingestion_runs` e `_ingestion_failures` registram reconciliação
por endpoint e falhas individuais. Não há expectativa de nulidade para metadados
técnicos. `resource_id`, `resource_name` e campos internos do JSON podem ser nulos por
contrato da fonte; sua tipagem e regras de negócio pertencem à Silver.

## Comportamento operacional

- A escrita usa `MERGE` Delta e nunca atualiza ou apaga uma versão Bronze.
- Uma falha de detalhe não descarta respostas válidas já coletadas; ela é registrada e,
  por padrão, faz o job terminar com erro para permitir alerta e retry.
- `max_concurrent_runs: 1` evita duas cargas completas concorrentes.
- Nenhum payload é enviado aos logs; mensagens de erro são truncadas em 1.000 caracteres.
- A frequência ainda não está agendada. O job é manual até volume, duração e cotas do
  Databricks Free Edition serem medidos em uma primeira execução controlada.
- Retenção: histórica por prazo indefinido nesta fase educacional. Uma política de
  expurgo só poderá ser aplicada após aprovação e análise de custo/linhagem.

## Execução e reconciliação

Valide antes de alterar o workspace:

```powershell
databricks bundle validate -t dev -p pokeapi-free
```

Deploy e execução são operações remotas e devem ser autorizados explicitamente:

```powershell
databricks bundle deploy -t dev -p pokeapi-free
databricks bundle run bronze_ingestion -t dev -p pokeapi-free
```

Para uma amostra de baixo custo, altere temporariamente os parâmetros do job ou execute
o entry point com `--endpoints pokemon,type`. Após uma execução, reconcilie:

```sql
SELECT endpoint, status, discovered_count, fetched_count, inserted_count, failed_count
FROM workspace.pokeapi_bronze_dev._ingestion_runs
ORDER BY finished_at DESC;

SELECT endpoint, COUNT(*) AS versions, COUNT(DISTINCT source_url) AS resources
FROM workspace.pokeapi_bronze_dev.pokemon
GROUP BY endpoint;

SELECT
  SUM(CASE WHEN source_url IS NULL THEN 1 ELSE 0 END) AS null_source_url,
  SUM(CASE WHEN payload_json IS NULL THEN 1 ELSE 0 END) AS null_payload,
  SUM(CASE WHEN run_id IS NULL THEN 1 ELSE 0 END) AS null_run_id
FROM workspace.pokeapi_bronze_dev.pokemon;
```

Uma segunda execução sem mudança na fonte deve apresentar `inserted_count = 0` para os
recursos inalterados. Esse é o teste operacional de idempotência do Gate 1.

## Gate e limitações

O Gate 1 só estará concluído depois de uma execução remota comprovar: criação das 48
tabelas, ausência de nulos técnicos, zero duplicatas pela chave lógica, reconciliação
entre descobertos/coletados/falhos e idempotência em uma segunda execução. A PokéAPI não
publica uma versão formal do dataset; por isso, URL, horário e hash são a versão observada.
