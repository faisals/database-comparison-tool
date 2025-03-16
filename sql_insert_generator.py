#!/usr/bin/env python
"""
SQL Insert Generator - A CLI tool to generate INSERT statements for SQL Server database tables.
"""
import argparse
import csv
import json
import os
import sys
import random
import string
import getpass
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Union

# Try to import pyodbc, but make it optional
try:
    import pyodbc
    PYODBC_AVAILABLE = True
    DB_DRIVER = "pyodbc"
except ImportError:
    PYODBC_AVAILABLE = False
    # Try to import pymssql as an alternative
    try:
        import pymssql
        PYMSSQL_AVAILABLE = True
        DB_DRIVER = "pymssql"
    except ImportError:
        PYMSSQL_AVAILABLE = False
        DB_DRIVER = None
        print("Warning: Neither pyodbc nor pymssql modules are available. Running in schema-only mode.")
        print("To enable database connectivity, install either pyodbc or pymssql:")
        print("\nOption 1 (pyodbc - recommended):")
        print("  For Mac users (especially M1/M2 chips):")
        print("  1. Install unixODBC: brew install unixodbc")
        print("  2. Install SQL Server driver: brew install msodbcsql17")
        print("  3. Install pyodbc: pip install pyodbc")
        print("\nOption 2 (pymssql - alternative):")
        print("  pip install pymssql")
        print("\nIf you encounter issues on Apple Silicon (M1/M2) with pyodbc:")
        print("  Try using Rosetta 2 with x86_64 architecture:")
        print("  CONDA_SUBDIR=osx-64 conda create -n pyodbc_env python=3.9")
        print("  conda activate pyodbc_env")
        print("  conda config --env --set subdir osx-64")
        print("  conda install -c conda-forge pyodbc")

