import datetime
import os
import logging
from typing import Dict, Optional, Union

import pandas as pd
import requests
from dotenv import load_dotenv


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


load_dotenv()
API_KEY: Optional[str] = os.getenv("API_KEY")
if not API_KEY:
    logging.warning(
        "API_KEY не найден в окружении – запросы к внешним сервисам могут упасть."
    )


def get_headers() -> Dict[str, str]:
    """
    Возвращает словарь заголовков.
    Если API_KEY доступен, добавляется Authorization Bearer.
    """
    if API_KEY:
        return {"Authorization": f"Bearer {API_KEY}"}
    return {}


def read_operations_excel(excel_path: str) -> pd.DataFrame:
    """
    Считывает Excel‑файл и возвращает DataFrame.
    Если в файле есть колонка «date», она конвертируется в тип datetime.
    """
    try:
        df = pd.read_excel(excel_path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        return df
    except Exception as exc:  # pragma: no cover
        logging.error(f"Ошибка при чтении файла {excel_path}: {exc}")
        return pd.DataFrame()


def get_currency_rates() -> Dict[str, float]:
    """
    Получает актуальные курсы валют из внешнего API.
    При ошибке возвращает набор фиксированных значений.
    """
    api_url = "https://marketplace.apilayer.com/exchangerates_data-api"
    try:
        response = requests.get(api_url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("rates", {})
    except Exception as exc:  # pragma: no cover
        logging.error(f"Ошибка при получении курсов валют: {exc}")
        return {"USD": 1.0, "EUR": 0.85, "RUB": 75.0}


def get_sp500_prices() -> float:
    """
    Получает текущую стоимость индекса S&P 500.
    При ошибке возвращает значение по умолчанию.
    """
    api_url = "https://marketplace.apilayer.com/exchangerates_data-api"
    try:
        response = requests.get(api_url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        data = response.json()
        price = data.get("price", 4000)
        return float(price)
    except Exception as exc:  # pragma: no cover
        logging.error(f"Ошибка при получении стоимости S&P 500: {exc}")
        return 4000.0


def filter_data_by_date_range(
    df: pd.DataFrame,
    date_obj: datetime.datetime,
    range_type: str = "M",
) -> pd.DataFrame:
    """
    Фильтрует DataFrame по указанному диапазону дат.
    """
    if "date" not in df.columns:
        raise ValueError("DataFrame должен содержать колонку 'date'.")

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
    elif range_type == "ALL":
        return df.copy()
    else:
        # Если передан неизвестный тип – считаем месяц
        start_date = date_obj.replace(day=1)
        next_month = (start_date + datetime.timedelta(days=31)).replace(day=1)
        end_date = next_month - datetime.timedelta(days=1)

    mask = (df["date"] >= start_date) & (df["date"] <= end_date)
    return df[mask].copy()


def calculate_expenses(df: pd.DataFrame) -> Dict[str, Union[int, Dict[str, float]]]:
    """
    Вычисляет общую сумму расходов, распределение по основным категориям
    и отдельные суммы для «Наличные» и «Переводы».
    """
    expenses = df[df["type"] == "expense"]
    total_expense = int(round(expenses["amount"].sum()))

    category_expenses = (
        expenses.groupby("category")["amount"].sum().sort_values(ascending=False)
    )
    main_categories = category_expenses.head(7).to_dict()
    other_total = category_expenses.iloc[7:].sum() if len(category_expenses) > 7 else 0
    main_categories["Остальное"] = float(other_total)

    cash_transfers = expenses[expenses["category"].isin(["Наличные", "Переводы"])]
    transfers_cash = cash_transfers.groupby("category")["amount"].sum().to_dict()

    return {
        "Общая сумма": total_expense,
        "Основные": main_categories,
        "Переводы и наличные": transfers_cash,
    }


def calculate_income(df: pd.DataFrame) -> Dict[str, Union[int, Dict[str, float]]]:
    """
    Вычисляет общую сумму поступлений и распределение по категориям.
    """
    income = df[df["type"] == "income"]
    total_income = int(round(income["amount"].sum()))

    category_income = income.groupby("category")["amount"].sum().sort_values(ascending=False)
    main_income = category_income.to_dict()

    return {
        "Общая сумма": total_income,
        "Основные": main_income,
    }
