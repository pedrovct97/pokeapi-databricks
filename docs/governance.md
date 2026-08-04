# Governança e documentação de dados

## Padrão obrigatório por objeto

Cada tabela ou view deverá documentar:

- nome totalmente qualificado;
- camada, owner e propósito;
- granularidade e chave primária lógica;
- origem e frequência de atualização;
- timezone e política de retenção;
- descrição, tipo, unidade e nulabilidade de cada coluna;
- regras de qualidade e comportamento em falhas;
- consumidores conhecidos e limitações.

## Convenções

- Catálogo de desenvolvimento: `workspace`.
- Schemas: `pokeapi_<camada>_dev`.
- Tabelas e colunas: `snake_case`, em inglês para acompanhar o contrato da API.
- Timestamps técnicos: horário de Brasília (UTC-3) e sufixo `_at`.
- Datas: sufixo `_date`.
- Identificadores: sufixo `_id`.
- Views: prefixo `vw_` somente quando necessário para distingui-las de tabelas publicadas.

## Contratos YAML e comentários no Unity Catalog

Os contratos navegáveis ficam em `src/pokeapi_lakehouse/contracts`, um YAML por tabela/produto. Eles
contêm descrição da tabela, granularidade, chaves, partições, dicionário de colunas e expectations de
qualidade. O gerador `tools/generate_data_contracts.py` mantém esses YAMLs alinhados aos DDLs
`create_*.sql`.

Comentários em tabelas já existentes no Unity Catalog não são reaplicados por
`CREATE TABLE IF NOT EXISTS`. Para sincronizar os comentários do YAML com o Catalog Explorer, use o
entrypoint `metadata_sync`, que executa de forma idempotente:

```sql
COMMENT ON TABLE ... IS '...';
ALTER TABLE ... ALTER COLUMN ... COMMENT '...';
```

Execute primeiro em dry-run para revisar os comandos gerados. A execução sem dry-run altera metadados
remotos e exige autorização explícita.

## Segurança

A fonte é pública, mas logs não devem registrar tokens OAuth, headers de autenticação ou conteúdo de arquivos locais. O perfil `pokeapi-free` é configuração da máquina e não faz parte do projeto.

