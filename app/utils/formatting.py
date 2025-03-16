"""
Formatting utilities for the Database Comparison Tool.
"""

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
