# CI/CD do PokéAPI Lakehouse

## Objetivo

A esteira impede que alterações com falhas conhecidas cheguem ao Databricks e mantém o
deploy reproduzível. Os testes locais não chamam a PokéAPI nem alteram tabelas remotas.

## Fluxo

1. Pull requests e pushes executam formatação, lint, mypy, Bandit, auditoria de
   dependências, pytest, contratos Great Expectations, cobertura mínima de 40% e build
   do wheel.
2. O CodeQL procura vulnerabilidades Python em pull requests, na `master` e semanalmente.
3. Um push aprovado na `master` dispara o CD somente depois que o workflow `CI` termina
   com sucesso.
4. O job de CD espera a aprovação do ambiente GitHub `development`, valida o bundle e
   então executa `databricks bundle deploy -t dev`.

O workflow de CD não executa os jobs de dados automaticamente. Isso separa a publicação
de código da ingestão e evita consumo ou alteração de dados sem uma decisão explícita.

## Configuração no GitHub

Crie um Environment chamado `development` em **Settings > Environments**:

- adicione ao menos um *required reviewer*;
- restrinja a implantação à branch `master`;
- crie a variável `DATABRICKS_HOST` com a URL do workspace;
- crie o secret `DATABRICKS_TOKEN` com um token de curta duração e menor privilégio.

Para uso profissional, substitua o token por OAuth de uma service principal. Nunca
adicione credenciais ao repositório, aos arquivos do bundle ou aos logs.

Em **Settings > Branches**, proteja a `master` e torne obrigatórios:

- `CI / Qualidade, testes e segurança`;
- `CodeQL / Análise estática Python`;
- ao menos uma revisão de pull request;
- resolução de todas as conversas antes do merge.

## Contrato Great Expectations

`tests/data_quality/test_bronze_expectations.py` cria uma amostra determinística usando
a mesma conversão da ingestão Bronze. O contrato executável continua no teste e é documentado em
`src/pokeapi_lakehouse/contracts/great_expectations/bronze_table.yaml`. Ele verifica:

- conjunto exato de colunas;
- unicidade de endpoint, identificador e hash do payload;
- campos técnicos obrigatórios;
- origem HTTPS na PokéAPI;
- resposta HTTP bem-sucedida;
- tamanho do SHA-256;
- faixas válidas para tentativas e tamanho da resposta.

As consultas `quality_*.sql` continuam sendo a validação autoritativa no Databricks.
Great Expectations antecipa regressões no CI; ele não substitui reconciliação,
integridade referencial ou validação das tabelas reais.

## Layout de SQL e contratos empacotados

Os SQLs do pacote são empacotados recursivamente via `sql/**/*.sql` e ficam separados por
camada/operação:

```txt
src/pokeapi_lakehouse/sql/bronze/{create,insert,merge,quality}/
src/pokeapi_lakehouse/sql/silver/{create,insert,merge,quality,stage}/
src/pokeapi_lakehouse/sql/gold/{create,merge,quality,stage}/
```

`tests/test_sql_layout.py` impede regressão para diretório plano, valida que `sql_query(...)`
resolve templates em subpastas, exige um YAML por tabela/produto com `create_*.sql`, valida que cada
contrato é um data dictionary completo e confirma que `contracts/**/*.yaml` também entra no pacote.
O teste compara os YAMLs com `tools/generate_data_contracts.py`; se um DDL mudar, regenere os
contratos antes de fechar a alteração.

O job `metadata_sync` do bundle usa esses contratos para aplicar comentários em tabelas e colunas no
Unity Catalog. Ele é validado por `tests/test_uc_metadata.py` e `tests/test_jobs.py`, mas sua execução
remota altera metadados e deve ser feita manualmente/aprovada fora do CI automático.

## Como reproduzir localmente

```powershell
python -m pip install -e ".[dev]"
python -m ruff format --check src tests notebooks
python -m ruff check src tests notebooks
python -m mypy src
python -m bandit -q -r src -lll
python -m pip_audit .
python -m pytest --cov=pokeapi_lakehouse --cov-report=term-missing --cov-fail-under=40
python -m pip wheel . --no-deps --no-build-isolation --wheel-dir .artifacts
```

O `pyproject.toml` exclui `.hermes/`, `.databricks-ai-tools/` e `.artifacts/` do
Ruff. A pasta `.hermes/` guarda skills, hooks e configurações de apoio ao
desenvolvimento com AI/Databricks; ela não deve ser analisada como código Python do
produto. A pasta `.databricks-ai-tools/` é apenas um snapshot bruto duplicado das
skills Databricks e deve permanecer fora do versionamento ativo.

O comando abaixo exige autenticação e apenas valida a configuração:

```powershell
databricks bundle validate -t dev -p pokeapi-free
```

Deploy e execução de jobs remotos continuam exigindo autorização explícita.
