"""Load reviewed SQL templates shipped inside the ingestion wheel."""

from importlib.resources import files


def _validate_identifier(value: str) -> str:
    parts = value.split(".")
    if len(parts) not in (1, 3) or any(
        not part or not part.replace("_", "").isalnum() for part in parts
    ):
        raise ValueError(f"identificador SQL inválido: {value}")
    return value


def sql_query(
    name: str,
    *,
    table: str | None = None,
    identifiers: dict[str, str] | None = None,
    literals: dict[str, str] | None = None,
) -> str:
    """Load a known query and safely bind identifiers and string literals."""
    if not name.replace("_", "").isalnum():
        raise ValueError(f"nome de query inválido: {name}")
    query_path = files("pokeapi_lakehouse").joinpath("sql", f"{name}.sql")
    query = query_path.read_text(encoding="utf-8")
    replacements = dict(identifiers or {})
    if table is not None:
        replacements["table"] = table
    for key, value in replacements.items():
        query = query.replace(f"{{{{{key}}}}}", _validate_identifier(value))
    for key, value in (literals or {}).items():
        query = query.replace(f"{{{{{key}}}}}", "'" + value.replace("'", "''") + "'")
    if "{{" in query or "}}" in query:
        raise ValueError(f"query {name} possui parâmetros não resolvidos")
    return query
