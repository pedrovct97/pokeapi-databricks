# Arquitetura

## Objetivo

Construir um Lakehouse reproduzível para dados públicos da PokéAPI, com ingestão observável, transformação por responsabilidades e produtos analíticos aptos a sustentar experimentos futuros de batalhas Pokémon.

## Fluxo planejado

`PokéAPI → Bronze → Silver → Gold → Features/ML`

- **PokéAPI:** fronteira externa sujeita a indisponibilidade, rate limiting e mudança de contrato.
- **Bronze:** preserva o payload recebido sem aplicar regras de negócio.
- **Silver:** converte payloads em entidades tipadas e relacionamentos explícitos.
- **Gold:** consolida métricas e datasets por caso de uso.
- **ML:** só consome datasets Gold versionados e divide treino/validação/teste sem vazamento.

## Decisões da fundação

1. Databricks Declarative Automation Bundles descreve recursos e deployments como código.
2. Unity Catalog governa schemas, tabelas, views, comentários e linhagem.
3. Cada camada possui schema próprio para impedir acoplamento e acesso acidental.
4. O ambiente `dev` usa schemas sufixados por `_dev` e não toca no catálogo legado.
5. Código compartilhado fica em `src/`; notebooks futuros devem apenas adaptar parâmetros e chamar módulos.
6. Credenciais permanecem no perfil OAuth local e nunca entram no Git.

## Organização dos artefatos SQL e contratos

As transformações continuam SQL-first, mas os templates não ficam mais em um diretório plano. O
pacote organiza `src/pokeapi_lakehouse/sql` por camada e operação para separar claramente DDL,
staging, merges, inserts e quality checks:

```txt
sql/bronze/create/   # DDLs Bronze
sql/bronze/insert/   # inserts auxiliares Bronze
sql/bronze/merge/    # MERGEs Bronze
sql/bronze/quality/  # quality checks Bronze
sql/silver/create/   # DDLs Silver
sql/silver/insert/   # inserts auxiliares Silver
sql/silver/stage/    # staging views Silver
sql/silver/merge/    # MERGEs Silver
sql/silver/quality/  # quality checks Silver
sql/gold/create/     # DDLs Gold
sql/gold/stage/      # staging views Gold
sql/gold/merge/      # MERGEs Gold
sql/gold/quality/    # quality checks Gold
```

Os orquestradores Python continuam chamando `sql_query("create_gold_pokemon_matchup", ...)` por nome
lógico. O loader resolve esse nome recursivamente dentro do pacote, evitando endereços hardcoded nas
funções de Bronze, Silver e Gold. O `pyproject.toml` empacota `sql/**/*.sql`, então o wheel do
Databricks contém os templates mesmo em subpastas.

Contratos YAML versionados ficam em `src/pokeapi_lakehouse/contracts`, separados pela semântica da
tabela/produto, não pela operação SQL. Silver fica em uma pasta única de contratos; Bronze e Gold
usam domínios lógicos quando ajudam a documentação. Cada tabela/produto com `create_*.sql` possui um
YAML próprio que serve como data dictionary navegável: descrição da tabela, granularidade, chaves,
partições, dicionário de colunas com tipo/nullability/comentário/papel semântico, SQLs associados e
expectations de qualidade. O gerador `tools/generate_data_contracts.py` deriva esses contratos dos
DDLs para manter o YAML alinhado com as colunas publicadas. Contratos locais de Great Expectations ficam em
`contracts/great_expectations/` e complementam, sem substituir, as queries `quality_*.sql` executadas
no Databricks.

O entrypoint `metadata_sync` lê esses contratos empacotados no wheel e sincroniza comentários no
Unity Catalog. Ele é separado das cargas Bronze/Silver/Gold para permitir execução sob demanda e
evitar alterações remotas de metadados sem uma decisão explícita.

## Restrições conhecidas

- Databricks Free Edition oferece somente compute serverless e possui cotas.
- A PokéAPI não fornece eventos reais de batalhas; o objetivo e a fonte do dataset de ML deverão ser definidos antes da Fase 5.
- Deploy, criação de schemas e execução de pipelines são mudanças remotas e exigem autorização explícita.

