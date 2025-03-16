"""
Tests for the formatting utility functions.
"""
import unittest
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.formatting import format_data_as_html

class TestFormattingUtils(unittest.TestCase):
    """Test cases for the formatting utility functions."""

    def test_format_data_as_html_empty(self):
        """Test formatting empty data."""
        # Empty data
        data = {
            'columns': [],
            'rows': []
        }

        # Format as HTML
        html = format_data_as_html(data)

        # Assertions
        self.assertIn("<div class='alert alert-warning'>No data available</div>", html)

    def test_format_data_as_html_none(self):
        """Test formatting None data."""
        # None data
        html = format_data_as_html(None)

        # Assertions
        self.assertIn("<div class='alert alert-warning'>No data available</div>", html)

    def test_format_data_as_html_with_data(self):
        """Test formatting data with values."""
        # Sample data
        data = {
            'columns': ['id', 'name', 'price'],
            'rows': [
                {'id': 1, 'name': 'Product 1', 'price': 10.99},
                {'id': 2, 'name': 'Product 2', 'price': 20.50}
            ]
        }

        # Format as HTML
        html = format_data_as_html(data)

        # Assertions
        self.assertIn("<table class='table table-sm table-striped'>", html)
        self.assertIn("<thead><tr>", html)
        self.assertIn("<th>id</th>", html)
        self.assertIn("<th>name</th>", html)
        self.assertIn("<th>price</th>", html)
        self.assertIn("<tbody>", html)
        self.assertIn("<td>1</td>", html)
        self.assertIn("<td>Product 1</td>", html)
        self.assertIn("<td>10.99</td>", html)
        self.assertIn("<td>2</td>", html)
        self.assertIn("<td>Product 2</td>", html)
        self.assertIn("<td>20.5</td>", html)

    def test_format_data_as_html_with_null_values(self):
        """Test formatting data with null values."""
        # Sample data with null values
        data = {
            'columns': ['id', 'name', 'price'],
            'rows': [
                {'id': 1, 'name': None, 'price': 10.99},
                {'id': 2, 'name': 'Product 2', 'price': None}
            ]
        }

        # Format as HTML
        html = format_data_as_html(data)

        # Assertions
        self.assertIn("<td><em>NULL</em></td>", html)  # Check for NULL formatting
        self.assertIn("<td>Product 2</td>", html)

    def test_format_data_as_html_missing_columns(self):
        """Test formatting data with missing columns in rows."""
        # Sample data with missing columns
        data = {
            'columns': ['id', 'name', 'price', 'category'],
            'rows': [
                {'id': 1, 'name': 'Product 1', 'price': 10.99},  # Missing category
                {'id': 2, 'name': 'Product 2'}  # Missing price and category
            ]
        }

        # Format as HTML
        html = format_data_as_html(data)

        # Assertions
        self.assertIn("<th>category</th>", html)
        self.assertIn("<td></td>", html)  # Empty cells for missing values

if __name__ == '__main__':
    unittest.main()
