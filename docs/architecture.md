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

## Restrições conhecidas

- Databricks Free Edition oferece somente compute serverless e possui cotas.
- A PokéAPI não fornece eventos reais de batalhas; o objetivo e a fonte do dataset de ML deverão ser definidos antes da Fase 5.
- Deploy, criação de schemas e execução de pipelines são mudanças remotas e exigem autorização explícita.

