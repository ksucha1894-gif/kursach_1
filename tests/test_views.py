import pytest
from unittest.mock import patch
import pandas as pd
from datetime import datetime

import src.views


@pytest.fixture
def get_sample_data():
    """
    Фикстура для предоставления образца данных (не используется напрямую в тесте).
    """
    return {
        "some": "data"
    }


@pytest.mark.parametrize("date_str, period, mock_returns, expected_keys", [
    (
            "2023-03-15",
            "M",
            {
                "expenses": {"Общая сумма": 200},
                "income": {"Общая сумма": 100},
                "rates": {"USD": 1.0},
                "sp500": 4200
            },
            ["Дата", "Диапазон", "Расходы", "Поступления", "Курсы валют", "Цена S&P 500"]
    ),
    (
            "2023-04-01",
            "Y",
            {
                "expenses": {"Общая сумма": 500},
                "income": {"Общая сумма": 300},
                "rates": {"USD": 0.75},
                "sp500": 4300
            },
            ["Дата", "Диапазон", "Расходы", "Поступления", "Курсы валют", "Цена S&P 500"]
    ),
])
def test_financial_data(get_sample_data, date_str, period, mock_returns, expected_keys):
    """
    Тестирует функцию get_financial_data, мокая все внешние зависимости.
    """
    sample_df = pd.DataFrame({
        'column1': [1, 2],
        'column2': ['a', 'b']
    })

    # Парсим дату, чтобы передать ее в mock_filter
    expected_date_obj = datetime.strptime(date_str, "%Y-%m-%d")

    # Мокаем функции
    with patch('src.views.read_operations_excel') as mock_read_excel, \
            patch('src.views.filter_data_by_date_range') as mock_filter, \
            patch('src.views.calculate_expenses') as mock_calc_expenses, \
            patch('src.views.calculate_income') as mock_calc_income, \
            patch('src.views.get_currency_rates') as mock_get_rates, \
            patch('src.views.get_sp500_prices') as mock_get_sp500:

        mock_read_excel.return_value = sample_df
        mock_filter.return_value = sample_df

        mock_calc_expenses.return_value = mock_returns["expenses"]
        mock_calc_income.return_value = mock_returns["income"]
        mock_get_rates.return_value = mock_returns["rates"]
        mock_get_sp500.return_value = mock_returns["sp500"]

        result = get_financial_data(date_str, period)

        assert isinstance(result, dict)

        for key in expected_keys:
            assert key in result, f"Ожидаемый ключ '{key}' не найден в результате: {result}"

        assert result["Расходы"] == mock_returns["expenses"]
        assert result["Поступления"] == mock_returns["income"]
        assert result["Курсы валют"] == mock_returns["rates"]
        assert result["Цена S&P 500"] == mock_returns["sp500"]

        mock_read_excel.assert_called_once()
        mock_filter.assert_called_once_with(sample_df, expected_date_obj, period)
        mock_calc_expenses.assert_called_once_with(sample_df)
        mock_calc_income.assert_called_once_with(sample_df)
        mock_get_rates.assert_called_once()
        mock_get_sp500.assert_called_once()
