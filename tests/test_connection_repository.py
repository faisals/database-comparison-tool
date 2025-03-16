"""
Tests for the ConnectionRepository class.
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the pymssql module
mock_pymssql = MagicMock()
sys.modules['pymssql'] = mock_pymssql

from app.models.connection_repository import ConnectionRepository

class TestConnectionRepository(unittest.TestCase):
    """Test cases for the ConnectionRepository class."""

    def setUp(self):
        """Set up test environment."""
        # Reset mocks before each test
        mock_pymssql.reset_mock()
        mock_pymssql.connect.side_effect = None
        
        self.repository = ConnectionRepository(
            server='localhost',
            database='dbcomparetool',
            username='graph',
            password='Openup123#'
        )
        
        # Mock connection and cursor
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor
        mock_pymssql.connect.return_value = self.mock_connection
        
        # Set up repository connection
        self.repository.connection = self.mock_connection
        self.repository.cursor = self.mock_cursor

    def test_init(self):
        """Test initialization of ConnectionRepository."""
        repository = ConnectionRepository()
        self.assertEqual(repository.server, 'localhost')
        self.assertEqual(repository.database, 'dbcomparetool')
        self.assertEqual(repository.username, 'graph')
        self.assertEqual(repository.password, 'Openup123#')
        self.assertIsNone(repository.connection)
        self.assertIsNone(repository.cursor)

    def test_connect_success(self):
        """Test successful connection to repository database."""
        # Reset repository connection
        self.repository.connection = None
        self.repository.cursor = None
        
        # Call the method
        result = self.repository.connect()
        
        # Assertions
        self.assertTrue(result)
        self.assertEqual(self.repository.connection, self.mock_connection)
        self.assertEqual(self.repository.cursor, self.mock_cursor)
        mock_pymssql.connect.assert_called_once_with(
            server='localhost',
            user='graph',
            password='Openup123#',
            database='dbcomparetool'
        )

    def test_connect_failure(self):
        """Test connection failure to repository database."""
        # Reset repository connection
        self.repository.connection = None
        self.repository.cursor = None
        
        # Set up mock to raise exception
        mock_pymssql.connect.side_effect = Exception("Connection failed")
        
        # Call the method
        result = self.repository.connect()
        
        # Assertions
        self.assertFalse(result)
        self.assertIsNone(self.repository.connection)
        self.assertIsNone(self.repository.cursor)

    def test_disconnect(self):
        """Test disconnection from repository database."""
        # Call the method
        self.repository.disconnect()
        
        # Assertions
        self.mock_cursor.close.assert_called_once()
        self.mock_connection.close.assert_called_once()

    def test_ensure_tables_exist(self):
        """Test ensuring tables exist in the database."""
        # Call the method
        result = self.repository.ensure_tables_exist()
        
        # Assertions
        self.assertTrue(result)
        self.mock_cursor.execute.assert_called_once()
        self.mock_connection.commit.assert_called_once()

    def test_ensure_tables_exist_error(self):
        """Test error handling when ensuring tables exist."""
        # Set up mock to raise exception
        self.mock_cursor.execute.side_effect = Exception("SQL error")
        
        # Call the method
        result = self.repository.ensure_tables_exist()
        
        # Assertions
        self.assertFalse(result)
        self.mock_cursor.execute.assert_called_once()
        self.mock_connection.commit.assert_not_called()

    def test_save_connection_new(self):
        """Test saving a new connection."""
        # Set up mock to return 0 (no existing connection)
        self.mock_cursor.fetchone.return_value = (0,)
        
        # Call the method
        result = self.repository.save_connection(
            connection_name='Test Connection',
            server='test-server',
            database='test-db',
            username='test-user',
            password='test-pass'
        )
        
        # Assertions
        self.assertTrue(result)
        self.assertEqual(self.mock_cursor.execute.call_count, 2)  # One for check, one for insert
        self.mock_connection.commit.assert_called_once()

    def test_save_connection_update(self):
        """Test updating an existing connection."""
        # Set up mock to return 1 (existing connection)
        self.mock_cursor.fetchone.return_value = (1,)
        
        # Call the method
        result = self.repository.save_connection(
            connection_name='Test Connection',
            server='test-server',
            database='test-db',
            username='test-user',
            password='test-pass'
        )
        
        # Assertions
        self.assertTrue(result)
        self.assertEqual(self.mock_cursor.execute.call_count, 2)  # One for check, one for update
        self.mock_connection.commit.assert_called_once()

    def test_save_connection_error(self):
        """Test error handling when saving a connection."""
        # Set up mock to raise exception
        self.mock_cursor.execute.side_effect = Exception("SQL error")
        
        # Call the method
        result = self.repository.save_connection(
            connection_name='Test Connection',
            server='test-server',
            database='test-db',
            username='test-user',
            password='test-pass'
        )
        
        # Assertions
        self.assertFalse(result)
        self.mock_cursor.execute.assert_called_once()
        self.mock_connection.commit.assert_not_called()

    def test_get_all_connections(self):
        """Test retrieving all connections."""
        # Set up mock to return test data
        mock_rows = [
            (1, 'Connection 1', 'server1', 'db1', 'user1', 'pass1', datetime.now(), datetime.now()),
            (2, 'Connection 2', 'server2', 'db2', 'user2', 'pass2', datetime.now(), datetime.now())
        ]
        self.mock_cursor.fetchall.return_value = mock_rows
        
        # Call the method
        connections = self.repository.get_all_connections()
        
        # Assertions
        self.assertEqual(len(connections), 2)
        self.assertEqual(connections[0]['id'], 1)
        self.assertEqual(connections[0]['name'], 'Connection 1')
        self.assertEqual(connections[1]['id'], 2)
        self.assertEqual(connections[1]['name'], 'Connection 2')

    def test_get_all_connections_error(self):
        """Test error handling when retrieving all connections."""
        # Set up mock to raise exception
        self.mock_cursor.execute.side_effect = Exception("SQL error")
        
        # Call the method
        connections = self.repository.get_all_connections()
        
        # Assertions
        self.assertEqual(connections, [])
        self.mock_cursor.execute.assert_called_once()

    def test_get_connection_by_name_found(self):
        """Test retrieving a connection by name when it exists."""
        # Set up mock to return test data
        mock_row = (1, 'Test Connection', 'test-server', 'test-db', 'test-user', 'test-pass', datetime.now(), datetime.now())
        self.mock_cursor.fetchone.return_value = mock_row
        
        # Call the method
        connection = self.repository.get_connection_by_name('Test Connection')
        
        # Assertions
        self.assertIsNotNone(connection)
        self.assertEqual(connection['id'], 1)
        self.assertEqual(connection['name'], 'Test Connection')
        self.assertEqual(connection['server'], 'test-server')
        self.assertEqual(connection['database'], 'test-db')
        self.assertEqual(connection['username'], 'test-user')
        self.assertEqual(connection['password'], 'test-pass')

    def test_get_connection_by_name_not_found(self):
        """Test retrieving a connection by name when it doesn't exist."""
        # Set up mock to return None
        self.mock_cursor.fetchone.return_value = None
        
        # Call the method
        connection = self.repository.get_connection_by_name('Nonexistent Connection')
        
        # Assertions
        self.assertIsNone(connection)

    def test_get_connection_by_name_error(self):
        """Test error handling when retrieving a connection by name."""
        # Set up mock to raise exception
        self.mock_cursor.execute.side_effect = Exception("SQL error")
        
        # Call the method
        connection = self.repository.get_connection_by_name('Test Connection')
        
        # Assertions
        self.assertIsNone(connection)
        self.mock_cursor.execute.assert_called_once()

    def test_delete_connection(self):
        """Test deleting a connection."""
        # Call the method
        result = self.repository.delete_connection('Test Connection')
        
        # Assertions
        self.assertTrue(result)
        self.mock_cursor.execute.assert_called_once()
        self.mock_connection.commit.assert_called_once()

    def test_delete_connection_error(self):
        """Test error handling when deleting a connection."""
        # Set up mock to raise exception
        self.mock_cursor.execute.side_effect = Exception("SQL error")
        
        # Call the method
        result = self.repository.delete_connection('Test Connection')
        
        # Assertions
        self.assertFalse(result)
        self.mock_cursor.execute.assert_called_once()
        self.mock_connection.commit.assert_not_called()

    def test_update_last_used_date(self):
        """Test updating the last used date for a connection."""
        # Call the method
        result = self.repository.update_last_used_date('Test Connection')
        
        # Assertions
        self.assertTrue(result)
        self.mock_cursor.execute.assert_called_once()
        self.mock_connection.commit.assert_called_once()

    def test_update_last_used_date_error(self):
        """Test error handling when updating the last used date."""
        # Set up mock to raise exception
        self.mock_cursor.execute.side_effect = Exception("SQL error")
        
        # Call the method
        result = self.repository.update_last_used_date('Test Connection')
        
        # Assertions
        self.assertFalse(result)
        self.mock_cursor.execute.assert_called_once()
        self.mock_connection.commit.assert_not_called()

if __name__ == '__main__':
    unittest.main()
