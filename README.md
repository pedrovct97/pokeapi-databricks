# PokéAPI Lakehouse no Databricks

Projeto educacional de engenharia de dados e machine learning construído do zero no Databricks Free Edition. A implementação segue gates: uma camada só começa quando a anterior estiver documentada, testada e validada.

## Estado atual

**Fase 1 — Bronze em implementação.** O job genérico cobre os 48 endpoints REST v2 da
PokéAPI e materializa uma tabela Delta por recurso. A validação e a execução remota ainda
precisam ser realizadas antes de considerar o Gate 1 concluído.

## Arquitetura planejada

| Camada | Responsabilidade | Gate de saída |
|---|---|---|
| Bronze | Preservar respostas brutas da PokéAPI e metadados de ingestão | Schema, volume, idempotência e rastreabilidade validados |
| Silver | Normalizar entidades e aplicar regras de qualidade | Chaves, nulos, duplicatas e integridade referencial validados |
| Gold | Publicar métricas e datasets orientados a consumo | Definições de métricas e reconciliação com Silver validadas |
| ML | Simular/analisar batalhas com baseline reproduzível | Ausência de leakage, avaliação e limitações documentadas |

Detalhes: [arquitetura](docs/architecture.md), [governança](docs/governance.md) e [processo por gates](docs/delivery-gates.md).

Contrato e runbook da ingestão: [Fase 1 — Bronze](docs/bronze-ingestion.md).
As DDLs, `MERGE` e verificações de qualidade ficam em
[`src/pokeapi_lakehouse/sql`](src/pokeapi_lakehouse/sql/), separadas do cliente HTTP Python.

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
