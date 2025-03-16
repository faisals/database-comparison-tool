# SQL Insert Generator

A command-line tool that generates INSERT statements for SQL Server database tables. This tool can generate statements for one or multiple rows based on table schema, with support for random data generation or data from input files.

## Features

- Connect to SQL Server databases using Windows authentication or SQL Server authentication
- Save and manage database connection information for easy reuse
- Generate INSERT statements for any table in the database
- Create statements for a single row or multiple rows
- Generate random data based on column types and constraints
- Load data from CSV or JSON files
- Output to console or file
- View table schema without generating INSERT statements
- Work in offline mode with mock schemas when database connectivity is unavailable

# Database Table Comparison Tool

A modern web application that allows you to compare table structures and data between different database versions. This tool leverages the connection management system from the SQL Insert Generator to provide a visual comparison of database tables.

## Features

- Compare table schemas between different databases
- Visualize differences with interactive charts
- Identify columns that exist only in one database
- Highlight differences in column properties (data types, nullability, etc.)
- View sample data from both tables
- Generate printable comparison reports
- Support for both pyodbc and pymssql database drivers

## Installation

### Requirements

- Python 3.6 or higher
- SQL Server ODBC Driver (ODBC Driver 17 for SQL Server recommended) - *Optional if using pymssql*
- PyMSSQL - *Alternative to pyodbc for database connectivity*

### Steps

1. Clone or download this repository
2. Install the required Python packages:

```
pip install -r requirements.txt
```

3. Make the script executable (on Linux/macOS):

```
chmod +x sql_insert_generator.py
```

## Usage

### First-Time Setup

There are two ways to save database connection information:

#### Interactive Setup

Run the interactive setup wizard:

```
python sql_insert_generator.py --setup
```

You'll be guided through a step-by-step process to save your database connection information.

#### Non-Interactive Setup

Save a connection directly from the command line:

```
python sql_insert_generator.py --save-connection "MyConnection" --server localhost --database MyDatabase --username sa --password myPassword
```

For Windows authentication:

```
python sql_insert_generator.py --save-connection "MyWindowsAuth" --server localhost --database MyDatabase --trusted
```

### Managing Connections

List saved connections:

```
python sql_insert_generator.py --list-connections
```

Delete a saved connection:

```
python sql_insert_generator.py --delete-connection "MyConnection"
```

Use a saved connection:

```
python sql_insert_generator.py --connection "MyConnection" --table Customers
```

### Working with Mock Schemas (Offline Mode)

If you don't have access to a database or the ODBC driver is not installed, you can work in offline mode using mock schemas:

#### Creating a Mock Schema

Create a mock schema interactively:

```
python sql_insert_generator.py --create-mock-schema --table Customers
```

You'll be guided through defining column names, data types, and constraints.

#### Using a Mock Schema

Generate INSERT statements using a mock schema:

```
python sql_insert_generator.py --table Customers --mock-schema Customers --rows 5
```

#### Managing Mock Schemas

List saved mock schemas:

```
python sql_insert_generator.py --list-mock-schemas
```

Delete a mock schema:

```
python sql_insert_generator.py --delete-mock-schema Customers
```

Export a mock schema to a file:

```
python sql_insert_generator.py --table Customers --save-mock-schema customers_schema
```

Import a mock schema from a file:

```
python sql_insert_generator.py --table Customers --load-mock-schema customers_schema.json
```

### Basic Usage

Generate a single INSERT statement for a table:

```
python sql_insert_generator.py --server localhost --database MyDatabase --username sa --password myPassword --table Customers
```

Generate multiple INSERT statements:

```
python sql_insert_generator.py --server localhost --database MyDatabase --username sa --password myPassword --table Customers --rows 5
```

### Using Windows Authentication

```
python sql_insert_generator.py --server localhost --database MyDatabase --trusted --table Customers
```

### Using a Connection String

```
python sql_insert_generator.py --connection-string "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=MyDatabase;UID=sa;PWD=myPassword" --table Customers
```

### Output to File

```
python sql_insert_generator.py --server localhost --database MyDatabase --username sa --password myPassword --table Customers --rows 10 --output-file inserts.sql
```

### Using Input Data from File

```
python sql_insert_generator.py --server localhost --database MyDatabase --username sa --password myPassword --table Customers --input-file customers.csv
```

### View Table Schema Only

```
python sql_insert_generator.py --server localhost --database MyDatabase --username sa --password myPassword --table Customers --schema-only
```

### Database Table Comparison Tool

#### Running the Web Application

Start the web application:

```
python db_compare_app.py
```

This will start a development server at http://localhost:5000. Open this URL in your web browser to access the application.

#### Using the Comparison Tool

1. **Select Database Connections**: On the home page, select the source and target database connections you want to compare.

2. **Select Tables**: Choose the tables you want to compare from each database. The tool will automatically select tables with matching names if they exist in both databases.

3. **View Comparison Results**: The tool will display a detailed comparison of the table schemas, highlighting:
   - Columns that exist only in the source database
   - Columns that exist only in the target database
   - Columns that exist in both but have differences (data type, length, nullability, etc.)
   - Identical columns
   
4. **View Data Samples**: You can also view sample data from both tables to compare the actual content.

5. **Print Report**: Generate a printable report of the comparison results for documentation purposes.

#### Example Workflow

1. Set up database connections using the SQL Insert Generator:
   ```
   python sql_insert_generator.py --setup
   ```

2. Start the Database Table Comparison Tool:
   ```
   python db_compare_app.py
   ```

3. Open your browser and navigate to http://localhost:5000

4. Select your source and target database connections

5. Choose the tables you want to compare

6. Review the comparison results

## Input File Format

### CSV

The CSV file should have column names in the header row that match the table column names:

```csv
FirstName,LastName,Email,Age
John,Doe,john@example.com,30
Jane,Smith,jane@example.com,25
```

### JSON

The JSON file should contain an array of objects with property names that match the table column names:

```json
[
  {
    "FirstName": "John",
    "LastName": "Doe",
    "Email": "john@example.com",
    "Age": 30
  },
  {
    "FirstName": "Jane",
    "LastName": "Smith",
    "Email": "jane@example.com",
    "Age": 25
  }
]
```

## Notes for Windows Users

- Ensure you have the SQL Server ODBC driver installed
- For Windows authentication, use the `--trusted` flag instead of providing username and password
- If using PowerShell, you may need to escape quotes in the connection string

## Configuration Storage

- Connection information is stored in `~/.sql_insert_generator/connections.json`. Passwords are stored in plain text, so be cautious with this file's permissions.
- Mock schemas are stored in `~/.sql_insert_generator/schemas.json`.

## Troubleshooting

- If you encounter connection issues, verify your SQL Server instance is running and accessible
- Check that the ODBC driver is installed correctly
- Ensure the user has appropriate permissions to access the database and table
- For issues with input files, verify the column names match exactly with the table column names
- If you see an error about pyodbc not being available, you can still use the tool in mock schema mode

## License

MIT
