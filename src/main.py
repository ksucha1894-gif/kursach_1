import os
import datetime

from src.utils import (read_operations_excel, filter_data_by_date_range,
                       calculate_expenses, calculate_income,
                       get_sp500_prices)


def get_financial_data(date_str: str, range_type='M'):
    """
    Главная функция для получения фин. данных за конкретный диапазон.
    """
    # Определяем путь к файлу operations.xlsx относительно текущего файла
    current_dir = os.path.dirname(__file__)
    parent_dir = os.path.dirname(current_dir)
    excel_path = os.path.join(parent_dir, 'data', 'operations.xlsx')

    df = read_operations_excel(excel_path)

    if df is None or df.empty:
        return {"error": "Не удалось загрузить операции"}

    # Парсим строковую дату
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return {"error": "Некорректный формат даты. Ожидается YYYY-MM-DD"}

    # Фильтруем по диапазону
    df_filtered = filter_data_by_date_range(df, date_obj, range_type)

    # Расходы
    expenses = calculate_expenses(df_filtered)
    # Поступления
    income = calculate_income(df_filtered)

    # Курсы валют
    currency_rates = get_currency_rates()
    # Цена S&P 500
    sp500_price = get_sp500_prices()

    return {
        "Дата": date_str,
        "Диапазон": range_type,
        "Расходы": expenses,
        "Поступления": income,
        "Курсы валют": currency_rates,
        "Цена S&P 500": sp500_price
    }
