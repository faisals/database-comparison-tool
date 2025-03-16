"""
Utility functions for database comparison.
"""
import pandas as pd
import numpy as np
from deepdiff import DeepDiff
import difflib
import html

def compare_schemas(schema1, schema2):
    """Compare two table schemas and return differences using DeepDiff"""
    # Extract column names from each schema
    columns1 = [col['name'] for col in schema1]
    columns2 = [col['name'] for col in schema2]
    
    # Find common columns and columns only in one schema
    common_columns = list(set(columns1) & set(columns2))
    only_in_schema1 = list(set(columns1) - set(columns2))
    only_in_schema2 = list(set(columns2) - set(columns1))
    
    # Create dictionaries for comparison (using column name as key)
    schema1_dict = {col['name']: col for col in schema1}
    schema2_dict = {col['name']: col for col in schema2}
    
    # Filter for common columns only
    schema1_common = {k: v for k, v in schema1_dict.items() if k in common_columns}
    schema2_common = {k: v for k, v in schema2_dict.items() if k in common_columns}
    
    # Compare with DeepDiff for more detailed comparison
    diff = DeepDiff(schema1_common, schema2_common, verbose_level=2)
    
    # Process differences into our existing format
    differences = []
    for col_name in common_columns:
        col1 = schema1_dict.get(col_name)
        col2 = schema2_dict.get(col_name)
        
        # Extract differences for this column
        col_diffs = []
        
        # Check for critical properties first to maintain backward compatibility
        # This is important to ensure we match the expectations of existing tests
        if col1['formatted_data_type'] != col2['formatted_data_type']:
            col_diffs.append(f"Data type: {col1['formatted_data_type']} vs {col2['formatted_data_type']}")
        
        if col1['is_nullable'] != col2['is_nullable']:
            col_diffs.append(f"Nullable: {col1['is_nullable']} vs {col2['is_nullable']}")
        
        if col1['is_identity'] != col2['is_identity']:
            col_diffs.append(f"Identity: {col1['is_identity']} vs {col2['is_identity']}")
        
        if col1['is_primary_key'] != col2['is_primary_key']:
            col_diffs.append(f"Primary Key: {col1['is_primary_key']} vs {col2['is_primary_key']}")
        
        # Now add other differences from DeepDiff that we didn't already capture
        # Check for type changes
        type_changes = diff.get('type_changes', {})
        for path, change in type_changes.items():
            if path.startswith(f"root['{col_name}']"):
                prop = path.split("']['")[-1].rstrip("']")
                # Skip properties we already checked above
                if prop not in ['formatted_data_type', 'is_nullable', 'is_identity', 'is_primary_key']:
                    col_diffs.append(f"{prop}: {change['old_value']} vs {change['new_value']}")
        
        # Check for value changes
        value_changes = diff.get('values_changed', {})
        for path, change in value_changes.items():
            if path.startswith(f"root['{col_name}']"):
                prop = path.split("']['")[-1].rstrip("']")
                # Skip properties we already checked above
                if prop not in ['formatted_data_type', 'is_nullable', 'is_identity', 'is_primary_key']:
                    col_diffs.append(f"{prop}: {change['old_value']} vs {change['new_value']}")
        
        # Also check for nested changes that DeepDiff can detect
        for change_type in ['dictionary_item_added', 'dictionary_item_removed', 'iterable_item_added', 'iterable_item_removed']:
            changes = diff.get(change_type, {})
            for path in changes:
                if path.startswith(f"root['{col_name}']"):
                    parts = path.replace(f"root['{col_name}']", "").strip("[]'")
                    col_diffs.append(f"Structure change: {change_type} at {parts}")
        
        if col_diffs:
            differences.append({
                'column_name': col_name,
                'source': col1,
                'target': col2,
                'differences': col_diffs
            })
    
    # Calculate totals
    total_columns_schema1 = len(columns1)
    total_columns_schema2 = len(columns2)
    identical_columns = len(common_columns) - len(differences)
    
    return {
        'common_columns': common_columns,
        'only_in_source': only_in_schema1,
        'only_in_target': only_in_schema2,
        'differences': differences,
        'total_columns_schema1': total_columns_schema1,
        'total_columns_schema2': total_columns_schema2,
        'identical_columns': identical_columns
    }

