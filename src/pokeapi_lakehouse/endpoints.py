"""Versioned registry of the PokéAPI REST v2 resources ingested into Bronze."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Endpoint:
    """A list/detail endpoint exposed by PokéAPI REST v2."""

    name: str
    group: str

    @property
    def table_name(self) -> str:
        return self.name.replace("-", "_")


_ENDPOINT_GROUPS: dict[str, tuple[str, ...]] = {
    "berries": ("berry", "berry-firmness", "berry-flavor"),
    "contests": ("contest-type", "contest-effect", "super-contest-effect"),
    "encounters": (
        "encounter-method",
        "encounter-condition",
        "encounter-condition-value",
    ),
    "evolution": ("evolution-chain", "evolution-trigger"),
    "games": ("generation", "pokedex", "version", "version-group"),
    "items": (
        "item",
        "item-attribute",
        "item-category",
        "item-fling-effect",
        "item-pocket",
    ),
    "locations": ("location", "location-area", "pal-park-area", "region"),
    "machines": ("machine",),
    "moves": (
        "move",
        "move-ailment",
        "move-battle-style",
        "move-category",
        "move-damage-class",
        "move-learn-method",
        "move-target",
    ),
    "pokemon": (
        "ability",
        "characteristic",
        "egg-group",
        "gender",
        "growth-rate",
        "nature",
        "pokeathlon-stat",
        "pokemon",
        "pokemon-color",
        "pokemon-form",
        "pokemon-habitat",
        "pokemon-shape",
        "pokemon-species",
        "stat",
        "type",
    ),
    "utility": ("language",),
}

ENDPOINTS: tuple[Endpoint, ...] = tuple(
    Endpoint(name=name, group=group) for group, names in _ENDPOINT_GROUPS.items() for name in names
)


def select_endpoints(names: str | None = None) -> tuple[Endpoint, ...]:
    """Return all endpoints or a validated comma-separated subset."""
    if names is None or not names.strip() or names.strip().lower() == "all":
        return ENDPOINTS

    requested = {name.strip().lower() for name in names.split(",") if name.strip()}
    known = {endpoint.name: endpoint for endpoint in ENDPOINTS}
    unknown = requested - known.keys()
    if unknown:
        raise ValueError(f"endpoints desconhecidos: {', '.join(sorted(unknown))}")
    return tuple(endpoint for endpoint in ENDPOINTS if endpoint.name in requested)
