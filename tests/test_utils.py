import datetime

import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from src.utils import (read_operations_excel, get_sp500_prices, filter_data_by_date_range,
                       calculate_expenses, calculate_income)


@pytest.fixture
def df():
    """Создаёт тестовый DataFrame с разными типами и категориями."""
    data = {
        "date": pd.to_datetime(
            [
                "2023-01-10",
                "2023-01-15",
                "2023-02-05",
                "2023-02-20",
                "2023-03-01",
                "2023-03-15",
                "2023-04-01",
                "2023-04-15",
                "2023-05-01",
                "2023-05-15",
            ]
        ),
        "amount": [500, 1200, 800, 1500, 2000, 2500, 300, 700, 400, 900],
        "type": [
            "expense",
            "expense",
            "expense",
            "expense",
            "income",
            "income",
            "expense",
            "expense",
            "income",
            "income",
        ],
        "category": [
            "Зарплата",
            "Продукты",
            "Наличные",
            "Переводы",
            "Зарплата",
            "Бонусы",
            "Наличные",
            "Переводы",
            "Зарплата",
            "Бонусы",
        ],
    }
    return pd.DataFrame(data)


@pytest.fixture
def tmp_excel(df, tmp_path):
    """Создаёт временный Excel файл из DataFrame."""
    file_path = tmp_path / "operations.xlsx"
    df.to_excel(file_path, index=False)
    return str(file_path)


def test_read_operations_excel(tmp_excel, df):
    df_read = read_operations_excel(tmp_excel)
    assert isinstance(df_read, pd.DataFrame)
    assert "date" in df_read.columns
    # Проверяем, что даты были преобразованы
    assert pd.api.types.is_datetime64_any_dtype(df_read["date"])


@patch("requests.get")
def test_get_currency_rates(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"rates": {"USD": 1.0, "EUR": 0.85, "RUB": 75.0}}
    mock_resp.raise_for_status = lambda: None
    mock_get.return_value = mock_resp

    rates = get_currency_rates()
    assert rates["USD"] == 1.0
    assert rates["EUR"] == 0.85
    assert rates["RUB"] == 75.0


@patch("requests.get")
def test_get_sp500_prices(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"price": 4200}
    mock_resp.raise_for_status = lambda: None
    mock_get.return_value = mock_resp

    price = get_sp500_prices()
    assert price == 4200


def test_filter_data_by_date_range(df):
    """
    Тест проверяет корректность фильтрации по диапазонам W (неделя),
    M (месяц), Y (год) и ALL (полный набор).
    """
    date_obj = datetime.datetime(2023, 1, 15)  # произвольная дата

    for range_type in ("W", "M", "Y", "ALL"):
        filtered = filter_data_by_date_range(df, date_obj, range_type)

        if range_type == "ALL":
            assert len(filtered) == len(df)
        else:
            # Вычисляем ожидаемый диапазон, используя ту же логику, что и в функции
            if range_type == "W":
                start_date = date_obj - datetime.timedelta(days=date_obj.weekday())
                end_date = start_date + datetime.timedelta(days=6)
            elif range_type == "M":
                start_date = date_obj.replace(day=1)
                next_month = (start_date + datetime.timedelta(days=31)).replace(day=1)
                end_date = next_month - datetime.timedelta(days=1)
            elif range_type == "Y":
                start_date = date_obj.replace(month=1, day=1)
                end_date = date_obj.replace(month=12, day=31)
            else:
                # По умолчанию месяц
                start_date = date_obj.replace(day=1)
                next_month = (start_date + datetime.timedelta(days=31)).replace(day=1)
                end_date = next_month - datetime.timedelta(days=1)

            assert all(filtered["date"] >= start_date), f"Range {range_type} start mismatch"
            assert all(filtered["date"] <= end_date), f"Range {range_type} end mismatch"


@pytest.mark.parametrize(
    "category, expected_key",
    [
        ("Зарплата", "Основные"),
        ("Наличные", "Переводы и наличные"),
        ("Переводы", "Переводы и наличные"),
    ],
)
def test_calculate_expenses(df, category, expected_key):
    df_expense = df[df["type"] == "expense"]
    result = calculate_expenses(df_expense)
    assert "Общая сумма" in result
    assert expected_key in result
    # Проверяем, что ключи присутствуют во вложенных словарях
    if expected_key == "Основные":
        assert isinstance(result["Основные"], dict)
    else:
        assert isinstance(result["Переводы и наличные"], dict)


def test_calculate_income(df):
    df_income = df[df["type"] == "income"]
    result = calculate_income(df_income)
    assert "Общая сумма" in result
    assert "Основные" in result
    assert isinstance(result["Основные"], dict)


if __name__ == "__main__":
    pytest.main()
