# Database Table Comparison Tool

A modern Flask-based web application that allows you to compare table structures and data between different database versions. This tool provides a visual comparison of database tables with an intuitive user interface.

## Features

- Compare table schemas between different databases
- Visualize differences with interactive charts
- Identify columns that exist only in one database
- Highlight differences in column properties (data types, nullability, etc.)
- View sample data from both tables
- Generate printable comparison reports
- Support for both pyodbc and pymssql database drivers
- Clean, modern Bootstrap-based interface

## Technical Stack

- Flask web framework
- Jinja2 templating engine
- Flask-WTF for form handling
- Bootstrap for styling
- Database connections managed by ConnectionRepository

## Project Structure

- `db_compare_app.py` - Main application file
- `app/routes/` - Route handlers organized by function
- `app/forms/forms.py` - Form definitions using Flask-WTF
- `app/models/` - Database connection and model logic
- `templates/` - Jinja2 HTML templates
- `static/` - Static assets (CSS, JS, images)

## Installation

### Requirements

- Python 3.6 or higher
- SQL Server ODBC Driver (ODBC Driver 17 for SQL Server recommended) - *Optional if using pymssql*
- PyMSSQL - *Alternative to pyodbc for database connectivity*

### Steps

1. Clone or download this repository
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

Start the web application:

```bash
python db_compare_app.py
```

The application will be available at `http://localhost:5000` by default.

## Development

The application uses a clean, modular architecture:
- Routes are organized in separate files under `app/routes/`
- Forms are defined in `app/forms/forms.py`
- Database connections are handled by the ConnectionRepository in `app/models/`
- Templates use Bootstrap for a consistent, modern look

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
