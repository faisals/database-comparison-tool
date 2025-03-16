"""
Tests for the DatabaseConnection class.
"""
import unittest
from unittest.mock import MagicMock
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create mock modules
mock_pymssql = MagicMock()

# Mock the modules
sys.modules['pymssql'] = mock_pymssql

from app.models.database import DatabaseConnection

class TestDatabaseConnection(unittest.TestCase):
    """Test cases for the DatabaseConnection class."""

    def setUp(self):
        """Set up test environment."""
        # Reset mocks before each test
        mock_pymssql.reset_mock()
        
        # Clear side effects
        mock_pymssql.connect.side_effect = None
        
        self.connection = DatabaseConnection(
            server='test_server',
            database='test_db',
            username='test_user',
            password='test_pass'
        )

    def test_init(self):
        """Test initialization of DatabaseConnection."""
        self.assertEqual(self.connection.server, 'test_server')
        self.assertEqual(self.connection.database, 'test_db')
        self.assertEqual(self.connection.username, 'test_user')
        self.assertEqual(self.connection.password, 'test_pass')
        self.assertIsNone(self.connection.connection)
        self.assertIsNone(self.connection.cursor)

    def test_connect_success(self):
        """Test successful connection using pymssql."""
        # Set up mock
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_pymssql.connect.return_value = mock_connection

        # Call the method
        result = self.connection.connect()

        # Assertions
        self.assertTrue(result)
        self.assertEqual(self.connection.connection, mock_connection)
        self.assertEqual(self.connection.cursor, mock_cursor)
        mock_pymssql.connect.assert_called_once_with(
            server='test_server',
            user='test_user',
            password='test_pass',
            database='test_db',
            appname='Database Comparison Tool'
        )

    def test_connect_fail(self):
        """Test handling when connection fails."""
        # Set up mocks
        mock_pymssql.connect.side_effect = Exception("pymssql failed")

        # Call the method
        result = self.connection.connect()

        # Assertions
        self.assertFalse(result)
        self.assertIsNone(self.connection.connection)
        self.assertIsNone(self.connection.cursor)

    def test_disconnect(self):
        """Test disconnection from database."""
        # Set up mock connection and cursor
        self.connection.connection = MagicMock()
        self.connection.cursor = MagicMock()

        # Call the method
        self.connection.disconnect()

        # Assertions
        self.connection.cursor.close.assert_called_once()
        self.connection.connection.close.assert_called_once()

    def test_disconnect_no_connection(self):
        """Test disconnection when no connection exists."""
        # Ensure connection and cursor are None
        self.connection.connection = None
        self.connection.cursor = None

        # This should not raise an exception
        self.connection.disconnect()

    def test_get_tables(self):
        """Test retrieving tables from database."""
        # Set up mock cursor
        self.connection.cursor = MagicMock()
        mock_rows = [('table1',), ('table2',), ('table3',)]
        self.connection.cursor.fetchall.return_value = mock_rows

        # Call the method
        tables = self.connection.get_tables()

        # Assertions
        self.connection.cursor.execute.assert_called_once()
        self.assertEqual(tables, ['table1', 'table2', 'table3'])

    def test_get_table_schema(self):
        """Test retrieving table schema."""
        # Set up mock cursor
        self.connection.cursor = MagicMock()
        mock_rows = [
            ('id', 'int', None, 10, 0, 'NO', 1, 1),
            ('name', 'varchar', 100, None, None, 'YES', 0, 0),
            ('price', 'decimal', None, 10, 2, 'YES', 0, 0)
        ]
        self.connection.cursor.fetchall.return_value = mock_rows

        # Call the method
        schema = self.connection.get_table_schema('test_table')

        # Assertions
        self.connection.cursor.execute.assert_called_once()
        self.assertEqual(len(schema), 3)
        
        # Check first column (id)
        self.assertEqual(schema[0]['name'], 'id')
        self.assertEqual(schema[0]['type'], 'int')
        self.assertEqual(schema[0]['is_nullable'], 'No')
        self.assertEqual(schema[0]['is_identity'], 'Yes')
        self.assertEqual(schema[0]['is_primary_key'], 'Yes')
        self.assertEqual(schema[0]['formatted_data_type'], 'int')
        
        # Check second column (name)
        self.assertEqual(schema[1]['name'], 'name')
        self.assertEqual(schema[1]['type'], 'varchar')
        self.assertEqual(schema[1]['max_length'], 100)
        self.assertEqual(schema[1]['formatted_data_type'], 'varchar(100)')
        
        # Check third column (price)
        self.assertEqual(schema[2]['name'], 'price')
        self.assertEqual(schema[2]['type'], 'decimal')
        self.assertEqual(schema[2]['numeric_precision'], 10)
        self.assertEqual(schema[2]['numeric_scale'], 2)
        self.assertEqual(schema[2]['formatted_data_type'], 'decimal(10,2)')

    def test_get_table_data_all_columns(self):
        """Test retrieving table data with all columns."""
        # Set up mock cursor
        self.connection.cursor = MagicMock()
        mock_rows = [
            (1, 'Product 1', 10.99),
            (2, 'Product 2', 20.50)
        ]
        self.connection.cursor.fetchall.return_value = mock_rows
        self.connection.cursor.description = [
            ('id', None, None, None, None, None, None),
            ('name', None, None, None, None, None, None),
            ('price', None, None, None, None, None, None)
        ]

        # Call the method
        data = self.connection.get_table_data('test_table')

        # Assertions
        self.connection.cursor.execute.assert_called_once()
        self.assertEqual(data['columns'], ['id', 'name', 'price'])
        self.assertEqual(len(data['rows']), 2)
        self.assertEqual(data['rows'][0]['id'], 1)
        self.assertEqual(data['rows'][0]['name'], 'Product 1')
        self.assertEqual(data['rows'][0]['price'], 10.99)
        self.assertEqual(data['rows'][1]['id'], 2)
        self.assertEqual(data['rows'][1]['name'], 'Product 2')
        self.assertEqual(data['rows'][1]['price'], 20.50)
        self.assertEqual(data['total_rows'], 2)

    def test_get_table_data_selected_columns(self):
        """Test retrieving table data with selected columns."""
        # Set up mock cursor
        self.connection.cursor = MagicMock()
        mock_rows = [
            ('Product 1', 10.99),
            ('Product 2', 20.50)
        ]
        self.connection.cursor.fetchall.return_value = mock_rows

        # Call the method
        columns = ['name', 'price']
        data = self.connection.get_table_data('test_table', columns=columns)

        # Assertions
        self.connection.cursor.execute.assert_called_once()
        self.assertEqual(data['columns'], ['name', 'price'])
        self.assertEqual(len(data['rows']), 2)
        self.assertEqual(data['rows'][0]['name'], 'Product 1')
        self.assertEqual(data['rows'][0]['price'], 10.99)
        self.assertEqual(data['rows'][1]['name'], 'Product 2')
        self.assertEqual(data['rows'][1]['price'], 20.50)
        self.assertEqual(data['total_rows'], 2)

    def test_get_table_data_error(self):
        """Test handling error when retrieving table data."""
        # Set up mock cursor to raise exception
        self.connection.cursor = MagicMock()
        self.connection.cursor.execute.side_effect = Exception("SQL error")

        # Call the method
        data = self.connection.get_table_data('test_table')

        # Assertions
        self.connection.cursor.execute.assert_called_once()
        self.assertEqual(data['columns'], [])
        self.assertEqual(data['rows'], [])
        self.assertEqual(data['total_rows'], 0)

    def test_get_row_count(self):
        """Test retrieving row count for a table."""
        # Set up mock cursor
        self.connection.cursor = MagicMock()
        self.connection.cursor.fetchone.return_value = (100,)

        # Call the method
        count = self.connection.get_row_count('test_table')

        # Assertions
        self.connection.cursor.execute.assert_called_once()
        self.assertEqual(count, 100)

    def test_get_row_count_error(self):
        """Test handling error when retrieving row count."""
        # Set up mock cursor to raise exception
        self.connection.cursor = MagicMock()
        self.connection.cursor.execute.side_effect = Exception("SQL error")

        # Call the method
        count = self.connection.get_row_count('test_table')

        # Assertions
        self.connection.cursor.execute.assert_called_once()
        self.assertEqual(count, 0)

if __name__ == '__main__':
    unittest.main()
