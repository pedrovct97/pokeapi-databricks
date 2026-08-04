"""Timezone utilities for technical lakehouse timestamps."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

BRASILIA_TIMEZONE_ID = "America/Sao_Paulo"
BRASILIA_TZ = timezone(timedelta(hours=-3), name="BRT")


def now_brasilia() -> datetime:
    """Return the current Brasília time using the fixed UTC-3 offset."""
    return datetime.now(BRASILIA_TZ)


def configure_brasilia_timezone(spark: Any) -> None:
    """Configure Spark SQL timestamp rendering/calculation for Brasília time."""
    spark.conf.set("spark.sql.session.timeZone", BRASILIA_TIMEZONE_ID)
