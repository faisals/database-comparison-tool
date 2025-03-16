"""
Formatting utilities for the Database Comparison Tool.
"""

def format_data_as_html(data):
    """Format data as an HTML table"""
    if not data or not data['columns'] or not data['rows']:
        return "<div class='alert alert-warning'>No data available</div>"
    
    html = "<table class='table table-sm'>"
    
    # Header
    html += "<thead style='background-color: #F5F5F5; color: #333333;'><tr>"
    for col in data['columns']:
        html += f"<th>{col}</th>"
    html += "</tr></thead>"
    
    # Body
    html += "<tbody>"
    for row in data['rows']:
        status_class = ''
        if row.get('_status'):
            if row['_status'] == 'added':
                status_class = "style='background-color: rgba(76, 175, 80, 0.1); color: #333333;'"
            elif row['_status'] == 'removed':
                status_class = "style='background-color: rgba(244, 67, 54, 0.1); color: #333333;'"
            elif row['_status'] == 'modified':
                status_class = "style='background-color: rgba(33, 150, 243, 0.1); color: #333333;'"
        
        html += f"<tr {status_class}>"
        for col in data['columns']:
            value = row.get(col, '')
            cell_class = ''
            
            if row.get('_changes') and col in row['_changes']:
                cell_class = "style='background-color: rgba(33, 150, 243, 0.2); color: #333333;'"
            
            if value is None:
                value = '<em class="text-muted">NULL</em>'
            
            html += f"<td {cell_class}>{value}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    
    return html
