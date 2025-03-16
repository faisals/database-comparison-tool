# CORAL - Database Comparison Tool

A modern Flask-based web application that allows you to compare schemas and data between different database connections. CORAL provides a visual comparison interface with an emphasis on clarity and efficiency.

## Features

- Compare database schemas and data across different connections
- Visualize differences with interactive comparisons
- Identify schema differences and data discrepancies
- Support for multiple database connections
- Clean, modern Bootstrap-based interface
- Real-time comparison updates

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
- Required database drivers for your connections

### Steps

1. Clone or download this repository
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

Start CORAL:

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

## Configuration

Connection information is stored securely in the application's configuration directory.

## License

MIT
