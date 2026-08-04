"""Load reviewed SQL templates shipped inside the ingestion wheel."""

from functools import lru_cache
from importlib.resources import files
from importlib.resources.abc import Traversable


def _iter_files(root: Traversable) -> list[Traversable]:
    found: list[Traversable] = []
    for child in root.iterdir():
        if child.is_dir():
            found.extend(_iter_files(child))
        elif child.is_file():
            found.append(child)
    return found


@lru_cache(maxsize=1)
def _query_index() -> dict[str, Traversable]:
    sql_root = files("pokeapi_lakehouse").joinpath("sql")
    index: dict[str, Traversable] = {}
    duplicates: set[str] = set()
    for path in _iter_files(sql_root):
        if path.name in index:
            duplicates.add(path.name)
        index[path.name] = path
    if duplicates:
        duplicate_names = ", ".join(sorted(name.removesuffix(".sql") for name in duplicates))
        raise ValueError(f"queries SQL duplicadas no pacote: {duplicate_names}")
    return index


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
    query_filename = f"{name}.sql"
    query_path = _query_index().get(query_filename)
    if query_path is None:
        raise FileNotFoundError(f"query SQL não encontrada: {name}")
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
