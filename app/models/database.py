"""
Database connection model for the Database Comparison Tool.
"""
import pymssql

class DatabaseConnection:
    def __init__(self, server, database, username, password, driver='ODBC Driver 17 for SQL Server'):
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.driver = driver
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Connect to the database using pymssql"""
        try:
            self.connection = pymssql.connect(
                server=self.server,
                user=self.username,
                password=self.password,
                database=self.database,
                appname='Database Comparison Tool'
            )
            self.cursor = self.connection.cursor()
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
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
