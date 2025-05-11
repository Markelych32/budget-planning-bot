import pytest
import os


def test_env_file_exists():
    assert os.path.exists("../../../.env-example"), "Файл .env-example должен существовать"


def test_env_example_format():
    with open("../../../.env-example", "r") as f:
        content = f.read()

    assert "TELEGRAM_BOT_API_KEY" in content
    assert "DATABASE_NAME" in content
    assert "DB_USER" in content
    assert "DB_PASSWORD" in content


def test_docker_compose_exists():
    assert os.path.exists("../../../docker-compose.yaml"), "Файл docker-compose.yaml должен существовать"


def test_docker_compose_structure():
    with open("../../../docker-compose.yaml", "r") as f:
        content = f.read()

    assert "postgres_db" in content
    assert "backend" in content
    assert "fullstack" in content

def test_readme_content():
    assert os.path.exists("../../../README.md"), "Файл README.md должен существовать"

    with open("../../../README.md", "r") as f:
        content = f.read()

    assert "Family Budget" in content
    assert "docker compose" in content.lower() or "docker-compose" in content.lower()

@pytest.fixture
def sample_costs():
    return [
        {"id": 1, "name": "Продукты", "value": 1200, "date": "2023-05-01"},
        {"id": 2, "name": "Транспорт", "value": 500, "date": "2023-05-02"},
        {"id": 3, "name": "Рестораны", "value": 2500, "date": "2023-05-03"}
    ]


@pytest.fixture
def sample_incomes():
    return [
        {"id": 1, "name": "Зарплата", "value": 15000, "date": "2023-05-01"},
        {"id": 2, "name": "Подработка", "value": 5000, "date": "2023-05-15"}
    ]


def test_calculate_total_costs(sample_costs):
    total = sum(cost["value"] for cost in sample_costs)
    assert total == 4200


def test_calculate_balance(sample_costs, sample_incomes):
    total_costs = sum(cost["value"] for cost in sample_costs)
    total_incomes = sum(income["value"] for income in sample_incomes)
    balance = total_incomes - total_costs

    assert balance == 15800
    assert balance > 0


def test_daily_costs_report(sample_costs):
    daily_costs = {}
    for cost in sample_costs:
        date = cost["date"]
        if date not in daily_costs:
            daily_costs[date] = 0
        daily_costs[date] += cost["value"]

    assert daily_costs["2023-05-01"] == 1200
    assert daily_costs["2023-05-02"] == 500
    assert daily_costs["2023-05-03"] == 2500
    assert len(daily_costs) == 3


def test_cost_category_filtering():
    costs = [
        {"id": 1, "name": "Хлеб", "category": "Продукты", "value": 100},
        {"id": 2, "name": "Молоко", "category": "Продукты", "value": 200},
        {"id": 3, "name": "Автобус", "category": "Транспорт", "value": 50},
        {"id": 4, "name": "Метро", "category": "Транспорт", "value": 60},
        {"id": 5, "name": "Кафе", "category": "Рестораны", "value": 500}
    ]

    products = [cost for cost in costs if cost["category"] == "Продукты"]
    assert len(products) == 2
    assert sum(cost["value"] for cost in products) == 300

    transport = [cost for cost in costs if cost["category"] == "Транспорт"]
    assert len(transport) == 2
    assert sum(cost["value"] for cost in transport) == 110


def test_currency_conversion():
    exchange_rates = {"USD": 1.0, "EUR": 0.85, "RUB": 75.0}

    usd_amount = 100

    eur_amount = usd_amount * exchange_rates["USD"] / exchange_rates["EUR"]
    rub_amount = usd_amount * exchange_rates["USD"] / exchange_rates["RUB"]

    assert round(eur_amount, 2) == 117.65
    assert round(rub_amount, 2) == 1.33

    assert round(eur_amount * exchange_rates["EUR"] / exchange_rates["USD"], 2) == 100.00
    assert round(rub_amount * exchange_rates["RUB"] / exchange_rates["USD"], 2) == 100.00