import pytest

from src.domain.configurations import services as configurations_services


@pytest.mark.parametrize(
    "data,expected_result",
    [
        ("Food,Taxi", "Food,Taxi"),
        ("Food,,,Taxi", "Food,Taxi"),
        ("  Food,  Taxi ", "Food,Taxi"),
        ("  Se pa rated,  Taxi ", "Se pa rated,Taxi"),
    ],
)
def test_validate_income_sources_input(data, expected_result):
    result = configurations_services.clean_sources_input(data)
    assert result == expected_result


@pytest.mark.parametrize(
    "data,expected_result",
    [
        ("1,2,3", "1,2,3"),
        ("1,,,,2,3", "1,2,3"),
        ("  1,  2  , 3 ", "1,2,3"),
    ],
)
async def test_validate_ignore_categories_input(data, expected_result):
    result = await configurations_services.clean_ignore_categories(data)
    assert result == expected_result
