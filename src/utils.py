import datetime
import os
import pandas as pd
import requests
import logging
from dotenv import load_dotenv

# Загружаем API_KEY из файла .env
load_dotenv()
API_KEY = os.getenv('API_KEY')

logging.basicConfig(level=logging.INFO)


def read_operations_excel(excel_path: str) -> pd.DataFrame:
    """Читаем Excel и возвращаем DataFrame."""
    try:
        excel_data = pd.read_excel(excel_path)
        if 'date' in excel_data.columns:
            excel_data['date'] = pd.to_datetime(excel_data['date'])
        return excel_data
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return pd.DataFrame()


excel_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'operations.xlsx')
operations_excel = read_operations_excel(excel_path)
print(operations_excel)


def read_operations_excel(excel_path: str) -> pd.DataFrame:
    api_url = "https://marketplace.apilayer.com/exchangerates_data-api"
    try:
        response = requests.get(api_url, headers={'Authorization': f'Bearer {API_KEY}'})
        response.raise_for_status()
        data = response.json()
        return data['rates']
    except Exception as e:
        logging.error(f"Ошибка при получении курсов валют: {e}")
        # Возвращаем примерные курсы по умолчанию
        return {
            "USD": 1.0,
            "EUR": 0.85,
            "RUB": 75.0
        }


def get_sp500_prices() -> float:
    api_url = "https://marketplace.apilayer.com/exchangerates_data-api"
    try:
        response = requests.get(api_url, headers={'Authorization': f'Bearer {API_KEY}'})
        response.raise_for_status()
        data = response.json()
        return data.get('price', 4000)
    except Exception as e:
        logging.error(f"Ошибка при получении стоимости S&P 500: {e}")
        return 4000


def filter_data_by_date_range(df: pd.DataFrame, date_obj: datetime.datetime, range_type: str = "M",) -> pd.DataFrame:
    """Фильтрация данных по диапазону: W, M, Y, ALL."""
    if 'date' not in df.columns:
        raise ValueError("DataFrame должен содержать колонку 'date'.")

    if range_type == 'W':
        start_date = date_obj - datetime.timedelta(days=date_obj.weekday())
        end_date = start_date + datetime.timedelta(days=6)
    elif range_type == 'M':
        start_date = date_obj.replace(day=1)
        next_month = (start_date + datetime.timedelta(days=31)).replace(day=1)
        end_date = next_month - datetime.timedelta(days=1)
    elif range_type == 'Y':
        start_date = date_obj.replace(month=1, day=1)
        end_date = date_obj.replace(month=12, day=31)
    elif range_type == 'ALL':
        return df
    else:
        # по умолчанию месяц
        start_date = date_obj.replace(day=1)
        next_month = (start_date + datetime.timedelta(days=31)).replace(day=1)
        end_date = next_month - datetime.timedelta(days=1)

    return df[(df['date'] >= start_date) & (df['date'] <= end_date)]


def calculate_expenses(df: pd.DataFrame) -> dict:
    """Расчет расходов."""
    expenses = df[df['type'] == 'expense']
    total_expense = round(expenses['amount'].sum())

    category_expenses = expenses.groupby('category')['amount'].sum().sort_values(ascending=False)
    main_categories = category_expenses.head(7).to_dict()
    other_total = category_expenses.iloc[7:].sum() if len(category_expenses) > 7 else 0
    main_categories['Остальное'] = other_total

    cash_transfers = expenses[expenses['category'].isin(['Наличные', 'Переводы'])]\
        .groupby('category')['amount'].sum().sort_values(ascending=False)
    transfers_cash = cash_transfers.to_dict()

    return {
        "Общая сумма": total_expense,
        "Основные": main_categories,
        "Переводы и наличные": transfers_cash
    }


def calculate_income(df: pd.DataFrame) -> dict:
    """Расчет поступлений."""
    income = df[df['type'] == 'income']
    total_income = round(income['amount'].sum())

    category_income = income.groupby('category')['amount'].sum().sort_values(ascending=False)
    main_income = category_income.to_dict()

    return {
        "Общая сумма": total_income,
        "Основные": main_income
    }
