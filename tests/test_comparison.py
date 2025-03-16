"""
Tests for the comparison utility functions.
"""
import unittest
import sys
import os
import pandas as pd
import numpy as np

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.comparison import compare_schemas, compare_data

class TestComparisonUtils(unittest.TestCase):
    """Test cases for the comparison utility functions."""

    def test_compare_schemas_identical(self):
        """Test comparing identical schemas."""
        # Create identical schemas
        schema1 = [
            {
                'name': 'id',
                'type': 'int',
                'max_length': 0,
                'numeric_precision': 10,
                'numeric_scale': 0,
                'is_nullable': 'No',
                'is_identity': 'Yes',
                'is_primary_key': 'Yes',
                'formatted_data_type': 'int'
            },
            {
                'name': 'name',
                'type': 'varchar',
                'max_length': 100,
                'numeric_precision': None,
                'numeric_scale': None,
                'is_nullable': 'No',
                'is_identity': 'No',
                'is_primary_key': 'No',
                'formatted_data_type': 'varchar(100)'
            }
        ]
        schema2 = schema1.copy()  # Identical schema

        # Compare schemas
        result = compare_schemas(schema1, schema2)

        # Assertions
        self.assertEqual(result['total_columns_schema1'], 2)
        self.assertEqual(result['total_columns_schema2'], 2)
        self.assertEqual(result['identical_columns'], 2)
        self.assertEqual(len(result['common_columns']), 2)
        self.assertEqual(len(result['only_in_source']), 0)
        self.assertEqual(len(result['only_in_target']), 0)
        self.assertEqual(len(result['differences']), 0)

    def test_compare_schemas_different_columns(self):
        """Test comparing schemas with different columns."""
        # Create schemas with different columns
        schema1 = [
            {
                'name': 'id',
                'type': 'int',
                'max_length': 0,
                'numeric_precision': 10,
                'numeric_scale': 0,
                'is_nullable': 'No',
                'is_identity': 'Yes',
                'is_primary_key': 'Yes',
                'formatted_data_type': 'int'
            },
            {
                'name': 'name',
                'type': 'varchar',
                'max_length': 100,
                'numeric_precision': None,
                'numeric_scale': None,
                'is_nullable': 'No',
                'is_identity': 'No',
                'is_primary_key': 'No',
                'formatted_data_type': 'varchar(100)'
            },
            {
                'name': 'source_only',
                'type': 'int',
                'max_length': 0,
                'numeric_precision': 10,
                'numeric_scale': 0,
                'is_nullable': 'Yes',
                'is_identity': 'No',
                'is_primary_key': 'No',
                'formatted_data_type': 'int'
            }
        ]
        
        schema2 = [
            {
                'name': 'id',
                'type': 'int',
                'max_length': 0,
                'numeric_precision': 10,
                'numeric_scale': 0,
                'is_nullable': 'No',
                'is_identity': 'Yes',
                'is_primary_key': 'Yes',
                'formatted_data_type': 'int'
            },
            {
                'name': 'name',
                'type': 'varchar',
                'max_length': 100,
                'numeric_precision': None,
                'numeric_scale': None,
                'is_nullable': 'No',
                'is_identity': 'No',
                'is_primary_key': 'No',
                'formatted_data_type': 'varchar(100)'
            },
            {
                'name': 'target_only',
                'type': 'datetime',
                'max_length': 0,
                'numeric_precision': None,
                'numeric_scale': None,
                'is_nullable': 'Yes',
                'is_identity': 'No',
                'is_primary_key': 'No',
                'formatted_data_type': 'datetime'
            }
        ]

        # Compare schemas
        result = compare_schemas(schema1, schema2)

        # Assertions
        self.assertEqual(result['total_columns_schema1'], 3)
        self.assertEqual(result['total_columns_schema2'], 3)
        self.assertEqual(result['identical_columns'], 2)
        self.assertEqual(len(result['common_columns']), 2)
        self.assertEqual(len(result['only_in_source']), 1)
        self.assertEqual(len(result['only_in_target']), 1)
        self.assertEqual(result['only_in_source'][0], 'source_only')
        self.assertEqual(result['only_in_target'][0], 'target_only')
        self.assertEqual(len(result['differences']), 0)

    def test_compare_schemas_different_properties(self):
        """Test comparing schemas with different column properties."""
        # Create schemas with different column properties
        schema1 = [
            {
                'name': 'id',
                'type': 'int',
                'max_length': 0,
                'numeric_precision': 10,
                'numeric_scale': 0,
                'is_nullable': 'No',
                'is_identity': 'Yes',
                'is_primary_key': 'Yes',
                'formatted_data_type': 'int'
            },
            {
                'name': 'name',
                'type': 'varchar',
                'max_length': 100,
                'numeric_precision': None,
                'numeric_scale': None,
                'is_nullable': 'No',
                'is_identity': 'No',
                'is_primary_key': 'No',
                'formatted_data_type': 'varchar(100)'
            }
        ]
        
        schema2 = [
            {
                'name': 'id',
                'type': 'int',
                'max_length': 0,
                'numeric_precision': 10,
                'numeric_scale': 0,
                'is_nullable': 'No',
                'is_identity': 'Yes',
                'is_primary_key': 'Yes',
                'formatted_data_type': 'int'
            },
            {
                'name': 'name',
                'type': 'varchar',
                'max_length': 200,  # Different max_length
                'numeric_precision': None,
                'numeric_scale': None,
                'is_nullable': 'Yes',  # Different nullability
                'is_identity': 'No',
                'is_primary_key': 'No',
                'formatted_data_type': 'varchar(200)'  # Different formatted_data_type
            }
        ]

        # Compare schemas
        result = compare_schemas(schema1, schema2)

        # Assertions
        self.assertEqual(result['total_columns_schema1'], 2)
        self.assertEqual(result['total_columns_schema2'], 2)
        self.assertEqual(result['identical_columns'], 1)
        self.assertEqual(len(result['common_columns']), 2)
        self.assertEqual(len(result['only_in_source']), 0)
        self.assertEqual(len(result['only_in_target']), 0)
        self.assertEqual(len(result['differences']), 1)
        
        # Check the differences for the 'name' column
        name_diff = next((d for d in result['differences'] if d['column_name'] == 'name'), None)
        self.assertIsNotNone(name_diff)
        # DeepDiff detects data type, nullability, and max_length differences
        self.assertGreaterEqual(len(name_diff['differences']), 2)  
        self.assertTrue(any('Data type' in diff for diff in name_diff['differences']))
        self.assertTrue(any('Nullable' in diff for diff in name_diff['differences']))

    def test_compare_schemas_nested_properties(self):
        """Test comparing schemas with nested property differences using DeepDiff."""
        # Create schemas with nested property differences
        schema1 = [
            {
                'name': 'id',
                'type': 'int',
                'max_length': 0,
                'numeric_precision': 10,
                'numeric_scale': 0,
                'is_nullable': 'No',
                'is_identity': 'Yes',
                'is_primary_key': 'Yes',
                'formatted_data_type': 'int',
                'metadata': {
                    'last_updated': '2023-01-01',
                    'indexed': True,
                    'stats': {
                        'cardinality': 1000,
                        'distribution': 'uniform'
                    }
                }
            },
            {
                'name': 'complex_column',
                'type': 'json',
                'max_length': None,
                'numeric_precision': None,
                'numeric_scale': None,
                'is_nullable': 'Yes',
                'is_identity': 'No',
                'is_primary_key': 'No',
                'formatted_data_type': 'json',
                'metadata': {
                    'validation_schema': {
                        'type': 'object',
                        'required': ['id', 'name']
                    }
                }
            }
        ]
        
        schema2 = [
            {
                'name': 'id',
                'type': 'int',
                'max_length': 0,
                'numeric_precision': 10,
                'numeric_scale': 0,
                'is_nullable': 'No',
                'is_identity': 'Yes',
                'is_primary_key': 'Yes',
                'formatted_data_type': 'int',
                'metadata': {
                    'last_updated': '2023-02-15',  # Different date
                    'indexed': True,
                    'stats': {
                        'cardinality': 1200,  # Different cardinality
                        'distribution': 'uniform'
                    }
                }
            },
            {
                'name': 'complex_column',
                'type': 'json',
                'max_length': None,
                'numeric_precision': None,
                'numeric_scale': None,
                'is_nullable': 'Yes',
                'is_identity': 'No',
                'is_primary_key': 'No',
                'formatted_data_type': 'json',
                'metadata': {
                    'validation_schema': {
                        'type': 'object',
                        'required': ['id', 'name', 'timestamp']  # Added requirement
                    }
                }
            }
        ]

        # Compare schemas
        result = compare_schemas(schema1, schema2)

        # Assertions
        self.assertEqual(result['total_columns_schema1'], 2)
        self.assertEqual(result['total_columns_schema2'], 2)
        self.assertEqual(len(result['common_columns']), 2)
        self.assertEqual(len(result['only_in_source']), 0)
        self.assertEqual(len(result['only_in_target']), 0)
        
        # The DeepDiff implementation should detect nested differences
        self.assertEqual(len(result['differences']), 2)
        
        # Check that we found differences in both columns
        column_names_with_diffs = [d['column_name'] for d in result['differences']]
        self.assertIn('id', column_names_with_diffs)
        self.assertIn('complex_column', column_names_with_diffs)
        
        # Verify that at least some of the differences were detected
        id_diff = next((d for d in result['differences'] if d['column_name'] == 'id'), None)
        self.assertIsNotNone(id_diff)
        
        complex_diff = next((d for d in result['differences'] if d['column_name'] == 'complex_column'), None)
        self.assertIsNotNone(complex_diff)

    def test_compare_data_identical(self):
        """Test comparing identical data."""
        # Create identical data sets
        data1 = {
            'columns': ['id', 'name', 'price'],
            'rows': [
                {'id': 1, 'name': 'Product 1', 'price': 10.99},
                {'id': 2, 'name': 'Product 2', 'price': 20.50}
            ],
            'total_rows': 2
        }
        
        data2 = {
            'columns': ['id', 'name', 'price'],
            'rows': [
                {'id': 1, 'name': 'Product 1', 'price': 10.99},
                {'id': 2, 'name': 'Product 2', 'price': 20.50}
            ],
            'total_rows': 2
        }

        # Compare data
        result = compare_data(data1, data2, ['id', 'name', 'price'])

        # Assertions
        self.assertEqual(result['summary']['source_total_rows'], 2)
        self.assertEqual(result['summary']['target_total_rows'], 2)
        self.assertEqual(result['summary']['total_rows_compared'], 2)
        self.assertEqual(result['summary']['rows_with_differences'], 0)
        self.assertEqual(len(result['data_differences']), 0)

    def test_compare_data_different_values(self):
        """Test comparing data with different values."""
        # Create data sets with different values
        data1 = {
            'columns': ['id', 'name', 'price'],
            'rows': [
                {'id': 1, 'name': 'Product 1', 'price': 10.99},
                {'id': 2, 'name': 'Product 2', 'price': 20.50}
            ],
            'total_rows': 2
        }
        
        data2 = {
            'columns': ['id', 'name', 'price'],
            'rows': [
                {'id': 1, 'name': 'Product 1', 'price': 11.99},  # Different price
                {'id': 2, 'name': 'Different Name', 'price': 20.50}  # Different name
            ],
            'total_rows': 2
        }

        # Compare data
        result = compare_data(data1, data2, ['id', 'name', 'price'])

        # Assertions
        self.assertEqual(result['summary']['source_total_rows'], 2)
        self.assertEqual(result['summary']['target_total_rows'], 2)
        self.assertEqual(result['summary']['total_rows_compared'], 2)
        self.assertEqual(result['summary']['rows_with_differences'], 2)
        self.assertEqual(len(result['data_differences']), 2)
        
        # Check first row differences (price)
        self.assertEqual(result['data_differences'][0]['row'], 1)
        self.assertEqual(len(result['data_differences'][0]['differences']), 1)
        self.assertEqual(result['data_differences'][0]['differences']['price']['source'], '10.99')
        self.assertEqual(result['data_differences'][0]['differences']['price']['target'], '11.99')
        
        # Check second row differences (name)
        self.assertEqual(result['data_differences'][1]['row'], 2)
        self.assertEqual(len(result['data_differences'][1]['differences']), 1)
        self.assertEqual(result['data_differences'][1]['differences']['name']['source'], 'Product 2')
        self.assertEqual(result['data_differences'][1]['differences']['name']['target'], 'Different Name')

    def test_compare_data_different_row_counts(self):
        """Test comparing data with different row counts."""
        # Create data sets with different row counts
        data1 = {
            'columns': ['id', 'name', 'price'],
            'rows': [
                {'id': 1, 'name': 'Product 1', 'price': 10.99},
                {'id': 2, 'name': 'Product 2', 'price': 20.50},
                {'id': 3, 'name': 'Product 3', 'price': 30.00}
            ],
            'total_rows': 3
        }
        
        data2 = {
            'columns': ['id', 'name', 'price'],
            'rows': [
                {'id': 1, 'name': 'Product 1', 'price': 10.99},
                {'id': 2, 'name': 'Product 2', 'price': 20.50}
            ],
            'total_rows': 2
        }

        # Compare data
        result = compare_data(data1, data2, ['id', 'name', 'price'])

        # Assertions
        self.assertEqual(result['summary']['source_total_rows'], 3)
        self.assertEqual(result['summary']['target_total_rows'], 2)
        self.assertEqual(result['summary']['total_rows_compared'], 2)  # Only compares up to the minimum number of rows
        self.assertEqual(result['summary']['rows_with_differences'], 0)
        self.assertEqual(result['summary']['row_count_difference'], 1)
        self.assertEqual(len(result['data_differences']), 0)

    def test_compare_data_null_values(self):
        """Test comparing data with null values."""
        # Create data sets with null values
        data1 = {
            'columns': ['id', 'name', 'price'],
            'rows': [
                {'id': 1, 'name': 'Product 1', 'price': None},
                {'id': 2, 'name': None, 'price': 20.50}
            ],
            'total_rows': 2
        }
        
        data2 = {
            'columns': ['id', 'name', 'price'],
            'rows': [
                {'id': 1, 'name': 'Product 1', 'price': 10.99},  # Different from None
                {'id': 2, 'name': None, 'price': 20.50}  # Same None value
            ],
            'total_rows': 2
        }

        # Compare data
        result = compare_data(data1, data2, ['id', 'name', 'price'])

        # Assertions
        self.assertEqual(result['summary']['rows_with_differences'], 1)
        self.assertEqual(len(result['data_differences']), 1)
        
        # Check differences
        self.assertEqual(result['data_differences'][0]['row'], 1)
        self.assertEqual(result['data_differences'][0]['differences']['price']['source'], 'None')
        self.assertEqual(result['data_differences'][0]['differences']['price']['target'], '10.99')

    def test_compare_data_no_common_columns(self):
        """Test comparing data with no common columns."""
        # Create data sets with no common columns
        data1 = {
            'columns': ['id', 'name'],
            'rows': [
                {'id': 1, 'name': 'Product 1'},
                {'id': 2, 'name': 'Product 2'}
            ],
            'total_rows': 2
        }
        
        data2 = {
            'columns': ['code', 'price'],
            'rows': [
                {'code': 'A001', 'price': 10.99},
                {'code': 'A002', 'price': 20.50}
            ],
            'total_rows': 2
        }

        # Compare data with no common columns
        result = compare_data(data1, data2, [])

        # Assertions
        self.assertEqual(result['summary']['source_total_rows'], 2)
        self.assertEqual(result['summary']['target_total_rows'], 2)
        self.assertEqual(result['summary']['total_rows_compared'], 0)
        self.assertEqual(result['summary']['rows_with_differences'], 0)
        self.assertEqual(len(result['summary']['columns_compared']), 0)
        self.assertEqual(len(result['data_differences']), 0)

    def test_compare_data_subset_of_columns(self):
        """Test comparing data with a subset of columns."""
        # Create data sets with all columns
        data1 = {
            'columns': ['id', 'name', 'price', 'category'],
            'rows': [
                {'id': 1, 'name': 'Product 1', 'price': 10.99, 'category': 'A'},
                {'id': 2, 'name': 'Product 2', 'price': 20.50, 'category': 'B'}
            ],
            'total_rows': 2
        }
        
        data2 = {
            'columns': ['id', 'name', 'price', 'category'],
            'rows': [
                {'id': 1, 'name': 'Product 1', 'price': 10.99, 'category': 'C'},  # Different category
                {'id': 2, 'name': 'Different Name', 'price': 20.50, 'category': 'B'}  # Different name
            ],
            'total_rows': 2
        }

        # Compare only id and price columns
        result = compare_data(data1, data2, ['id', 'price'])

        # Assertions
        self.assertEqual(result['summary']['rows_with_differences'], 0)  # No differences in id and price
        self.assertEqual(len(result['data_differences']), 0)
        self.assertEqual(len(result['summary']['columns_compared']), 2)
        self.assertIn('id', result['summary']['columns_compared'])
        self.assertIn('price', result['summary']['columns_compared'])

    def test_compare_data_with_complex_differences(self):
        """Test comparing data with complex type differences using DeepDiff."""
        # Create data sets with different types and structures
        data1 = {
            'columns': ['id', 'name', 'metadata', 'tags', 'created_at'],
            'rows': [
                {
                    'id': 1, 
                    'name': 'Product 1', 
                    'metadata': {'version': '1.0', 'category': 'electronics'},
                    'tags': ['sale', 'new'],
                    'created_at': '2023-01-01'
                },
                {
                    'id': 2, 
                    'name': 'Product 2',
                    'metadata': {'version': '2.0', 'category': 'clothing'},
                    'tags': ['premium', 'limited'],
                    'created_at': '2023-02-15'
                }
            ],
            'total_rows': 2
        }
        
        data2 = {
            'columns': ['id', 'name', 'metadata', 'tags', 'created_at'],
            'rows': [
                {
                    'id': 1, 
                    'name': 'Product 1', 
                    'metadata': {'version': '1.1', 'category': 'electronics'},  # Version changed
                    'tags': ['sale', 'new', 'clearance'],  # Added tag
                    'created_at': '2023-01-01'
                },
                {
                    'id': 2, 
                    'name': 'Product 2',
                    'metadata': {'version': 2.0, 'category': 'apparel'},  # Type changed to number, category name changed
                    'tags': ['premium'],  # Removed tag
                    'created_at': '2023-02-15'
                }
            ],
            'total_rows': 2
        }

        # Compare data
        result = compare_data(data1, data2, ['id', 'name', 'metadata', 'tags', 'created_at'])

        # Assertions
        self.assertEqual(result['summary']['source_total_rows'], 2)
        self.assertEqual(result['summary']['target_total_rows'], 2)
        self.assertEqual(result['summary']['total_rows_compared'], 2)
        
        # DeepDiff should detect the differences in both rows
        self.assertEqual(result['summary']['rows_with_differences'], 2)
        
        # First row - check for differences
        row1_diff = next((d for d in result['data_differences'] if d['row'] == 1), None)
        self.assertIsNotNone(row1_diff)
        
        # Second row - check for differences
        row2_diff = next((d for d in result['data_differences'] if d['row'] == 2), None)
        self.assertIsNotNone(row2_diff)
        
        # Make sure we found metadata differences
        self.assertTrue(
            any('metadata' in key for key in row1_diff['differences'].keys()) or
            'metadata' in row1_diff['differences']
        )
        
        # Make sure we found tags differences
        self.assertTrue(
            any('tags' in key for key in row1_diff['differences'].keys()) or
            'tags' in row1_diff['differences']
        )

if __name__ == '__main__':
    unittest.main()