def compare_create_table_scripts(script1, script2):
    """
    Compare two CREATE TABLE scripts and return a unified diff with HTML formatting
    
    Args:
        script1 (str): The first CREATE TABLE script (source)
        script2 (str): The second CREATE TABLE script (target)
        
    Returns:
        dict: Dictionary containing the comparison results
            - has_differences (bool): Whether there are differences between the scripts
            - diff_html (str): HTML-formatted unified diff
            - source_script (str): Original source script
            - target_script (str): Original target script
    """
    # Split scripts into lines for comparison
    script1_lines = script1.splitlines()
    script2_lines = script2.splitlines()
    
    # Generate unified diff
    diff = difflib.unified_diff(
        script1_lines, 
        script2_lines,
        fromfile='Source Database',
        tofile='Target Database',
        lineterm=''
    )
    
    # Convert diff to list and check if there are differences
    diff_list = list(diff)
    has_differences = len(diff_list) > 0
    
    # Format diff as HTML
    diff_html = []
    for line in diff_list:
        if line.startswith('+'):
            # Added line (in target, not in source)
            formatted_line = f'<div class="diff-line diff-added">{html.escape(line)}</div>'
        elif line.startswith('-'):
            # Removed line (in source, not in target)
            formatted_line = f'<div class="diff-line diff-removed">{html.escape(line)}</div>'
        elif line.startswith('@@'):
            # Diff header
            formatted_line = f'<div class="diff-line diff-header">{html.escape(line)}</div>'
        elif line.startswith('---') or line.startswith('+++'):
            # File header
            formatted_line = f'<div class="diff-line diff-file-header">{html.escape(line)}</div>'
        else:
            # Context line (unchanged)
            formatted_line = f'<div class="diff-line diff-context">{html.escape(line)}</div>'
        
        diff_html.append(formatted_line)
    
    # Join HTML lines
    diff_html_str = '\n'.join(diff_html)
    
    return {
        'has_differences': has_differences,
        'diff_html': diff_html_str,
        'source_script': script1,
        'target_script': script2
    }

def compare_data(data1, data2, common_columns):
    """Compare data between two tables using DeepDiff for more detailed comparison"""
    # Create DataFrames from the data
    df1 = pd.DataFrame(data1['rows'])
    df2 = pd.DataFrame(data2['rows'])
    
    # Only compare columns that exist in both tables
    columns_to_compare = [col for col in common_columns if col in df1.columns and col in df2.columns]
    
    # If no common columns, return empty comparison
    if not columns_to_compare:
        return {
            'summary': {
                'source_total_rows': data1['total_rows'],
                'target_total_rows': data2['total_rows'],
                'total_rows_compared': 0,
                'rows_with_differences': 0,
                'columns_compared': [],
                'row_count_difference': abs(data1['total_rows'] - data2['total_rows'])
            },
            'data_differences': []
        }
    
    # Limit DataFrames to common columns
    df1_subset = df1[columns_to_compare]
    df2_subset = df2[columns_to_compare]
    
    # Find differences
    differences = []
    rows_with_differences = 0
    
    # Compare rows (up to the minimum number of rows in both datasets)
    min_rows = min(len(df1_subset), len(df2_subset))
    
    for i in range(min_rows):
        row1 = df1_subset.iloc[i].to_dict()
        row2 = df2_subset.iloc[i].to_dict()
        
        # Clean NaN values for proper comparison
        for col in columns_to_compare:
            if col in row1 and isinstance(row1[col], float) and np.isnan(row1[col]):
                row1[col] = None
            if col in row2 and isinstance(row2[col], float) and np.isnan(row2[col]):
                row2[col] = None
        
        # Use DeepDiff to compare the rows
        row_diff = DeepDiff(row1, row2, verbose_level=2)
        
        if row_diff:
            row_diffs = {}
            
            # First do a simple comparison for backward compatibility with tests
            for col in columns_to_compare:
                val1 = row1.get(col)
                val2 = row2.get(col)
                
                if val1 != val2:
                    row_diffs[col] = {
                        'source': 'None' if val1 is None else str(val1),
                        'target': 'None' if val2 is None else str(val2)
                    }
            
            # For complex nested structures, get detailed differences from DeepDiff
            for change_type, changes in row_diff.items():
                if change_type in ['values_changed', 'type_changes']:
                    for path, change in changes.items():
                        # Process path to extract column and possibly nested keys
                        path_parts = path.split("['")
                        if len(path_parts) >= 2:
                            col_name = path_parts[1].split("']")[0]
                            # For complex nested structures, provide more detail
                            if "']" in path and path.count("'") > 3:  # This is a nested path
                                nested_key = path.split("']['")[1].rstrip("']")
                                col_key = f"{col_name}['{nested_key}'"
                                row_diffs[col_key] = {
                                    'source': str(change.get('old_value', 'None')),
                                    'target': str(change.get('new_value', 'None'))
                                }
            
            # For items added/removed in nested structures
            for change_type in ['dictionary_item_added', 'iterable_item_added']:
                for path in row_diff.get(change_type, {}):
                    if "root['" in path:
                        col_key = path.replace("root['", "").rstrip("']")
                        if col_key not in row_diffs:
                            row_diffs[col_key] = {
                                'source': 'None',
                                'target': 'N/A'
                            }
            
            for change_type in ['dictionary_item_removed', 'iterable_item_removed']:
                for path in row_diff.get(change_type, {}):
                    if "root['" in path:
                        col_key = path.replace("root['", "").rstrip("']")
                        if col_key not in row_diffs:
                            row_diffs[col_key] = {
                                'source': 'N/A',
                                'target': 'None'
                            }
            
            if row_diffs:
                differences.append({
                    'row_index': i,
                    'differences': row_diffs
                })
                rows_with_differences += 1
    
    return {
        'summary': {
            'source_total_rows': data1['total_rows'],
            'target_total_rows': data2['total_rows'],
            'total_rows_compared': min_rows,
            'rows_with_differences': rows_with_differences,
            'columns_compared': columns_to_compare,
            'row_count_difference': abs(data1['total_rows'] - data2['total_rows'])
        },
        'data_differences': differences
    }
