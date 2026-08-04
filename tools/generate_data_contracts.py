"""Generate YAML data contracts from SQL CREATE TABLE templates.

The generated contracts are documentation-first: each table gets a data dictionary,
SQL template lineage, and baseline quality expectations aligned with the DDL.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

SQL_ROOT = Path("src/pokeapi_lakehouse/sql")
CONTRACT_ROOT = Path("src/pokeapi_lakehouse/contracts")
PROJECT_PACKAGE_ROOT = Path("src/pokeapi_lakehouse")


class NoAliasDumper(yaml.SafeDumper):
    """YAML dumper that keeps contracts readable by avoiding anchors/aliases."""

    def ignore_aliases(self, data: object) -> bool:
        return True


TABLE_ALIASES = {
    ("silver", "table", "runs"): "_silver_runs",
    ("silver", "table", "quarantine"): "_quarantine",
    ("gold", "dim", "pokemon_catalog"): "dim_pokemon",
    ("gold", "dim", "battle_move"): "dim_move",
    ("gold", "fact", "type_matchup_matrix"): "fact_type_matchup",
    ("gold", "fact", "pokemon_battle_profile"): "fact_pokemon_battle_stats",
    ("gold", "fact", "pokemon_matchup"): "fact_pokemon_matchup",
    ("gold", "bridge", "pokemon_move_pool"): "bridge_pokemon_move",
}

GRAIN_OVERRIDES = {
    "bronze_table": "uma linha por recurso retornado pela PokéAPI e hash de payload",
    "ingestion_runs": "uma linha por endpoint processado em uma execução Bronze",
    "ingestion_failures": "uma linha por falha observada durante ingestão Bronze",
    "silver_runs": "uma linha por entidade processada em uma execução Silver",
    "silver_quarantine": "uma linha por registro Bronze rejeitado pelas regras Silver",
    "gold_runs": "uma linha por produto publicado em uma execução Gold",
    "pokemon_matchup": (
        "uma linha direcional por jogo/versão, ruleset, nível de batalha, atacante e defensor"
    ),
    "pokemon_move_pool": "uma linha por movimento disponível para um Pokémon dentro de um ruleset",
    "type_matchup_matrix": "uma linha por combinação ofensiva e defensiva de tipos",
    "pokemon_battle_profile": (
        "uma linha por Pokémon, ruleset e nível de batalha com stats derivados"
    ),
}

PRIMARY_KEYS = {
    "bronze_table": ["endpoint", "resource_id", "payload_sha256"],
    "ingestion_runs": ["run_id", "endpoint"],
    "ingestion_failures": ["run_id", "endpoint", "source_url"],
    "silver_runs": ["silver_run_id", "entity"],
    "silver_quarantine": ["silver_run_id", "entity", "source_url", "source_payload_sha256"],
    "gold_runs": ["gold_run_id", "product"],
    "pokemon": ["pokemon_id"],
    "ability": ["ability_id"],
    "move": ["move_id"],
    "type": ["type_id"],
    "stat": ["stat_id"],
    "pokemon_species": ["species_id"],
    "pokemon_media": ["pokemon_id"],
    "language": ["language_id"],
    "ability_translation": ["ability_id", "language_id"],
    "move_translation": ["move_id", "language_id"],
    "pokemon_species_translation": ["species_id", "language_id"],
    "type_translation": ["type_id", "language_id"],
    "pokemon_type": ["pokemon_id", "type_slot"],
    "pokemon_stat": ["pokemon_id", "stat_id"],
    "pokemon_ability": ["pokemon_id", "ability_id", "ability_slot"],
    "pokemon_move": [
        "pokemon_id",
        "move_id",
        "version_group_name",
        "learn_method_name",
        "level_learned_at",
    ],
    "type_damage_relation": ["source_type_id", "target_type_id"],
    "version_group": ["version_group_id"],
    "game_version": ["version_id"],
    "pokemon_catalog": ["pokemon_key"],
    "battle_move": ["move_key"],
    "ruleset": ["ruleset_key"],
    "type_matchup_matrix": ["attacking_type_id", "defending_type_id"],
    "pokemon_battle_profile": ["pokemon_key", "ruleset_key"],
    "pokemon_move_pool": ["pokemon_move_key"],
    "pokemon_matchup": ["matchup_key"],
}

PARTITION_BY = {
    "pokemon_matchup": ["version_name", "battle_level"],
}

FOREIGN_KEYS = {
    "pokemon": [{"columns": ["species_id"], "references": "silver.pokemon_species.species_id"}],
    "pokemon_media": [{"columns": ["pokemon_id"], "references": "silver.pokemon.pokemon_id"}],
    "pokemon_type": [
        {"columns": ["pokemon_id"], "references": "silver.pokemon.pokemon_id"},
        {"columns": ["type_id"], "references": "silver.type.type_id"},
    ],
    "pokemon_stat": [
        {"columns": ["pokemon_id"], "references": "silver.pokemon.pokemon_id"},
        {"columns": ["stat_id"], "references": "silver.stat.stat_id"},
    ],
    "pokemon_ability": [
        {"columns": ["pokemon_id"], "references": "silver.pokemon.pokemon_id"},
        {"columns": ["ability_id"], "references": "silver.ability.ability_id"},
    ],
    "pokemon_move": [
        {"columns": ["pokemon_id"], "references": "silver.pokemon.pokemon_id"},
        {"columns": ["move_id"], "references": "silver.move.move_id"},
    ],
    "type_damage_relation": [
        {"columns": ["source_type_id"], "references": "silver.type.type_id"},
        {"columns": ["target_type_id"], "references": "silver.type.type_id"},
    ],
}

COMMON_DESCRIPTIONS = {
    "source_url": "URL canônica do recurso Bronze usado como linhagem da transformação",
    "source_payload_sha256": "Hash SHA-256 do payload Bronze usado como versão e linhagem",
    "source_observed_at": "Timestamp horário de Brasília (UTC-3) da observação do dado na origem",
    "silver_transformed_at": "Timestamp horário de Brasília (UTC-3) da transformação Silver",
    "silver_run_id": "UUID da execução Silver responsável pela publicação",
    "gold_transformed_at": "Timestamp horário de Brasília (UTC-3) da publicação Gold",
    "gold_run_id": "UUID da execução Gold responsável pela publicação",
    "run_id": "UUID da execução responsável pelo registro",
    "error_message": "Resumo técnico da falha, sem payload sensível",
}


def _strip_sql_comments(sql: str) -> str:
    return re.sub(r"--.*", "", sql)


def _find_create_body(sql: str) -> str:
    start = sql.index("(") + 1
    depth = 1
    in_quote = False
    idx = start
    while idx < len(sql):
        char = sql[idx]
        if char == "'":
            in_quote = not in_quote
        elif not in_quote:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return sql[start:idx]
        idx += 1
    raise ValueError("CREATE TABLE body not found")


def _split_top_level_commas(body: str) -> list[str]:
    parts: list[str] = []
    start = 0
    paren_depth = 0
    angle_depth = 0
    in_quote = False
    for idx, char in enumerate(body):
        if char == "'":
            in_quote = not in_quote
        elif not in_quote:
            if char == "(":
                paren_depth += 1
            elif char == ")":
                paren_depth -= 1
            elif char == "<":
                angle_depth += 1
            elif char == ">":
                angle_depth -= 1
            elif char == "," and paren_depth == 0 and angle_depth == 0:
                parts.append(body[start:idx].strip())
                start = idx + 1
    tail = body[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def _parse_column(definition: str) -> dict[str, Any] | None:
    normalized = " ".join(definition.strip().split())
    if not normalized:
        return None
    upper = normalized.upper()
    if upper.startswith(("CONSTRAINT ", "PRIMARY KEY", "FOREIGN KEY")):
        return None

    match = re.match(
        r"(?P<name>`?\w+`?)\s+(?P<type>[A-Z]+(?:\([^)]*\))?)"
        r"(?P<rest>.*?)(?:\s+COMMENT\s+'(?P<comment>(?:[^']|'')*)')?$",
        normalized,
        flags=re.IGNORECASE,
    )
    if not match:
        raise ValueError(f"Could not parse column definition: {definition}")

    name = match.group("name").strip("`")
    data_type = match.group("type").upper().replace(" ", "")
    rest = match.group("rest") or ""
    comment = (
        match.group("comment") or COMMON_DESCRIPTIONS.get(name) or _fallback_description(name)
    ).replace("''", "'")
    return {
        "name": name,
        "type": data_type,
        "nullable": "NOT NULL" not in rest.upper(),
        "description": comment,
        "semantic_role": _semantic_role(name, data_type),
    }


def _parse_table_comment(sql: str) -> str:
    matches = re.findall(r"\bCOMMENT\s+'((?:[^']|'')*)'", sql, flags=re.IGNORECASE | re.DOTALL)
    if not matches:
        return "Tabela documentada do PokéAPI Lakehouse."
    return " ".join(matches[-1].replace("''", "'").split())


def _logical_name(create_sql: Path) -> str:
    layer = create_sql.relative_to(SQL_ROOT).parts[0]
    stem = create_sql.stem.removeprefix("create_")
    if stem.startswith(f"{layer}_"):
        return stem.removeprefix(f"{layer}_")
    return stem


def _contract_path(create_sql: Path) -> Path:
    relative_parts = create_sql.relative_to(SQL_ROOT).parts
    layer = relative_parts[0]
    logical = _logical_name(create_sql)
    if layer == "silver":
        return CONTRACT_ROOT / layer / f"{logical}.yaml"
    domain = _contract_domain(layer, logical)
    return CONTRACT_ROOT / layer / domain / f"{logical}.yaml"


def _contract_domain(layer: str, logical: str) -> str:
    if layer == "bronze":
        return "entity" if logical == "table" else "metadata"
    if layer == "silver":
        return "table"
    if layer == "gold":
        if logical == "runs":
            return "metadata"
        if logical == "pokemon_move_pool":
            return "bridge"
        if logical in {"pokemon_battle_profile", "pokemon_matchup", "type_matchup_matrix"}:
            return "fact"
        return "dim"
    raise ValueError(f"camada desconhecida: {layer}")


def _table_name(layer: str, domain: str, logical: str) -> str:
    if layer == "bronze":
        return "<endpoint>" if logical == "table" else f"_{logical}"
    if layer == "silver":
        return TABLE_ALIASES.get((layer, domain, logical), logical)
    if layer == "gold":
        return TABLE_ALIASES.get(
            (layer, domain, logical),
            f"{domain}_{logical}" if domain in {"dim", "fact", "bridge"} else f"_{logical}",
        )
    return logical


def _semantic_role(name: str, data_type: str) -> str:
    if name.endswith("_run_id") or name == "run_id":
        return "audit"
    if name in {"source_url", "source_payload_sha256", "payload_sha256", "source_observed_at"}:
        return "lineage"
    if name.endswith("_key") or name.endswith("_id") or name == "matchup_key":
        return "business_key"
    if name.endswith("_at") or name.endswith("_ms") or name in {"status", "error_message"}:
        return "audit"
    if data_type.startswith(("DECIMAL", "DOUBLE", "BIGINT", "INT")) and not name.endswith("_id"):
        return "metric"
    if data_type == "BOOLEAN":
        return "quality" if name.startswith("is_") else "dimension"
    return "dimension"


def _fallback_description(name: str) -> str:
    readable = name.replace("_", " ")
    if name.endswith("_id"):
        return f"Identificador de {readable.removesuffix(' id')}"
    if name.endswith("_key"):
        return f"Chave canônica de {readable.removesuffix(' key')}"
    if name.endswith("_name"):
        return f"Nome técnico de {readable.removesuffix(' name')}"
    if name.endswith("_count"):
        return f"Quantidade de {readable.removesuffix(' count')}"
    if name.endswith("_at"):
        return f"Timestamp associado a {readable.removesuffix(' at')}"
    return f"Campo {readable} documentado a partir do contrato da tabela"


def _grain(layer: str, domain: str, logical: str, table: str) -> str:
    prefixed = f"{layer}_{logical}"
    if logical in GRAIN_OVERRIDES:
        return GRAIN_OVERRIDES[logical]
    if prefixed in GRAIN_OVERRIDES:
        return GRAIN_OVERRIDES[prefixed]
    if layer == "silver":
        return f"uma linha por tabela normalizada Silver em {table}"
    if domain == "bridge":
        return f"uma linha por relacionamento normalizado em {table}"
    if domain == "translation":
        return f"uma linha por entidade e idioma em {table}"
    if domain == "metadata":
        return f"uma linha de auditoria operacional em {table}"
    if domain == "dim":
        return f"uma linha por entidade conformada em {table}"
    if domain == "fact":
        return f"uma linha por métrica analítica em {table}"
    return f"uma linha por entidade normalizada em {table}"


def _related_templates(create_sql: Path) -> list[str]:
    layer = create_sql.relative_to(SQL_ROOT).parts[0]
    logical = _logical_name(create_sql)
    sql_stem = create_sql.stem.removeprefix("create_")
    candidates = [create_sql]
    for op in ("stage", "merge", "quality"):
        for pattern in (f"{op}_{sql_stem}.sql", f"{op}_{layer}_{logical}.sql"):
            match = next(SQL_ROOT.rglob(pattern), None)
            if match is not None and match not in candidates:
                candidates.append(match)
    return [path.relative_to(PROJECT_PACKAGE_ROOT).as_posix() for path in candidates]


def _expectations(
    logical: str, columns: list[dict[str, Any]], primary_key: list[str]
) -> list[dict[str, Any]]:
    expectations: list[dict[str, Any]] = [
        {
            "name": "schema_columns_match_ddl",
            "type": "expect_table_columns_to_match_ordered_list",
            "columns": [column["name"] for column in columns],
            "severity": "error",
        }
    ]
    if primary_key:
        expectations.append(
            {
                "name": "primary_key_not_null",
                "type": "expect_column_values_to_not_be_null",
                "columns": primary_key,
                "severity": "error",
            }
        )
        expectations.append(
            {
                "name": "primary_key_unique",
                "type": "expect_compound_columns_to_be_unique",
                "columns": primary_key,
                "severity": "error",
            }
        )
    for column in columns:
        if not column["nullable"] and column["name"] not in primary_key:
            expectations.append(
                {
                    "name": f"{column['name']}_not_null",
                    "type": "expect_column_values_to_not_be_null",
                    "column": column["name"],
                    "severity": "error",
                }
            )
    if "payload_sha256" in {column["name"] for column in columns}:
        expectations.append(
            {
                "name": "payload_sha256_length",
                "type": "expect_column_value_lengths_to_equal",
                "column": "payload_sha256",
                "value": 64,
                "severity": "error",
            }
        )
    if logical == "pokemon_matchup":
        expectations.extend(
            [
                {
                    "name": "attacker_win_probability_range",
                    "type": "expect_column_values_to_be_between",
                    "column": "attacker_win_probability",
                    "min_value": 0,
                    "max_value": 1,
                    "severity": "error",
                },
                {
                    "name": "battle_level_supported_values",
                    "type": "expect_column_values_to_be_in_set",
                    "column": "battle_level",
                    "values": [50, 80, 100],
                    "severity": "error",
                },
            ]
        )
    return expectations


def build_contract(create_sql: Path) -> dict[str, Any]:
    sql = _strip_sql_comments(create_sql.read_text(encoding="utf-8"))
    relative_parts = create_sql.relative_to(SQL_ROOT).parts
    layer = relative_parts[0]
    logical = _logical_name(create_sql)
    domain = _contract_domain(layer, logical)
    table = _table_name(layer, domain, logical)
    body = _find_create_body(sql)
    columns = [column for part in _split_top_level_commas(body) if (column := _parse_column(part))]
    primary_key = PRIMARY_KEYS.get(logical, PRIMARY_KEYS.get(f"{layer}_{logical}", []))
    return {
        "version": 1,
        "layer": layer,
        "domain": domain,
        "owner": "pokeapi_lakehouse",
        "logical_name": logical,
        "table": table,
        "description": _parse_table_comment(sql),
        "grain": _grain(layer, domain, logical, table),
        "primary_key": primary_key,
        "foreign_keys": FOREIGN_KEYS.get(logical, []),
        "partition_by": PARTITION_BY.get(logical, []),
        "columns": columns,
        "quality_expectations": _expectations(logical, columns, primary_key),
        "sql_templates": _related_templates(create_sql),
    }


def main() -> None:
    created = []
    for old_path in [
        CONTRACT_ROOT / "bronze" / "bronze_table.yaml",
        CONTRACT_ROOT / "silver" / "pokemon.yaml",
        CONTRACT_ROOT / "gold" / "fact_pokemon_matchup.yaml",
    ]:
        if old_path.exists():
            old_path.unlink()

    for create_sql in sorted(SQL_ROOT.rglob("create_*.sql")):
        contract = build_contract(create_sql)
        path = _contract_path(create_sql)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.dump(
                contract,
                Dumper=NoAliasDumper,
                allow_unicode=True,
                sort_keys=False,
                width=100,
            ),
            encoding="utf-8",
        )
        created.append(path)
    print(f"generated_contracts={len(created)}")


if __name__ == "__main__":
    main()
