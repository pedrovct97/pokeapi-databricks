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
- Timestamps técnicos: UTC e sufixo `_at`.
- Datas: sufixo `_date`.
- Identificadores: sufixo `_id`.
- Views: prefixo `vw_` somente quando necessário para distingui-las de tabelas publicadas.

## Segurança

A fonte é pública, mas logs não devem registrar tokens OAuth, headers de autenticação ou conteúdo de arquivos locais. O perfil `pokeapi-free` é configuração da máquina e não faz parte do projeto.

