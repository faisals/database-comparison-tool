"""
Repository for storing and retrieving database connection information.
"""
import os
from datetime import datetime
import pymssql

class ConnectionRepository:
    """Repository for database connection information."""
    
    def __init__(self, server='localhost', database='dbcomparetool', 
                 username='graph', password='Openup123#'):
        """Initialize the connection repository."""
        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Connect to the repository database."""
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
        """Disconnect from the repository database."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            
    def ensure_tables_exist(self):
        """Ensure that the necessary tables exist in the database."""
        if not self.connection:
            if not self.connect():
                return False
                
        try:
            # Create the table if it doesn't exist
            self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DatabaseConnections')
            BEGIN
                CREATE TABLE [DatabaseConnections] (
                    [ConnectionId] INT IDENTITY(1,1) PRIMARY KEY,
                    [ConnectionName] NVARCHAR(100) NOT NULL,
                    [Server] NVARCHAR(255) NOT NULL,
                    [Database_Name] NVARCHAR(255) NOT NULL,
                    [Username] NVARCHAR(100) NOT NULL,
                    [Password] NVARCHAR(255) NOT NULL,
                    [Driver] NVARCHAR(255) NULL,
                    [CreatedDate] DATETIME NOT NULL,
                    [LastUsedDate] DATETIME NULL
                )
            END
            """)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error ensuring tables exist: {e}")
            return False
            
    def save_connection(self, connection_name, server, database, username, password, driver='ODBC Driver 17 for SQL Server'):
        """Save a database connection to the repository."""
        if not self.connection:
            if not self.connect():
                return False
                
        try:
            # Check if connection with this name already exists
            self.cursor.execute("""
            SELECT COUNT(*) FROM [DatabaseConnections] WHERE [ConnectionName] = %s
            """, (connection_name,))
            
            count = self.cursor.fetchone()[0]
            
            if count > 0:
                # Update existing connection
                self.cursor.execute("""
                UPDATE [DatabaseConnections]
                SET [Server] = %s, [Database_Name] = %s, [Username] = %s, [Password] = %s, 
                    [Driver] = %s, [LastUsedDate] = %s
                WHERE [ConnectionName] = %s
                """, (server, database, username, password, driver,
                      datetime.now(), connection_name))
            else:
                # Insert new connection
                self.cursor.execute("""
                INSERT INTO [DatabaseConnections] 
                ([ConnectionName], [Server], [Database_Name], [Username], [Password], [Driver], [CreatedDate], [LastUsedDate])
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (connection_name, server, database, username, password, driver,
                      datetime.now(), datetime.now()))
                
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error saving connection: {e}")
            return False
            
    def get_all_connections(self):
        """Get all database connections from the repository."""
        if not self.connection:
            if not self.connect():
                return []
                
        try:
            self.cursor.execute("""
            SELECT [ConnectionId], [ConnectionName], [Server], [Database_Name], [Username], [Password], 
                   [Driver], [CreatedDate], [LastUsedDate]
            FROM [DatabaseConnections]
            ORDER BY [ConnectionName]
            """)
            
            connections = []
            for row in self.cursor.fetchall():
                connections.append({
                    'id': row[0],
                    'name': row[1],
                    'server': row[2],
                    'database': row[3],
                    'username': row[4],
                    'password': row[5],
                    'driver': row[6] if len(row) > 6 else 'ODBC Driver 17 for SQL Server',
                    'created_date': row[7] if len(row) > 7 else None,
                    'last_used_date': row[8] if len(row) > 8 else None
                })
                
            return connections
        except Exception as e:
            print(f"Error getting connections: {e}")
            return []
            
    def get_connection_by_name(self, connection_name):
        """Get a database connection by name."""
        if not self.connection:
            if not self.connect():
                return None
                
        try:
            self.cursor.execute("""
            SELECT [ConnectionId], [ConnectionName], [Server], [Database_Name], [Username], [Password], 
                   [Driver], [CreatedDate], [LastUsedDate]
            FROM [DatabaseConnections]
            WHERE [ConnectionName] = %s
            """, (connection_name,))  
            
            row = self.cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'server': row[2],
                    'database': row[3],
                    'username': row[4],
                    'password': row[5],
                    'driver': row[6] if len(row) > 6 else 'ODBC Driver 17 for SQL Server',
                    'created_date': row[7] if len(row) > 7 else None,
                    'last_used_date': row[8] if len(row) > 8 else None
                }
            else:
                return None
        except Exception as e:
            print(f"Error getting connection by name: {e}")
            return None
            
    def delete_connection(self, connection_name):
        """Delete a database connection by name."""
        if not self.connection:
            if not self.connect():
                return False
                
        try:
            self.cursor.execute("""
            DELETE FROM [DatabaseConnections]
            WHERE [ConnectionName] = %s
            """, (connection_name,))
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error deleting connection: {e}")
            return False
            
    def update_last_used_date(self, connection_name):
        """Update the last used date for a connection."""
        if not self.connection:
            if not self.connect():
                return False
                
        try:
            self.cursor.execute("""
            UPDATE [DatabaseConnections]
            SET [LastUsedDate] = %s
            WHERE [ConnectionName] = %s
            """, (datetime.now(), connection_name))
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error updating last used date: {e}")
            return False
