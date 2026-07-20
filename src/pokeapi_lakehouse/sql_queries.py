"""Load reviewed SQL templates shipped inside the ingestion wheel."""

from importlib.resources import files


def sql_query(name: str, *, table: str) -> str:
    """Load a known query and bind its validated table identifier."""
    if not name.replace("_", "").isalnum():
        raise ValueError(f"nome de query inválido: {name}")
    parts = table.split(".")
    if len(parts) != 3 or any(not part.replace("_", "").isalnum() for part in parts):
        raise ValueError(f"tabela inválida: {table}")
    query_path = files("pokeapi_lakehouse").joinpath("sql", f"{name}.sql")
    query = query_path.read_text(encoding="utf-8")
    return query.replace("{{table}}", table)
