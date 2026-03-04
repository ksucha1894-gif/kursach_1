import json
from unittest.mock import patch

import pandas as pd
import pytest

from src.services import analyze_bonus_from_excel


@pytest.fixture
def base_dataframe() -> pd.DataFrame:
    """Базовый DataFrame, который будет модифицироваться."""

    data = {
        "date": pd.to_datetime(["2023-01-01", "2023-01-02"]),
        "category": ["A", "B"],
        "amount": [100, 200],
    }
    return pd.DataFrame(data)


@pytest.fixture
def empty_dataframe() -> pd.DataFrame:
    """Пустой DataFrame."""
    return pd.DataFrame()


@pytest.fixture
def df_missing_columns(base_dataframe) -> pd.DataFrame:
    """DataFrame без обязательных колонок."""
    return base_dataframe.drop(columns=["date", "amount"])


@pytest.fixture
def df_fixture(request):
    """
    Получает имя фикстуры из параметра теста и возвращает её значение.
    """
    # request.param содержит строку‑имя фикстуры, например "base_dataframe"
    return request.getfixturevalue(request.param)


test_cases = [
    ("полный датафрейм", "base_dataframe", {"total": 300, "count": 2}),
    ("пустой датафрейм", "empty_dataframe", {"error": "No data"}),
    ("недостающие колонки", "df_missing_columns", {"error": "Missing columns"}),
]


@pytest.mark.parametrize(
    "desc, df_fixture, expected",
    test_cases,
    indirect=["df_fixture"],          # передаём fixture как параметр
)
@patch("src.utils.read_operations_excel")   # mock чтения Excel
@patch("os.path.exists")                 # mock проверки существования пути
def test_analyze_bonus_from_excel(
    mock_path_exists,
    mock_read_excel,
    desc,
    df_fixture,
    expected,
):
    """
    Тестирует analyze_bonus_from_excel() для трёх сценариев:
    1. Полный датафрейм
    2. Пустой датафрейм
    3. Невозможно найти колонки
    """
    # 1. Мокаем проверку существования файла
    mock_path_exists.return_value = True

    # 2. Мокаем чтение Excel – возвращаем DataFrame, который пришёл из fixture
    mock_read_excel.return_value = df_fixture

    # 3. Вызываем тестируемую функцию (путь к файлу – любой, так как мокаем)
    result_json = analyze_bonus_from_excel("dummy_path.xlsx")

    # 4. Преобразуем JSON в dict для удобного сравнения
    result = json.loads(result_json)

    # 5. Сравниваем с ожидаемым
    assert result == expected, f"{desc}: получено {result}, ожидалось {expected}"
