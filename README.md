# PokéAPI Lakehouse no Databricks

Projeto educacional de engenharia de dados e machine learning construído do zero no Databricks Free Edition. A implementação segue gates: uma camada só começa quando a anterior estiver documentada, testada e validada.

## Estado atual

Bronze e Silver validadas no Databricks. O primeiro produto Gold é o catálogo de Pokémon em
inglês, idioma disponibilizado pela fonte para o conteúdo consumido.

## Arquitetura planejada

| Camada | Responsabilidade | Gate de saída |
|---|---|---|
| Bronze | Preservar respostas brutas da PokéAPI e metadados de ingestão | Schema, volume, idempotência e rastreabilidade validados |
| Silver | Normalizar entidades e aplicar regras de qualidade | Chaves, nulos, duplicatas e integridade referencial validados |
| Gold | Publicar métricas e datasets orientados a consumo | Definições de métricas e reconciliação com Silver validadas |
| ML | Simular/analisar batalhas com baseline reproduzível | Ausência de leakage, avaliação e limitações documentadas |

Detalhes: [arquitetura](docs/architecture.md), [governança](docs/governance.md) e [processo por gates](docs/delivery-gates.md).

Contrato e runbook da ingestão: [Fase 1 — Bronze](docs/bronze-ingestion.md).
As DDLs, stages, `MERGE`, inserts e verificações de qualidade ficam em
[`src/pokeapi_lakehouse/sql`](src/pokeapi_lakehouse/sql/), separadas do cliente HTTP Python e
organizadas por camada e operação:

```txt
sql/bronze/{create,insert,merge,quality}/
sql/silver/{create,insert,merge,quality,stage}/
sql/gold/{create,merge,quality,stage}/
```

O loader `sql_query(...)` procura templates recursivamente dentro desse diretório, mantendo os
nomes lógicos usados pelos orquestradores. Os contratos YAML versionados ficam em
[`src/pokeapi_lakehouse/contracts`](src/pokeapi_lakehouse/contracts/), separados por contrato lógico
de tabela/produto: Silver fica plano; Bronze e Gold usam domínios de contrato quando isso ajuda a
documentação. Cada YAML funciona como
data dictionary navegável: descreve tabela, granularidade, chaves, partições, colunas, tipos,
nullability, comentários e expectations de qualidade. A pasta `contracts/great_expectations/`
registra expectativas locais de qualidade usadas no CI.

Silver SQL-first: [domínio de Pokémon e batalha](docs/silver-pilot.md).

Gold SQL-first: [catálogo de Pokémon em inglês](docs/gold-pokemon-catalog.md).

Fundação para batalhas: [matriz, perfis e movimentos](docs/battle-foundation.md).

## Ambientes e isolamento

O target `dev` usa o perfil OAuth local `pokeapi-free`, o catálogo `workspace` e schemas exclusivos:

- `workspace.pokeapi_bronze_dev`
- `workspace.pokeapi_silver_dev`
- `workspace.pokeapi_gold_dev`

O catálogo legado `pokemon_lakehouse` não é alterado.

## Comandos locais

```powershell
python -m pip install -e ".[dev]"
python -m ruff check .
python -m mypy src
python -m pytest
python -m pip wheel . --no-deps --no-build-isolation --no-cache-dir --wheel-dir .artifacts
databricks bundle validate -t dev -p pokeapi-free
```

Deploy e execução remota exigem autorização explícita.

Para sincronizar comentários de tabelas/colunas no Unity Catalog a partir dos contratos YAML, use o
entrypoint `metadata_sync`. Primeiro gere um dry-run no job ou localmente para revisar os SQLs; a
execução sem `--dry-run` altera metadados no Databricks e exige autorização explícita.

## Ferramentas de AI do projeto

A pasta `.hermes/` concentra configurações, hooks e skills de apoio ao
desenvolvimento com Hermes e Databricks. Ela deve ser preservada como material ativo
do projeto.

O snapshot bruto `.databricks-ai-tools/` não é necessário no repositório quando as
skills úteis já estão organizadas em `.hermes/`; por isso ele fica ignorado para evitar
duplicidade e ruído em lint/testes.
