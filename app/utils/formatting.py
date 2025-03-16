"""
Formatting utilities for the Database Comparison Tool.
"""

def format_data_as_html(comparison_result):
    """Format comparison result as HTML"""
    if not comparison_result:
        return "<div class='alert alert-warning'>No comparison data available</div>"
    
    summary = comparison_result.get('summary', {})
    data_differences = comparison_result.get('data_differences', [])
    columns = comparison_result.get('columns', [])
    
    # Create a modern card layout with the requested color scheme
    html = ""
    
    # Comparison Summary card with key metrics
    html += "<div class='coral-card mb-4'>"
    html += "<div class='coral-card-header'><h4 class='mb-0'>Comparison Summary</h4></div>"
    html += "<div class='coral-card-body'>"
    html += "<div class='row'>"
    
    # Summary statistics in a 3-column layout
    html += "<div class='col-md-4 mb-3'>"
    html += "<div class='summary-stat'>"
    html += f"<div class='summary-stat-value'>{summary.get('total_rows_compared', 0)}</div>"
    html += "<div class='summary-stat-label'>Total Rows Compared</div>"
    html += "</div></div>"
    
    html += "<div class='col-md-4 mb-3'>"
    html += "<div class='summary-stat'>"
    html += f"<div class='summary-stat-value' style='color: #2196F3;'>{summary.get('rows_with_differences', 0)}</div>"
    html += "<div class='summary-stat-label'>Rows with Differences</div>"
    html += "</div></div>"
    
    html += "<div class='col-md-4 mb-3'>"
    html += "<div class='summary-stat'>"
    html += f"<div class='summary-stat-value' style='color: {('#4CAF50' if summary.get('row_count_difference', 0) >= 0 else '#F44336')};'>{summary.get('row_count_difference', 0)}</div>"
    html += "<div class='summary-stat-label'>Row Count Difference</div>"
    html += "</div></div>"
    
    html += "</div>" # End of row
    html += "</div></div>" # End of card
    
    # Detailed Summary card with table of totals
    html += "<div class='coral-card mb-4'>"
    html += "<div class='coral-card-header'><h4 class='mb-0'>Detailed Summary</h4></div>"
    html += "<div class='coral-card-body'>"
    html += "<div class='table-responsive'>"
    html += "<table class='coral-table coral-table-striped'>"
    html += "<tbody>"
    html += f"<tr><th>Source Total Rows</th><td>{summary.get('source_total_rows', 0)}</td></tr>"
    html += f"<tr><th>Target Total Rows</th><td>{summary.get('target_total_rows', 0)}</td></tr>"
    html += f"<tr><th>Rows Compared</th><td>{summary.get('total_rows_compared', 0)}</td></tr>"
    html += f"<tr><th>Rows With Differences</th><td>{summary.get('rows_with_differences', 0)}</td></tr>"
    html += f"<tr><th>Row Count Difference</th><td>{summary.get('row_count_difference', 0)}</td></tr>"
    html += "</tbody></table>"
    html += "</div></div></div>"
    
    # If no differences, show a message
    if not data_differences and summary.get('rows_with_differences', 0) == 0:
        html += "<div class='alert alert-success'>No differences found in the compared data</div>"
        return html
    
    # Create a dictionary to track rows with differences for row highlighting
    row_differences = {}
    for diff in data_differences:
        row_index = diff.get('row_index', 0)
        row_differences[row_index] = diff.get('differences', {})
    
    # Detailed Differences card with collapsible table
    html += "<div class='coral-card mb-4'>"
    html += "<div class='coral-card-header'><h4 class='mb-0'>Detailed Differences</h4></div>"
    html += "<div class='coral-card-body'>"
    
    # Add tooltip to explain the colors
    html += "<div class='mb-3'>"
    html += "<span class='badge me-2' style='background-color: #4CAF50;'>Added</span>"
    html += "<span class='badge me-2' style='background-color: #F44336;'>Deleted</span>"
    html += "<span class='badge me-2' style='background-color: #2196F3;'>Modified</span>"
    html += "</div>"
    
    html += "<div class='table-responsive'>"
    html += "<table class='coral-table coral-table-striped coral-table-hover' id='detailedDifferencesTable'>"
    html += "<thead><tr><th>Row</th><th>Column</th><th>Source Value</th><th>Target Value</th></tr></thead>"
    html += "<tbody>"
    
    for diff in data_differences:
        row_index = diff.get('row_index', 0) + 1  # 1-based indexing for display
        diff_details = diff.get('differences', {})
        
        # Create a JSON string of the full row data for the expandable row
        row_data_json = "{"
        for col, values in diff_details.items():
            source_val = values.get('source', '').replace('"', '\\"')
            target_val = values.get('target', '').replace('"', '\\"')
            row_data_json += f'"{col}": {{"source": "{source_val}", "target": "{target_val}"}}, '
        row_data_json = row_data_json.rstrip(', ') + "}"
        
        for col, values in diff_details.items():
            source_val = values.get('source', '')
            target_val = values.get('target', '')
            
            # Determine the difference type for styling
            if source_val == '' and target_val != '':
                diff_class = "diff-added"
            elif source_val != '' and target_val == '':
                diff_class = "diff-deleted"
            else:
                diff_class = "diff-modified"
            
            html += f"<tr class='{diff_class} expandable-row' data-row-id='Row {row_index}' data-row-details='{row_data_json}'>"
            html += f"<td>{row_index}</td>"
            html += f"<td>{col}</td>"
            html += f"<td>{source_val}</td>"
            html += f"<td>{target_val}</td>"
            html += "</tr>"
    
    html += "</tbody></table>"
    html += "</div></div></div>"
    
    # Add data preview with row highlighting - only showing rows with differences
    if 'source_data' in comparison_result and 'target_data' in comparison_result:
        source_data = comparison_result.get('source_data', {}).get('rows', [])
        target_data = comparison_result.get('target_data', {}).get('rows', [])
        
        if source_data or target_data:
            # Source data collapsible section
            html += "<div class='collapsible-section'>"
            html += "<div class='collapsible-header'>"
            html += "<h5 class='mb-0'>Source Data</h5>"
            html += "<i class='bi bi-chevron-down collapse-icon'></i>"
            html += "</div>"
            html += "<div class='collapsible-content'>"
            html += "<div class='table-responsive'>"
            html += "<table class='coral-table coral-table-striped coral-table-hover'>"
            html += "<thead><tr>"
            for col in columns:
                html += f"<th>{col}</th>"
            html += "</tr></thead><tbody>"
            
            # Track if we have any rows to display
            source_rows_displayed = 0
            
            for row_index, row in enumerate(source_data):
                # Only show rows with differences or rows that don't exist in target
                if row_index in row_differences or row_index >= len(target_data):
                    source_rows_displayed += 1
                    
                    # Apply row highlighting based on differences
                    if row_index in row_differences:
                        html += "<tr class='diff-modified'>"  # Blue for modified
                    else:
                        # This row doesn't exist in target
                        html += "<tr class='diff-deleted'>"  # Red for deleted
                            
                    for col in columns:
                        html += f"<td>{row.get(col, '')}</td>"
                    html += "</tr>"
            
            if source_rows_displayed == 0:
                html += "<tr><td colspan='" + str(len(columns)) + "' class='text-center'>No differences found in source data</td></tr>"
                
            html += "</tbody></table></div>"
            html += "</div></div>"  # End of collapsible section
            
            # Target data collapsible section
            html += "<div class='collapsible-section'>"
            html += "<div class='collapsible-header'>"
            html += "<h5 class='mb-0'>Target Data</h5>"
            html += "<i class='bi bi-chevron-down collapse-icon'></i>"
            html += "</div>"
            html += "<div class='collapsible-content'>"
            html += "<div class='table-responsive'>"
            html += "<table class='coral-table coral-table-striped coral-table-hover'>"
            html += "<thead><tr>"
            for col in columns:
                html += f"<th>{col}</th>"
            html += "</tr></thead><tbody>"
            
            # Track if we have any rows to display
            target_rows_displayed = 0
            
            for row_index, row in enumerate(target_data):
                # Only show rows with differences or rows that don't exist in source
                if row_index in row_differences or row_index >= len(source_data):
                    target_rows_displayed += 1
                    
                    # Apply row highlighting based on differences
                    if row_index in row_differences:
                        html += "<tr class='diff-modified'>"  # Blue for modified
                    else:
                        # This row doesn't exist in source
                        html += "<tr class='diff-added'>"  # Green for added
                            
                    for col in columns:
                        html += f"<td>{row.get(col, '')}</td>"
                    html += "</tr>"
            
            if target_rows_displayed == 0:
                html += "<tr><td colspan='" + str(len(columns)) + "' class='text-center'>No differences found in target data</td></tr>"
                
            html += "</tbody></table></div>"
            html += "</div></div>"  # End of collapsible section
    
    return html
