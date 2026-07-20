"""Configuração validada e independente do runtime Databricks."""

from dataclasses import dataclass


def _validate_identifier(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized or not normalized.replace("_", "").isalnum():
        raise ValueError(f"{field_name} deve conter apenas letras, números e underscore")
    return normalized


@dataclass(frozen=True)
class LakehouseConfig:
    """Nomes dos objetos Unity Catalog usados por uma execução do pipeline."""

    catalog: str
    bronze_schema: str
    silver_schema: str
    gold_schema: str

    def __post_init__(self) -> None:
        for field_name in ("catalog", "bronze_schema", "silver_schema", "gold_schema"):
            object.__setattr__(
                self,
                field_name,
                _validate_identifier(getattr(self, field_name), field_name),
            )

    def qualified_schema(self, layer: str) -> str:
        """Retorna o schema qualificado para uma camada conhecida."""
        schemas = {
            "bronze": self.bronze_schema,
            "silver": self.silver_schema,
            "gold": self.gold_schema,
        }
        try:
            schema = schemas[layer.lower()]
        except KeyError as exc:
            raise ValueError(f"camada desconhecida: {layer}") from exc
        return f"{self.catalog}.{schema}"
