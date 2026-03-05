import json
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

import pandas as pd


logging.basicConfig(
    level=logging.INFO,
    filename="report.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def save_report_to_file(
    filename: Optional[str] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Декоратор, сохраняющий результат функции в файл.
    Если результат – DataFrame → CSV, dict → JSON, иначе – строка.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Tuple[Any, ...], **kwargs: Dict[str, Any]) -> Any:
            result = func(*args, **kwargs)

            file_name = filename or "report.txt"

            try:
                with open(file_name, "w", encoding="utf-8") as f:
                    if isinstance(result, pd.DataFrame):
                        f.write(result.to_csv(index=False, sep="\t"))
                    elif isinstance(result, dict):
                        f.write(json.dumps(result, ensure_ascii=False, indent=2))
                    else:
                        f.write(str(result))
                logging.info(f"Отчет сохранен в файл {file_name}")
            except Exception as exc:  # pragma: no cover
                logging.error(f"Ошибка при сохранении отчета: {exc}")

            return result

        return wrapper

    return decorator


@save_report_to_file()
def spending_by_category(
    transactions: pd.DataFrame,
    category: str,
    date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Формирует отчёт о тратах по выбранной категории за последние 3 месяца.
    Возвращает словарь с итогами.
    """

    column_mapping = {
        "date": ["дата", "date", "Дата"],
        "category": ["категория", "category", "Категория"],
        "amount": ["сумма", "amount", "Сумма"],
    }

    def find_column(columns: pd.Index, keywords: list[str]) -> Optional[str]:
        """
        Поиск колонки, содержащей любой из указанных ключевых слов:
            Список названий колонок (может содержать любые типы).
            Ключевые слова для поиска.
            Название найденной колонки (строка) или ``None`` если ничего не найдено.
        """
        for kw in keywords:
            for col in columns:
                # Приводим колонки к строке, чтобы гарантировать тип ``str``.
                if kw.lower() in str(col).lower():
                    return str(col)
        return None

    date_col = find_column(transactions.columns, column_mapping["date"])
    category_col = find_column(transactions.columns, column_mapping["category"])
    amount_col = find_column(transactions.columns, column_mapping["amount"])

    if not date_col:
        raise KeyError("Не найден столбец с датой.")
    if not category_col:
        raise KeyError("Не найден столбец с категорией.")
    if not amount_col:
        logging.warning(
            "Колонка 'amount' не найдена, создаём нулевую колонку."
        )
        transactions["amount"] = 0.0
        amount_col = "amount"

    transactions.rename(
        columns={date_col: "date", category_col: "category", amount_col: "amount"},
        inplace=True,
    )

    ref_date = pd.to_datetime(date) if date else pd.Timestamp.now()
    transactions["date"] = pd.to_datetime(
        transactions["date"], errors="coerce", dayfirst=False
    )

    start_date = ref_date - pd.DateOffset(months=3)

    mask_date = (transactions["date"] >= start_date) & (
        transactions["date"] <= ref_date
    )
    mask_category = transactions["category"] == category
    filtered = transactions[mask_date & mask_category]

    total_spent = float(filtered["amount"].sum())

    report: Dict[str, Any] = {
        "category": category,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": ref_date.strftime("%Y-%m-%d"),
        "total_spent": total_spent,
    }

    return report
