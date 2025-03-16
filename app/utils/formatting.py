"""
Formatting utilities for the Database Comparison Tool.
"""

def format_data_as_html(comparison_result):
    """Format comparison result as HTML"""
    if not comparison_result:
        return "<div class='alert alert-warning'>No comparison data available</div>"
    
    summary = comparison_result.get('summary', {})
    data_differences = comparison_result.get('data_differences', [])
    
    # Create summary section
    html = "<div class='comparison-summary card mb-4'>"
    html += "<div class='card-header'><h4>Comparison Summary</h4></div>"
    html += "<div class='card-body'>"
    html += "<table class='table table-bordered'>"
    html += "<tr><th>Source Total Rows</th><td>" + str(summary.get('source_total_rows', 0)) + "</td></tr>"
    html += "<tr><th>Target Total Rows</th><td>" + str(summary.get('target_total_rows', 0)) + "</td></tr>"
    html += "<tr><th>Rows Compared</th><td>" + str(summary.get('total_rows_compared', 0)) + "</td></tr>"
    html += "<tr><th>Rows With Differences</th><td>" + str(summary.get('rows_with_differences', 0)) + "</td></tr>"
    html += "<tr><th>Row Count Difference</th><td>" + str(summary.get('row_count_difference', 0)) + "</td></tr>"
    html += "</table>"
    html += "</div></div>"
    
    # If no differences, show a message
    if not data_differences:
        html += "<div class='alert alert-success'>No differences found in the compared data</div>"
        return html
    
    # Create differences table
    html += "<div class='comparison-details card'>"
    html += "<div class='card-header'><h4>Detailed Differences</h4></div>"
    html += "<div class='card-body'>"
    html += "<div class='table-responsive'>"
    html += "<table class='table table-bordered table-striped'>"
    html += "<thead><tr><th>Row</th><th>Column</th><th>Source Value</th><th>Target Value</th></tr></thead>"
    html += "<tbody>"
    
    for diff in data_differences:
        row_index = diff.get('row_index', 0) + 1  # 1-based indexing for display
        diff_details = diff.get('differences', {})
        
        for col, values in diff_details.items():
            html += "<tr>"
            html += f"<td>{row_index}</td>"
            html += f"<td>{col}</td>"
            html += f"<td>{values.get('source', '')}</td>"
            html += f"<td>{values.get('target', '')}</td>"
            html += "</tr>"
    
    html += "</tbody></table>"
    html += "</div></div></div>"
    
    return html
