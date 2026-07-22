# Gates de entrega

## Gate 0 — Fundação

- Estrutura, comandos e responsabilidades documentados.
- Bundle validado contra o workspace de desenvolvimento.
- Testes, lint e tipos locais aprovados.
- Nenhuma credencial versionada.

## Gate 1 — Bronze

- Contrato da fonte registrado com endpoint, parâmetros e versão observada.
- Payload bruto preservado com `ingested_at` em horário de Brasília (UTC-3), URL, status HTTP e identificador da execução.
- Retry, timeout e falhas parciais tratados.
- Reexecução idempotente e reconciliação de volume demonstradas.
- Tabelas e colunas comentadas no Unity Catalog.

## Gate 2 — Silver

- Granularidade e chaves declaradas por tabela.
- Tipos, nulos, duplicatas, faixas e integridade referencial validados.
- Transformações reproduzíveis exclusivamente a partir da Bronze.
- Reconciliação entre Bronze e Silver documentada.

## Gate 3 — Gold

- Cada tabela ou view possui consumidor e pergunta de negócio explícitos.
- Métricas documentam fórmula, filtros, unidade, janela e fonte.
- Resultados reconciliados com Silver e consultas sem `SELECT *`.

## Gate 4 — Catálogo e operação

- Descrições de schemas, tabelas, views e colunas publicadas.
- Linhagem, frequência, owner, SLA esperado e runbook registrados.
- Alertas distinguem indisponibilidade da API, qualidade e falhas de transformação.

## Gate 5 — Machine learning

- Definição de “batalha” e fonte dos rótulos aprovadas.
- Dataset versionado, baseline simples e divisão sem leakage.
- Métricas, incerteza, vieses e limitações reportados.
- Experimentos e modelos rastreados no MLflow.

