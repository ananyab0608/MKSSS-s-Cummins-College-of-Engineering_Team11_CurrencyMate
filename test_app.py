import unittest
import pandas as pd
from app import app  # Import the Flask app

class TestExchangeRateCalculations(unittest.TestCase):

    def setUp(self):
        # Create a test client
        self.app = app.test_client()
        self.app.testing = True

        # Sample DataFrame to test
        data = {
            'Date': pd.date_range(start='2023-01-01', periods=5, freq='D'),
            'USD': [1.1, 1.2, 1.5, 1.3, 1.4]
        }
        self.df = pd.DataFrame(data).set_index('Date')

    def test_highest_rate(self):
        highest_rate = self.df['USD'].max()
        self.assertEqual(highest_rate, 1.5, "The highest rate should be 1.5.")

    def test_lowest_rate(self):
        lowest_rate = self.df['USD'].min()
        self.assertEqual(lowest_rate, 1.1, "The lowest rate should be 1.1.")

if __name__ == '__main__':
    unittest.main()