class SQLInsertGenerator:
    """Generate INSERT statements for SQL Server database tables."""
    
    def __init__(self, connection_string: Optional[str] = None, server: Optional[str] = None, 
                 database: Optional[str] = None, username: Optional[str] = None, 
                 password: Optional[str] = None, trusted_connection: bool = False,
                 connection_name: Optional[str] = None):
        """Initialize the generator with connection details."""
        self.connection_string = connection_string
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.trusted_connection = trusted_connection
        self.connection_name = connection_name
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Connect to the SQL Server database."""
        if not (PYODBC_AVAILABLE or PYMSSQL_AVAILABLE):
            print("Neither pyodbc nor pymssql is available, cannot connect to database.")
            return False

        try:
            if DB_DRIVER == "pyodbc":
                if self.connection_string:
                    conn_str = self.connection_string
                else:
                    if self.trusted_connection:
                        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE={self.database};Trusted_Connection=yes;"
                    else:
                        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password}"
                
                self.connection = pyodbc.connect(conn_str)
                self.cursor = self.connection.cursor()
                return True
            elif DB_DRIVER == "pymssql":
                # pymssql uses different connection parameters
                if self.connection_string:
                    # Connection string not directly supported by pymssql
                    # Extract parameters from connection string if possible
                    print("Warning: Connection string format not directly supported by pymssql.")
                    print("Using server, database, username and password parameters instead.")
                
                if self.trusted_connection:
                    self.connection = pymssql.connect(
                        server=self.server,
                        database=self.database,
                        trusted=True
                    )
                else:
                    self.connection = pymssql.connect(
                        server=self.server,
                        database=self.database,
                        user=self.username,
                        password=self.password
                    )
                self.cursor = self.connection.cursor(as_dict=True)
                return True
        except Exception as e:
            error_type = "pyodbc" if DB_DRIVER == "pyodbc" else "pymssql"
            print(f"Error connecting to database using {error_type}: {e}", file=sys.stderr)
            return False
    
    def disconnect(self):
        """Close the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get the schema for a specific table."""
        if not self.cursor:
            raise ValueError("Not connected to database")
        
        # Get column information
        columns_query = f"""
        SELECT 
            c.name AS column_name,
            t.name AS data_type,
            c.max_length,
            c.precision,
            c.scale,
            c.is_nullable,
            c.is_identity,
            ISNULL(i.is_primary_key, 0) AS is_primary_key
        FROM 
            sys.columns c
        INNER JOIN 
            sys.types t ON c.user_type_id = t.user_type_id
        LEFT JOIN 
            (SELECT 
                ic.column_id, 
                ic.object_id,
                1 AS is_primary_key
             FROM 
                sys.indexes i
             INNER JOIN 
                sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
             WHERE 
                i.is_primary_key = 1
            ) i ON c.object_id = i.object_id AND c.column_id = i.column_id
        WHERE 
            c.object_id = OBJECT_ID(?)
        ORDER BY 
            c.column_id
        """
        
        try:
            if DB_DRIVER == "pyodbc":
                self.cursor.execute(columns_query, (table_name,))
                columns = []
                for row in self.cursor.fetchall():
                    column = {
                        'name': row.column_name,
                        'type': row.data_type,
                        'max_length': row.max_length,
                        'precision': row.precision,
                        'scale': row.scale,
                        'is_nullable': row.is_nullable,
                        'is_identity': row.is_identity,
                        'is_primary_key': row.is_primary_key
                    }
                    columns.append(column)
            elif DB_DRIVER == "pymssql":
                # pymssql uses ? placeholders differently, need to use %s instead
                pymssql_query = columns_query.replace("?", "%s")
                self.cursor.execute(pymssql_query, (table_name,))
                columns = []
                for row in self.cursor.fetchall():
                    # row is already a dict when using as_dict=True
                    column = {
                        'name': row['column_name'],
                        'type': row['data_type'],
                        'max_length': row['max_length'],
                        'precision': row['precision'],
                        'scale': row['scale'],
                        'is_nullable': row['is_nullable'],
                        'is_identity': row['is_identity'],
                        'is_primary_key': row['is_primary_key']
                    }
                    columns.append(column)
            else:
                print("No database driver available, cannot get table schema.")
                return []
                
            if not columns:
                print(f"Table '{table_name}' not found or has no columns.", file=sys.stderr)
                return []
                
            return columns
        except Exception as e:
            error_type = "pyodbc" if DB_DRIVER == "pyodbc" else "pymssql"
            print(f"Error getting table schema using {error_type}: {e}", file=sys.stderr)
            return []
    
    def generate_random_value(self, column: Dict[str, Any]) -> Any:
        """Generate a random value based on column type."""
        data_type = column['type'].lower()
        
        # Handle nullable columns
        if column['is_nullable'] and random.random() < 0.1:  # 10% chance of NULL for nullable columns
            return None
            
        # Identity columns are typically auto-generated
        if column['is_identity']:
            return None
            
        # Generate appropriate random values based on data type
        if data_type in ('char', 'varchar', 'nvarchar', 'nchar', 'text', 'ntext'):
            max_length = min(column['max_length'], 50)  # Limit to 50 chars for readability
            if data_type.startswith('n'):  # Unicode types have length in bytes (2 per char)
                max_length = max_length // 2
            length = random.randint(1, max(1, max_length))
            return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
            
        elif data_type in ('int', 'bigint', 'smallint', 'tinyint'):
            ranges = {
                'tinyint': (0, 255),
                'smallint': (-32768, 32767),
                'int': (-2147483648, 2147483647),
                'bigint': (-9223372036854775808, 9223372036854775807)
            }
            min_val, max_val = ranges.get(data_type, (-1000, 1000))
            return random.randint(min_val, max_val)
            
        elif data_type in ('decimal', 'numeric', 'money', 'smallmoney', 'float', 'real'):
            precision = column['precision'] or 10
            scale = column['scale'] or 2
            max_val = 10 ** (precision - scale) - 1
            return round(random.uniform(0, max_val), scale)
            
        elif data_type in ('bit', 'boolean'):
            return random.choice([0, 1])
            
        elif data_type in ('date', 'datetime', 'datetime2', 'smalldatetime'):
            # Random date between 2000-01-01 and 2025-12-31
            year = random.randint(2000, 2025)
            month = random.randint(1, 12)
            day = random.randint(1, 28)  # Using 28 to avoid month/day validation issues
            return date(year, month, day)
            
        elif data_type in ('time'):
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            return f"{hour:02d}:{minute:02d}:{second:02d}"
            
        elif data_type in ('uniqueidentifier', 'guid'):
            return f"{{{format(random.randint(0, 0xffffffff), '08x')}-{format(random.randint(0, 0xffff), '04x')}-" \
                   f"{format(random.randint(0, 0xffff), '04x')}-{format(random.randint(0, 0xffff), '04x')}-" \
                   f"{format(random.randint(0, 0xffffffffffff), '012x')}}}"
                   
        # Default for unsupported types
        return "NULL"
    
    def format_value_for_sql(self, value: Any, column: Dict[str, Any]) -> str:
        """Format a value for use in an SQL INSERT statement."""
        if value is None:
            return "NULL"
            
        data_type = column['type'].lower()
        
        # String types need quotes and escaping
        if data_type in ('char', 'varchar', 'nvarchar', 'nchar', 'text', 'ntext'):
            # Escape single quotes by doubling them
            escaped_value = str(value).replace("'", "''")
            return f"'{escaped_value}'"
            
        # Date/time types need formatting
        elif data_type in ('date', 'datetime', 'datetime2', 'smalldatetime'):
            if isinstance(value, (datetime, date)):
                return f"'{value.isoformat()}'"
            return f"'{value}'"
            
        elif data_type == 'time':
            return f"'{value}'"
            
        # GUID/uniqueidentifier
        elif data_type in ('uniqueidentifier', 'guid'):
            return f"'{value}'"
            
        # Bit values
        elif data_type in ('bit', 'boolean'):
            return "1" if value else "0"
            
        # Numeric types can be used as-is
        return str(value)
    
    def generate_insert_statement(self, table_name: str, data: List[Dict[str, Any]], 
                                  columns: List[Dict[str, Any]]) -> str:
        """Generate an INSERT statement for the given table and data."""
        # Filter out identity columns
        non_identity_columns = [col for col in columns if not col['is_identity']]
        column_names = [col['name'] for col in non_identity_columns]
        
        # Start building the INSERT statement
        insert_stmt = f"INSERT INTO {table_name} ({', '.join(column_names)})\nVALUES\n"
        
        # Add each row of values
        rows = []
        for row_data in data:
            values = []
            for col in non_identity_columns:
                col_name = col['name']
                if col_name in row_data:
                    values.append(self.format_value_for_sql(row_data[col_name], col))
                else:
                    values.append("NULL")
            rows.append(f"({', '.join(values)})")
        
        insert_stmt += ',\n'.join(rows) + ";"
        return insert_stmt
    
    def generate_random_data(self, columns: List[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
        """Generate random data for the specified columns."""
        data = []
        for _ in range(count):
            row = {}
            for col in columns:
                row[col['name']] = self.generate_random_value(col)
            data.append(row)
        return data
    
    def load_data_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load data from a CSV or JSON file."""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.json':
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON file: {e}", file=sys.stderr)
                return []
                
        elif file_ext == '.csv':
            try:
                with open(file_path, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    return list(reader)
            except Exception as e:
                print(f"Error reading CSV file: {e}", file=sys.stderr)
                return []
                
        else:
            print(f"Unsupported file format: {file_ext}", file=sys.stderr)
            return []
    
    def generate_inserts(self, table_name: str, row_count: int = 1, 
                         output_file: Optional[str] = None, 
                         input_file: Optional[str] = None,
                         mock_schema: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate INSERT statements for the specified table."""
        # Get table schema
        if mock_schema:
            columns = mock_schema
        else:
            columns = self.get_table_schema(table_name)
        
        if not columns:
            return ""
        
        # Get data
        if input_file:
            data = self.load_data_from_file(input_file)
            if not data:
                return ""
        else:
            data = self.generate_random_data(columns, row_count)
        
        # Generate INSERT statement
        insert_stmt = self.generate_insert_statement(table_name, data, columns)
        
        # Write to file if specified
        if output_file:
            try:
                with open(output_file, 'w') as f:
                    f.write(insert_stmt)
                print(f"INSERT statement written to {output_file}")
            except Exception as e:
                print(f"Error writing to file: {e}", file=sys.stderr)
        
        return insert_stmt


class ConnectionManager:
    """Manage saved database connections."""
    
    def __init__(self):
        """Initialize the connection manager."""
        self.config_dir = os.path.join(os.path.expanduser("~"), ".sql_insert_generator")
        self.connections_file = os.path.join(self.config_dir, "connections.json")
        self.ensure_config_dir()
        
    def ensure_config_dir(self):
        """Ensure the configuration directory exists."""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
    def load_connections(self) -> Dict[str, Dict[str, Any]]:
        """Load saved connections from the configuration file."""
        if not os.path.exists(self.connections_file):
            return {}
            
        try:
            with open(self.connections_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Error reading connections file. File may be corrupted.", file=sys.stderr)
            return {}
            
    def save_connection(self, name: str, server: str, database: str, 
                        username: Optional[str] = None, password: Optional[str] = None, 
                        trusted: bool = False,
                        connection_string: Optional[str] = None) -> bool:
        """Save a connection to the configuration file."""
        connections = self.load_connections()
        
        # Create connection data
        connection_data = {
            'server': server,
            'database': database,
            'trusted': trusted
        }
        
        if connection_string:
            connection_data['connection_string'] = connection_string
        elif not trusted:
            connection_data['username'] = username
            # We encrypt the password with a simple encoding - in a real app, use proper encryption
            if password:
                connection_data['password'] = password  # In a real app, encrypt this
                
        connections[name] = connection_data
        
        try:
            with open(self.connections_file, 'w') as f:
                json.dump(connections, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving connection: {e}", file=sys.stderr)
            return False
            
    def delete_connection(self, name: str) -> bool:
        """Delete a saved connection."""
        connections = self.load_connections()
        
        if name not in connections:
            print(f"Connection '{name}' not found.", file=sys.stderr)
            return False
            
        del connections[name]
        
        try:
            with open(self.connections_file, 'w') as f:
                json.dump(connections, f, indent=2)
            return True
        except Exception as e:
            print(f"Error deleting connection: {e}", file=sys.stderr)
            return False
            
    def get_connection(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a saved connection by name."""
        connections = self.load_connections()
        return connections.get(name)
        
    def list_connections(self) -> List[str]:
        """List all saved connections."""
        connections = self.load_connections()
        return list(connections.keys())


class MockSchemaManager:
    """Manage mock table schemas for offline use."""
    
    def __init__(self):
        """Initialize the mock schema manager."""
        self.config_dir = os.path.join(os.path.expanduser("~"), ".sql_insert_generator")
        self.schemas_file = os.path.join(self.config_dir, "schemas.json")
        self.ensure_config_dir()
        
    def ensure_config_dir(self):
        """Ensure the configuration directory exists."""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
    def load_schemas(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load saved schemas from the configuration file."""
        if not os.path.exists(self.schemas_file):
            return {}
            
        try:
            with open(self.schemas_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Error reading schemas file. File may be corrupted.", file=sys.stderr)
            return {}
            
    def save_schema(self, table_name: str, columns: List[Dict[str, Any]]) -> bool:
        """Save a schema to the configuration file."""
        schemas = self.load_schemas()
        schemas[table_name] = columns
        
        try:
            with open(self.schemas_file, 'w') as f:
                json.dump(schemas, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving schema: {e}", file=sys.stderr)
            return False
            
    def delete_schema(self, table_name: str) -> bool:
        """Delete a saved schema."""
        schemas = self.load_schemas()
        
        if table_name not in schemas:
            print(f"Schema for table '{table_name}' not found.", file=sys.stderr)
            return False
            
        del schemas[table_name]
        
        try:
            with open(self.schemas_file, 'w') as f:
                json.dump(schemas, f, indent=2)
            return True
        except Exception as e:
            print(f"Error deleting schema: {e}", file=sys.stderr)
            return False
            
    def get_schema(self, table_name: str) -> Optional[List[Dict[str, Any]]]:
        """Get a saved schema by table name."""
        schemas = self.load_schemas()
        return schemas.get(table_name)
        
    def list_schemas(self) -> List[str]:
        """List all saved schemas."""
        schemas = self.load_schemas()
        return list(schemas.keys())


def create_mock_schema_interactive() -> List[Dict[str, Any]]:
    """Interactive creation of a mock table schema."""
    print("=== Create Mock Table Schema ===")
    
    columns = []
    
    while True:
        print("\nColumn definition:")
        name = safe_input("Column name (leave empty to finish): ")
        if not name:
            break
            
        data_type = safe_input("Data type (e.g., varchar, int, datetime): ").lower()
        
        max_length = 0
        if data_type in ('char', 'varchar', 'nvarchar', 'nchar'):
            max_length_str = safe_input("Max length (default: 50): ")
            max_length = int(max_length_str) if max_length_str.isdigit() else 50
            
        precision = 0
        scale = 0
        if data_type in ('decimal', 'numeric'):
            precision_str = safe_input("Precision (default: 10): ")
            precision = int(precision_str) if precision_str.isdigit() else 10
            
            scale_str = safe_input("Scale (default: 2): ")
            scale = int(scale_str) if scale_str.isdigit() else 2
            
        is_nullable = safe_input("Nullable? (y/n, default: y): ").lower() != 'n'
        is_identity = safe_input("Identity column? (y/n, default: n): ").lower() == 'y'
        is_primary_key = safe_input("Primary key? (y/n, default: n): ").lower() == 'y'
        
        column = {
            'name': name,
            'type': data_type,
            'max_length': max_length,
            'precision': precision,
            'scale': scale,
            'is_nullable': is_nullable,
            'is_identity': is_identity,
            'is_primary_key': is_primary_key
        }
        
        columns.append(column)
        print(f"Added column: {name} ({data_type})")
    
    if not columns:
        print("No columns defined.")
        return []
        
    return columns


def safe_input(prompt: str, default: str = "") -> str:
    """Get input from the user safely, with a default value if stdin is not available."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print(f"\nUsing default: {default}")
        return default


def safe_getpass(prompt: str, default: str = "") -> str:
    """Get password input from the user safely, with a default value if stdin is not available."""
    try:
        return getpass.getpass(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print(f"\nUsing default: {default}")
        return default


def setup_new_connection_interactive(connection_manager: ConnectionManager) -> Optional[Dict[str, Any]]:
    """Interactive setup for a new database connection."""
    print("=== Setup New Database Connection ===")
    
    # Get connection name
    while True:
        name = safe_input("Connection name: ")
        if name:
            break
        print("Connection name cannot be empty.")
    
    # Check if connection with this name already exists
    if connection_manager.get_connection(name):
        overwrite = safe_input(f"Connection '{name}' already exists. Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            return None
    
    # Connection type
    use_conn_string = safe_input("Use connection string? (y/n, default: n): ").lower() == 'y'
    
    if use_conn_string:
        # Connection string
        conn_string = safe_input("Connection string: ")
        if not conn_string:
            print("Connection string cannot be empty.")
            return None
            
        # Extract server and database from connection string if possible
        server = ""
        database = ""
        
        # Simple parsing - in a real app, use a more robust method
        parts = conn_string.split(';')
        for part in parts:
            if part.upper().startswith('SERVER='):
                server = part.split('=', 1)[1]
            elif part.upper().startswith('DATABASE='):
                database = part.split('=', 1)[1]
        
        # Save connection
        if connection_manager.save_connection(
            name=name,
            server=server,
            database=database,
            connection_string=conn_string
        ):
            print(f"Connection '{name}' saved successfully.")
            return {
                'name': name,
                'connection_string': conn_string
            }
        return None
    else:
        # Server
        server = safe_input("Server: ")
        if not server:
            print("Server cannot be empty.")
            return None
            
        # Database
        database = safe_input("Database: ")
        if not database:
            print("Database cannot be empty.")
            return None
            
        # Authentication type
        use_trusted = safe_input("Use Windows authentication? (y/n, default: n): ").lower() == 'y'
        
        if use_trusted:
            # Save connection with Windows authentication
            if connection_manager.save_connection(
                name=name,
                server=server,
                database=database,
                trusted=True
            ):
                print(f"Connection '{name}' saved successfully.")
                return {
                    'name': name,
                    'server': server,
                    'database': database,
                    'trusted': True
                }
            return None
        else:
            # Username
            username = safe_input("Username: ")
            if not username:
                print("Username cannot be empty.")
                return None
                
            # Password
            password = safe_getpass("Password: ")
            if not password:
                print("Password cannot be empty.")
                return None
                
            # Save connection with SQL authentication
            if connection_manager.save_connection(
                name=name,
                server=server,
                database=database,
                username=username,
                password=password,
                trusted=False
            ):
                print(f"Connection '{name}' saved successfully.")
                return {
                    'name': name,
                    'server': server,
                    'database': database,
                    'username': username,
                    'password': password,
                    'trusted': False
                }
            return None


def setup_new_connection_noninteractive(connection_manager: ConnectionManager, 
                                        name: str, server: str, database: str,
                                        username: Optional[str] = None, 
                                        password: Optional[str] = None,
                                        trusted: bool = False,
                                        connection_string: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Non-interactive setup for a new database connection."""
    # Check if connection with this name already exists
    if connection_manager.get_connection(name):
        print(f"Connection '{name}' already exists. Use --force to overwrite.")
        return None
    
    if connection_string:
        # Save connection with connection string
        if connection_manager.save_connection(
            name=name,
            server=server,
            database=database,
            connection_string=connection_string
        ):
            print(f"Connection '{name}' saved successfully.")
            return {
                'name': name,
                'connection_string': connection_string
            }
    elif trusted:
        # Save connection with Windows authentication
        if connection_manager.save_connection(
            name=name,
            server=server,
            database=database,
            trusted=True
        ):
            print(f"Connection '{name}' saved successfully.")
            return {
                'name': name,
                'server': server,
                'database': database,
                'trusted': True
            }
    else:
        # Save connection with SQL authentication
        if not username or not password:
            print("Username and password are required for SQL Server authentication.")
            return None
            
        if connection_manager.save_connection(
            name=name,
            server=server,
            database=database,
            username=username,
            password=password,
            trusted=False
        ):
            print(f"Connection '{name}' saved successfully.")
            return {
                'name': name,
                'server': server,
                'database': database,
                'username': username,
                'password': password,
                'trusted': False
            }
    
    return None


def parse_args(return_parser=False):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate INSERT statements for SQL Server tables')
    
    # Connection options
    conn_group = parser.add_argument_group('Connection Options')
    conn_group.add_argument('--connection-string', help='Full connection string')
    conn_group.add_argument('--server', help='SQL Server instance name')
    conn_group.add_argument('--database', help='Database name')
    conn_group.add_argument('--username', help='SQL Server username')
    conn_group.add_argument('--password', help='SQL Server password')
    conn_group.add_argument('--trusted', action='store_true', help='Use Windows authentication')
    conn_group.add_argument('--connection', help='Use a saved connection by name')
    
    # Table and data options
    table_group = parser.add_argument_group('Table and Data Options')
    table_group.add_argument('--table', help='Table name to generate INSERT for')
    table_group.add_argument('--rows', type=int, default=1, help='Number of rows to generate (default: 1)')
    table_group.add_argument('--input-file', help='Input CSV or JSON file with data')
    table_group.add_argument('--output-file', help='Output file for INSERT statements')
    table_group.add_argument('--schema-only', action='store_true', help='Only show table schema, no INSERT generation')
    table_group.add_argument('--mock-schema', help='Use a mock schema for offline use')
    
    # Connection management options
    manage_group = parser.add_argument_group('Connection Management')
    manage_group.add_argument('--setup', action='store_true', help='Set up a new database connection interactively')
    manage_group.add_argument('--save-connection', help='Save a new connection with the given name (requires --server and --database)')
    manage_group.add_argument('--force', action='store_true', help='Force overwrite of an existing connection when using --save-connection')
    manage_group.add_argument('--list-connections', action='store_true', help='List saved connections')
    manage_group.add_argument('--delete-connection', help='Delete a saved connection by name')
    
    # Mock schema management options
    mock_schema_group = parser.add_argument_group('Mock Schema Management')
    mock_schema_group.add_argument('--create-mock-schema', action='store_true', help='Create a new mock schema interactively')
    mock_schema_group.add_argument('--save-mock-schema', help='Save a mock schema to a file')
    mock_schema_group.add_argument('--load-mock-schema', help='Load a mock schema from a file')
    mock_schema_group.add_argument('--list-mock-schemas', action='store_true', help='List saved mock schemas')
    mock_schema_group.add_argument('--delete-mock-schema', help='Delete a saved mock schema')
    
    if return_parser:
        return parser
    
    return parser.parse_args()


def create_generator_from_args(args, connection_manager):
    """Create a SQLInsertGenerator instance from command line arguments."""
    # If using a saved connection
    if args.connection:
        conn_data = connection_manager.get_connection(args.connection)
        if not conn_data:
            print(f"Connection '{args.connection}' not found.")
            return None
            
        if 'connection_string' in conn_data:
            args.connection_string = conn_data['connection_string']
        else:
            args.server = conn_data['server']
            args.database = conn_data['database']
            if conn_data.get('trusted', False):
                args.trusted = True
            else:
                args.username = conn_data.get('username')
                args.password = conn_data.get('password')
    
    # Validate connection parameters
    if not args.connection_string and not (args.server and args.database):
        if args.trusted:
            if not (args.server and args.database):
                print("When using Windows authentication, --server and --database are required")
                return None
        else:
            if not (args.server and args.database and args.username and args.password):
                print("Either --connection-string or (--server, --database, --username, --password) must be provided")
                return None
    
    # Create generator
    generator = SQLInsertGenerator(
        connection_string=args.connection_string,
        server=args.server,
        database=args.database,
        username=args.username,
        password=args.password,
        trusted_connection=args.trusted
    )
    
    # Connect to database
    if not generator.connect():
        return None
        
    return generator


def main():
    """Main function to handle command line arguments and execute the tool."""
    # Create connection manager
    connection_manager = ConnectionManager()
    
    # Create mock schema manager
    mock_schema_manager = MockSchemaManager()
    
    # Parse command line arguments
    args = parse_args()
    
    # Handle connection management commands
    if args.setup:
        if not (PYODBC_AVAILABLE or PYMSSQL_AVAILABLE):
            print("\nNeither pyodbc nor pymssql is available. You have two options:")
            print("1. Install a database driver to enable database connectivity (recommended)")
            print("2. Continue using mock schemas for offline mode")
            print("\nWhat would you like to do?")
            print("  [1] Show me detailed installation instructions for database drivers")
            print("  [2] Continue with mock schema mode")
            print("  [3] Exit")
            
            choice = safe_input("Enter your choice (1-3): ")
            
            if choice == "1":
                print("\n=== Database Driver Installation Instructions ===")
                print("\nOption 1: PyODBC (recommended)")
                print("\nFor Mac users:")
                print("  1. Install unixODBC:")
                print("     brew install unixodbc")
                print("\n  2. Install SQL Server driver:")
                print("     brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release")
                print("     brew update")
                print("     brew install msodbcsql17 mssql-tools")
                print("\n  3. Install pyodbc:")
                print("     pip install pyodbc")
                print("\nFor Mac with M1/M2 chips (if the above doesn't work):")
                print("  1. Install Rosetta 2 if needed:")
                print("     softwareupdate --install-rosetta")
                print("\n  2. Create a conda environment with x86_64 architecture:")
                print("     CONDA_SUBDIR=osx-64 conda create -n pyodbc_env python=3.9")
                print("     conda activate pyodbc_env")
                print("     conda config --env --set subdir osx-64")
                print("     conda install -c conda-forge pyodbc")
                print("\nOption 2: pymssql (alternative)")
                print("\n  Install pymssql:")
                print("     pip install pymssql")
                print("\nAfter installation, run this tool again.")
                return
            elif choice == "2":
                print("\nContinuing with mock schema mode...")
                if not args.table:
                    table_name = safe_input("Enter a table name for your mock schema: ")
                    if not table_name:
                        print("Table name is required for creating a mock schema.")
                        return
                else:
                    table_name = args.table
                    
                mock_schema = create_mock_schema_interactive()
                if mock_schema:
                    mock_schema_manager.save_schema(table_name, mock_schema)
                    print(f"Mock schema for '{table_name}' saved.")
                return
            else:
                return
        
        setup_new_connection_interactive(connection_manager)
        return
    
    if args.save_connection:
        if not (PYODBC_AVAILABLE or PYMSSQL_AVAILABLE):
            print("Neither pyodbc nor pymssql is available. Cannot save database connections.")
            return
        
        if not args.server or not args.database:
            print("Error: --server and --database are required with --save-connection", file=sys.stderr)
            return
            
        if not args.trusted and (not args.username or not args.password):
            print("Error: --username and --password are required with --save-connection unless --trusted is specified", file=sys.stderr)
            return
            
        if connection_manager.save_connection(
            args.save_connection,
            args.server,
            args.database,
            args.username,
            args.password,
            args.trusted,
            args.connection_string
        ):
            print(f"Connection '{args.save_connection}' saved successfully.")
        return
        
    if args.list_connections:
        connections = connection_manager.list_connections()
        if connections:
            print("Saved connections:")
            for conn in connections:
                print(f"  - {conn}")
        else:
            print("No saved connections found.")
        return
        
    if args.delete_connection:
        if connection_manager.delete_connection(args.delete_connection):
            print(f"Connection '{args.delete_connection}' deleted.")
        return
    
    # Handle mock schema management commands
    if args.create_mock_schema:
        mock_schema = create_mock_schema_interactive()
        if mock_schema and args.table:
            mock_schema_manager.save_schema(args.table, mock_schema)
            print(f"Mock schema for '{args.table}' saved.")
        return
        
    if args.save_mock_schema and args.table:
        mock_schema = mock_schema_manager.get_schema(args.table)
        if mock_schema:
            with open(f"{args.save_mock_schema}.json", 'w') as f:
                json.dump(mock_schema, f, indent=2)
            print(f"Mock schema saved to {args.save_mock_schema}.json")
        else:
            print(f"Mock schema for table '{args.table}' not found.")
        return
        
    if args.load_mock_schema and args.table:
        try:
            with open(args.load_mock_schema, 'r') as f:
                mock_schema = json.load(f)
            mock_schema_manager.save_schema(args.table, mock_schema)
            print(f"Mock schema loaded from {args.load_mock_schema} and saved for table '{args.table}'")
        except Exception as e:
            print(f"Error loading mock schema: {e}")
        return
        
    if args.list_mock_schemas:
        mock_schemas = mock_schema_manager.list_schemas()
        if mock_schemas:
            print("Saved mock schemas:")
            for schema in mock_schemas:
                print(f"  - {schema}")
        else:
            print("No saved mock schemas found.")
        return
        
    if args.delete_mock_schema:
        if mock_schema_manager.delete_schema(args.delete_mock_schema):
            print(f"Mock schema '{args.delete_mock_schema}' deleted.")
        return
    
    # If no table is specified and no connection management command was given,
    # show help and available connections
    if not args.table and not args.connection_string and not args.server:
        connections = connection_manager.list_connections()
        if connections:
            print("Available saved connections:")
            for conn in connections:
                print(f"  - {conn}")
            print("\nUse --connection NAME to use a saved connection.")
        else:
            print("No saved connections found. Use --setup to create one.")
            
        mock_schemas = mock_schema_manager.list_schemas()
        if mock_schemas:
            print("\nAvailable mock schemas:")
            for schema in mock_schemas:
                print(f"  - {schema}")
            print("\nUse --table NAME --mock-schema NAME to use a mock schema.")
            
        parser = parse_args(True)
        parser.print_help()
        return
    
    # If no table is specified but connection info is provided, show available tables
    if not args.table and (args.connection_string or args.server or args.connection):
        if not (PYODBC_AVAILABLE or PYMSSQL_AVAILABLE):
            print("Neither pyodbc nor pymssql is available. Cannot connect to database.")
            return
            
        # Create generator with connection info
        generator = create_generator_from_args(args, connection_manager)
        if not generator:
            return
            
        # Get available tables
        tables = generator.get_available_tables()
        if tables:
            print("Available tables:")
            for table in tables:
                print(f"  - {table}")
            print("\nUse --table NAME to generate INSERT statements for a specific table.")
        else:
            print("No tables found in the database.")
        return
    
    # Require a table name
    if not args.table:
        print("Error: --table is required", file=sys.stderr)
        return
    
    # Set default row count
    if not args.rows:
        args.rows = 1
    
    # Create generator with connection info if needed
    if not args.mock_schema:
        if not (PYODBC_AVAILABLE or PYMSSQL_AVAILABLE):
            # Check if we have a mock schema for this table
            mock_schema = mock_schema_manager.get_schema(args.table)
            if mock_schema:
                print(f"Using mock schema for table '{args.table}'")
                args.mock_schema = args.table
            else:
                print("Neither pyodbc nor pymssql is available and no mock schema found for this table.")
                print("Would you like to create a mock schema for this table? (y/n)")
                response = safe_input("").lower()
                if response == 'y':
                    mock_schema = create_mock_schema_interactive()
                    if mock_schema:
                        mock_schema_manager.save_schema(args.table, mock_schema)
                        print(f"Mock schema for '{args.table}' saved.")
                        args.mock_schema = args.table
                    else:
                        return
                else:
                    return
        else:
            # Create generator with connection info
            generator = create_generator_from_args(args, connection_manager)
            if not generator:
                return
    
    # Handle mock schema mode
    if args.mock_schema:
        mock_schema = mock_schema_manager.get_schema(args.mock_schema)
        if not mock_schema:
            print(f"Mock schema '{args.mock_schema}' not found.")
            return
            
        # Create generator without connection
        generator = SQLInsertGenerator()
        
        if args.schema_only:
            # Just print the table schema
            print(f"Schema for table {args.table} (mock):")
            for col in mock_schema:
                nullable = "NULL" if col['is_nullable'] else "NOT NULL"
                identity = "IDENTITY" if col['is_identity'] else ""
                pk = "PRIMARY KEY" if col['is_primary_key'] else ""
                print(f"  {col['name']} {col['type']} {nullable} {identity} {pk}".strip())
        else:
            # Generate INSERT statements
            insert_stmt = generator.generate_inserts(
                args.table,
                args.rows,
                args.output_file,
                args.input_file,
                mock_schema
            )
            
            if insert_stmt and not args.output_file:
                print(insert_stmt)
        return
    
    # Normal database mode
    try:
        if args.schema_only:
            # Just print the table schema
            columns = generator.get_table_schema(args.table)
            if columns:
                print(f"Schema for table {args.table}:")
                for col in columns:
                    nullable = "NULL" if col['is_nullable'] else "NOT NULL"
                    identity = "IDENTITY" if col['is_identity'] else ""
                    pk = "PRIMARY KEY" if col['is_primary_key'] else ""
                    print(f"  {col['name']} {col['type']} {nullable} {identity} {pk}".strip())
        else:
            # Generate INSERT statements
            insert_stmt = generator.generate_inserts(
                args.table,
                args.rows,
                args.output_file,
                args.input_file
            )
            
            if insert_stmt and not args.output_file:
                print(insert_stmt)
    finally:
        if generator and hasattr(generator, 'connection') and generator.connection:
            generator.connection.close()


if __name__ == "__main__":
    main()
