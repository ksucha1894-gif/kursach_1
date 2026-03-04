import unittest
import pandas as pd
from src.reports import spending_by_category


class TestSpendingByCategory(unittest.TestCase):

    def setUp(self):
        # Создаем тестовые данные
        self.data = pd.DataFrame({
            'date': [
                '2023-01-15', '2023-02-10', '2023-03-20', '2023-04-01',
                '2022-12-01', '2022-11-15'
            ],
            'category': [
                'Банковские операции', 'Общие расходы', 'Банковские операции',
                'Банковские операции', 'Банковские операции', 'Общие расходы'
            ],
            'amount': [1000, 200, 300, 400, 500, 600]
        })

    def test_spending_last_3_months(self):
        # Проверка суммы по категории 'Банковские операции' за последние 3 месяца
        category = 'Банковские операции'
        date_str = '2023-04-01'
        report = spending_by_category(self.data.copy(), category, date=date_str)

        # Ожидаемая сумма: 2023-01-15 (1000), 2023-03-20 (300), 2023-04-01 (400)
        expected_total = 1000 + 300 + 400

        self.assertIsInstance(report, dict)
        self.assertAlmostEqual(report['total_spent'], expected_total, places=2)
        self.assertEqual(report['category'], category)
        self.assertEqual(report['start_date'], '2023-01-01')
        self.assertEqual(report['end_date'], '2023-04-01')

    def test_spending_other_category(self):
        # Проверка суммы по другой категории, которая есть в диапазоне
        category = 'Общие расходы'
        date_str = '2023-04-01'
        report = spending_by_category(self.data.copy(), category, date=date_str)

        # В последние 3 месяца есть одна подходящая запись: 2023-02-10 (200)
        self.assertEqual(report['total_spent'], 200.0)

    def test_missing_column(self):
        # Проверка поведения при отсутствии колонки 'date'
        df_no_date = self.data.drop(columns=['date'])
        with self.assertRaises(KeyError):
            spending_by_category(df_no_date, 'Банковские операции', date='2023-04-01')

    def test_amount_column_absent(self):
        # Проверка, что при отсутствии колонки 'amount' возвращается 0
        df_no_amount = self.data.drop(columns=['amount'])
        report = spending_by_category(df_no_amount, 'Банковские операции', date='2023-04-01')
        self.assertEqual(report['total_spent'], 0.0)

    def test_no_data_in_range(self):
        # Создаем данные вне диапазона последних 3 месяцев
        df = pd.DataFrame({
            'date': ['2022-01-01', '2022-12-01'],
            'category': ['Общие расходы', 'Банковские операции'],
            'amount': [100, 300]
        })

        report = spending_by_category(df, 'Общие расходы', date='2023-04-01')
        # Данных для этой категории в диапазоне нет
        self.assertEqual(report['total_spent'], 0.0)


if __name__ == '__main__':
    unittest.main()
