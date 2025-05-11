import pytest
import re
from decimal import Decimal, InvalidOperation


def validate_money(value):
    for char in (" ", "_", "-"):
        value = value.replace(char, "")

    value = value.replace(",", ".")

    if value.count(".") > 1:
        raise ValueError("Значение не может содержать более одной точки")

    try:
        validated = Decimal(value) * 100
    except InvalidOperation:
        raise ValueError("Значение должно быть корректным числом")

    if validated < 0:
        raise ValueError("Значение должно быть больше 0")

    return int(validated)


def validate_date(date_str):
    pattern = r"^\d{4}-(?:0?[1-9]|1[0-2])-(?:0?[1-9]|[12][0-9]|3[01])$"
    if not re.match(pattern, date_str):
        raise ValueError("Некорректный формат даты. Используйте формат YYYY-MM-DD")
    return date_str


def test_validate_money_valid_cases():
    assert validate_money("100") == 10000
    assert validate_money("100.50") == 10050
    assert validate_money("100,50") == 10050
    assert validate_money("1 000.50") == 100050
    assert validate_money("1_000.50") == 100050

def test_validate_date_valid_cases():
    assert validate_date("2023-05-01") == "2023-05-01"
    assert validate_date("2023-5-1") == "2023-5-1"
    assert validate_date("2023-12-31") == "2023-12-31"


def test_validate_date_invalid_cases():
    with pytest.raises(ValueError):
        validate_date("05-01-2023")

    with pytest.raises(ValueError):
        validate_date("2023/05/01")

    with pytest.raises(ValueError):
        validate_date("2023-13-01")

    with pytest.raises(ValueError):
        validate_date("2023-12-32")

    with pytest.raises(ValueError):
        validate_date("абв")


def validate_income_source(source):
    valid_sources = ["REVENUE", "OTHER", "GIFT", "DEBT"]
    if source not in valid_sources:
        raise ValueError(f"Недопустимый источник дохода. Допустимые значения: {', '.join(valid_sources)}")
    return source


def test_validate_income_source():
    assert validate_income_source("REVENUE") == "REVENUE"
    assert validate_income_source("OTHER") == "OTHER"
    assert validate_income_source("GIFT") == "GIFT"
    assert validate_income_source("DEBT") == "DEBT"

    with pytest.raises(ValueError):
        validate_income_source("INVALID")


def validate_category(category, valid_categories):
    if category not in valid_categories:
        raise ValueError(f"Недопустимая категория. Допустимые значения: {', '.join(valid_categories)}")
    return category


def test_validate_category():
    valid_categories = ["Продукты", "Транспорт", "Рестораны", "Одежда"]

    assert validate_category("Продукты", valid_categories) == "Продукты"
    assert validate_category("Транспорт", valid_categories) == "Транспорт"

    with pytest.raises(ValueError):
        validate_category("Недвижимость", valid_categories)