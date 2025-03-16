#!/usr/bin/env python
"""
CORAL - Database Comparison Tool
A web application for comparing schemas and data between database connections.
"""
import os
import secrets
import pandas as pd
import numpy as np
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SelectMultipleField, SubmitField, widgets
from wtforms.validators import DataRequired, Length
from werkzeug.security import generate_password_hash, check_password_hash

# Import pymssql for database connections
import pymssql

# Import the blueprints
from app.routes.connections import connections_bp
from app.routes.main import main_bp
from app.routes.comparison import comparison_bp

# Set up Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)

# Register blueprints
app.register_blueprint(connections_bp)
app.register_blueprint(main_bp)
app.register_blueprint(comparison_bp)

# Database connection class
class DatabaseConnection:
    def __init__(self, server, database, username, password):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Connect to the database using pymssql"""
        try:
            self.connection = pymssql.connect(
                server=self.server,
                user=self.username,
                password=self.password,
                database=self.database
            )
            self.cursor = self.connection.cursor()
            return True
        except Exception as e:
            print(f"Error connecting with pymssql: {e}")
            return False
    
    def disconnect(self):
        """Close the database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def get_tables(self):
        """Get all tables in the database"""
        query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE' 
        ORDER BY TABLE_NAME
        """
        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_table_schema(self, table_name):
        """Get schema information for a table"""
        # Get column information
        query = """
        SELECT 
            c.COLUMN_NAME, 
            c.DATA_TYPE,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.NUMERIC_PRECISION,
            c.NUMERIC_SCALE,
            c.IS_NULLABLE,
            COLUMNPROPERTY(OBJECT_ID(c.TABLE_SCHEMA + '.' + c.TABLE_NAME), c.COLUMN_NAME, 'IsIdentity') as IS_IDENTITY,
            CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END AS IS_PRIMARY_KEY
        FROM 
            INFORMATION_SCHEMA.COLUMNS c
        LEFT JOIN (
            SELECT 
                ku.TABLE_CATALOG,
                ku.TABLE_SCHEMA,
                ku.TABLE_NAME,
                ku.COLUMN_NAME
            FROM 
                INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS ku
                    ON tc.CONSTRAINT_TYPE = 'PRIMARY KEY' 
                    AND tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
        ) pk ON 
            c.TABLE_CATALOG = pk.TABLE_CATALOG
            AND c.TABLE_SCHEMA = pk.TABLE_SCHEMA
            AND c.TABLE_NAME = pk.TABLE_NAME
            AND c.COLUMN_NAME = pk.COLUMN_NAME
        WHERE 
            c.TABLE_NAME = %s
        ORDER BY 
            c.ORDINAL_POSITION
        """
        
        self.cursor.execute(query, (table_name,))
        columns = []
        for row in self.cursor.fetchall():
            column = {
                'name': row[0],
                'type': row[1],
                'max_length': row[2] if row[2] is not None else 0,
                'numeric_precision': row[3],
                'numeric_scale': row[4],
                'is_nullable': 'Yes' if row[5] == 'YES' else 'No',
                'is_identity': 'Yes' if row[6] == 1 else 'No',
                'is_primary_key': 'Yes' if row[7] == 1 else 'No'
            }
            
            # Format data type with precision/scale/length
            if column['type'] in ('varchar', 'nvarchar', 'char', 'nchar'):
                if column['max_length'] == -1:
                    column['formatted_data_type'] = f"{column['type']}(MAX)"
                else:
                    column['formatted_data_type'] = f"{column['type']}({column['max_length']})"
            elif column['type'] in ('decimal', 'numeric'):
                column['formatted_data_type'] = f"{column['type']}({column['numeric_precision']},{column['numeric_scale']})"
            else:
                column['formatted_data_type'] = column['type']
                
            columns.append(column)
        
        return columns
    
    def get_table_data(self, table_name, columns=None, limit=50):
        """Get sample data from a table with optional column selection"""
        if columns:
            column_list = ", ".join([f"[{col}]" for col in columns])
        else:
            column_list = "*"
            
        query = f"SELECT TOP {limit} {column_list} FROM [{table_name}]"
        
        try:
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            
            # Get column names
            if columns:
                column_names = columns
            else:
                column_names = [column[0] for column in self.cursor.description]
                
            # Convert to list of dicts for easier processing
            result = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(column_names):
                    row_dict[col] = row[i]
                result.append(row_dict)
                
            return {
                'columns': column_names,
                'rows': result,
                'total_rows': len(result)
            }
        except Exception as e:
            print(f"Error fetching data: {e}")
            return {
                'columns': [],
                'rows': [],
                'total_rows': 0
            }
    
    def get_row_count(self, table_name):
        """Get the total number of rows in a table"""
        query = f"SELECT COUNT(*) FROM [{table_name}]"
        try:
            self.cursor.execute(query)
            return self.cursor.fetchone()[0]
        except Exception as e:
            print(f"Error getting row count: {e}")
            return 0

# Forms
class ConnectionForm(FlaskForm):
    connection_name = StringField('Connection Name', validators=[DataRequired(), Length(min=1, max=50)])
    server = StringField('Server', validators=[DataRequired()])
    database = StringField('Database', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class DatabaseSelectionForm(FlaskForm):
    connection1 = SelectField('Source Connection', validators=[DataRequired()])
    connection2 = SelectField('Target Connection', validators=[DataRequired()])
    submit = SubmitField('Compare Databases')

class TableSelectionForm(FlaskForm):
    table1 = SelectField('Source Table', validators=[DataRequired()])
    table2 = SelectField('Target Table', validators=[DataRequired()])

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class ColumnSelectionForm(FlaskForm):
    columns = MultiCheckboxField('Columns to Compare')
    compare_data = BooleanField('Compare Data', default=True)

# Helper functions
def compare_schemas(schema1, schema2):
    """Compare two table schemas and return differences"""
    # Extract column names from each schema
    columns1 = [col['name'] for col in schema1]
    columns2 = [col['name'] for col in schema2]
    
    # Find common columns and columns only in one schema
    common_columns = list(set(columns1) & set(columns2))
    only_in_schema1 = list(set(columns1) - set(columns2))
    only_in_schema2 = list(set(columns2) - set(columns1))
    
    # Compare properties of common columns
    differences = []
    for col_name in common_columns:
        col1 = next((col for col in schema1 if col['name'] == col_name), None)
        col2 = next((col for col in schema2 if col['name'] == col_name), None)
        
        if col1 and col2:
            col_diffs = []
            
            # Check data type
            if col1['formatted_data_type'] != col2['formatted_data_type']:
                col_diffs.append(f"Data type: {col1['formatted_data_type']} vs {col2['formatted_data_type']}")
            
            # Check nullability
            if col1['is_nullable'] != col2['is_nullable']:
                col_diffs.append(f"Nullable: {col1['is_nullable']} vs {col2['is_nullable']}")
            
            # Check identity
            if col1['is_identity'] != col2['is_identity']:
                col_diffs.append(f"Identity: {col1['is_identity']} vs {col2['is_identity']}")
            
            # Check primary key
            if col1['is_primary_key'] != col2['is_primary_key']:
                col_diffs.append(f"Primary Key: {col1['is_primary_key']} vs {col2['is_primary_key']}")
            
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

def compare_data(data1, data2, common_columns):
    """Compare data between two tables"""
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
        row_diffs = {}
        
        for col in columns_to_compare:
            # Handle NaN values
            val1 = df1_subset.iloc[i][col]
            val2 = df2_subset.iloc[i][col]
            
            # Convert numpy NaN to None for comparison
            if isinstance(val1, float) and np.isnan(val1):
                val1 = None
            if isinstance(val2, float) and np.isnan(val2):
                val2 = None
                
            # Compare values
            if val1 != val2:
                row_diffs[col] = {
                    'source': str(val1),
                    'target': str(val2)
                }
        
        if row_diffs:
            differences.append({
                'row': i + 1,  # 1-based indexing for display
                'differences': row_diffs
            })
            rows_with_differences += 1
    
    # Create summary
    summary = {
        'source_total_rows': data1['total_rows'],
        'target_total_rows': data2['total_rows'],
        'total_rows_compared': min_rows,
        'rows_with_differences': rows_with_differences,
        'columns_compared': columns_to_compare,
        'row_count_difference': abs(data1['total_rows'] - data2['total_rows'])
    }
    
    return {
        'summary': summary,
        'data_differences': differences
    }

def format_data_as_html(data):
    """Format data as an HTML table"""
    if not data or not data['columns'] or not data['rows']:
        return "<div class='alert alert-warning'>No data available</div>"
    
    html = "<table class='table table-sm table-striped'>"
    
    # Header
    html += "<thead><tr>"
    for col in data['columns']:
        html += f"<th>{col}</th>"
    html += "</tr></thead>"
    
    # Body
    html += "<tbody>"
    for row in data['rows']:
        html += "<tr>"
        for col in data['columns']:
            value = row.get(col, '')
            if value is None:
                value = '<em>NULL</em>'
            html += f"<td>{value}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    
    return html

if __name__ == '__main__':
    app.run(debug=True, port=5007, use_reloader=True, reloader_type='stat')
