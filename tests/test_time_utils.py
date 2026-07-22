from datetime import timedelta

from pokeapi_lakehouse.time_utils import BRASILIA_TIMEZONE_ID, now_brasilia


def test_now_brasilia_uses_utc_minus_three_offset() -> None:
    current = now_brasilia()

    assert current.tzinfo is not None
    assert current.utcoffset() == timedelta(hours=-3)


def test_brasilia_timezone_id_matches_spark_region() -> None:
    assert BRASILIA_TIMEZONE_ID == "America/Sao_Paulo"
