import json
import pandas as pd
from datetime import datetime
import logging
import os
from functools import reduce
from src.utils import read_operations_excel

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def analyze_bonus_from_excel(excel_path: str, year: int, month: int) -> str:
    """
    Читает Excel файл через read_operations_excel, анализирует транзакции за указанный месяц и возвращает JSON.
    """
    try:
        # Чтение Excel файла с помощью функции
        df = read_operations_excel(excel_path)
        if df.empty:
            logging.error("Пустой DataFrame после чтения файла.")
            return json.dumps({"error": "Пустой файл или некорректный путь."})
    except Exception as e:
        logging.error(f"Ошибка при чтении файла через read_operations_excel: {e}")
        return json.dumps({"error": f"Ошибка при чтении файла: {e}"})

    # Проверка колонок
    required_columns = ['Дата операции', 'Категория', 'Сумма операции с округлением']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logging.error(f"Отсутствуют необходимые колонки: {missing_cols}")
        return json.dumps({"error": f"Отсутствуют колонки: {missing_cols}"})

    # Преобразуем данные
    df['date'] = pd.to_datetime(df['Дата операции'], dayfirst=True, errors='coerce')
    df['category'] = df['Категория']
    df['amount'] = df['Сумма операции с округлением']

    # Удаляем строки с некорректной датой
    df = df.dropna(subset=['date'])

    # Фильтрация по году и месяцу
    df_filtered = df[(df['date'].dt.year == year) & (df['date'].dt.month == month)]

    # Конвертация в список словарей
    data = df_filtered.to_dict(orient='records')

    # Анализируем
    def analyze_bonus_categories(data, year, month):
        """
        Анализ транзакций для определения кешбэка по категориям.
        """
        filtered_transactions = list(
            filter(
                lambda t: (
                        'date' in t and
                        isinstance(t['date'], datetime) and
                        t['date'].year == year and
                        t['date'].month == month
                ),
                data
            )
        )

        def reducer(acc, transaction):
            category = transaction.get('category', 'Неопределенная')
            amount = transaction.get('amount', 0)
            cashback_rate = 0.03
            cashback = amount * cashback_rate
            return {
                **acc,
                category: acc.get(category, 0) + cashback
            }

        cashback_by_category = reduce(reducer, filtered_transactions, {})
        return {category: round(amount, 2) for category, amount in cashback_by_category.items()}

    result = analyze_bonus_categories(data, year, month)

    return json.dumps(result, ensure_ascii=False, indent=4)


# Пример использования
if __name__ == "__main__":
    excel_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'operations.xlsx')
    year = 2023
    month = 3

    json_result = analyze_bonus_from_excel(excel_file_path, year, month)
    print(json_result)
