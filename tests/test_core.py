import unittest
from unittest.mock import MagicMock, patch
import services

class TestServices(unittest.TestCase):

    @patch('services.get_db_cursor')
    def test_calculate_tax(self, mock_db):
        # Tax is 10%
        self.assertEqual(services.calculate_tax(100000), 10000)
        self.assertEqual(services.calculate_tax(15500), 1550)

    @patch('services.get_db_cursor')
    @patch('services.datetime')
    def test_generate_transaction_code(self, mock_datetime, mock_get_db_cursor):
        # Mock Date
        mock_date = MagicMock()
        mock_date.strftime.return_value = "20231027"
        mock_datetime.datetime.now.return_value = mock_date

        # Mock DB Cursor Context
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_cursor.return_value.__enter__.return_value = mock_cursor

        # Case 1: No previous transaction
        mock_cursor.fetchone.return_value = None
        code = services.generate_transaction_code()
        self.assertEqual(code, "TRX-20231027-0001")

        # Case 2: Previous transaction exists
        mock_cursor.fetchone.return_value = {'transaction_code': 'TRX-20231027-0042'}
        code = services.generate_transaction_code()
        self.assertEqual(code, "TRX-20231027-0043")

if __name__ == '__main__':
    unittest.main()
