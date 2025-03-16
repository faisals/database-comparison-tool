/**
 * CORAL - Modern Interactive Features
 * Provides interactive functionality for the CORAL database comparison tool
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    initializeTooltips();
    
    // Initialize collapsible sections
    initializeCollapsibles();
    
    // Initialize toggle switches
    initializeToggles();
    
    // Initialize expandable rows
    initializeExpandableRows();
});

/**
 * Initialize tooltip functionality
 */
function initializeTooltips() {
    // Using Bootstrap's tooltip functionality if available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * Initialize collapsible sections
 */
function initializeCollapsibles() {
    const collapsibleHeaders = document.querySelectorAll('.collapsible-header');
    
    collapsibleHeaders.forEach(header => {
        header.addEventListener('click', function() {
            // Toggle active class
            this.classList.toggle('active');
            
            // Get the content associated with this header
            const content = this.nextElementSibling;
            
            // Toggle display
            if (content.style.display === 'block') {
                content.style.display = 'none';
                // Change icon if present
                const icon = this.querySelector('.collapse-icon');
                if (icon) {
                    icon.classList.remove('bi-chevron-up');
                    icon.classList.add('bi-chevron-down');
                }
            } else {
                content.style.display = 'block';
                // Change icon if present
                const icon = this.querySelector('.collapse-icon');
                if (icon) {
                    icon.classList.remove('bi-chevron-down');
                    icon.classList.add('bi-chevron-up');
                }
            }
        });
    });
}

/**
 * Initialize toggle switches
 */
function initializeToggles() {
    // Toggle differences only
    const toggleDifferencesOnly = document.getElementById('toggleDifferencesOnly');
    if (toggleDifferencesOnly) {
        toggleDifferencesOnly.addEventListener('change', function() {
            const showOnlyDifferences = this.checked;
            const tableRows = document.querySelectorAll('.detailed-differences-table tbody tr');
            
            tableRows.forEach(row => {
                if (showOnlyDifferences) {
                    // If toggle is on, hide rows without differences
                    if (!row.classList.contains('diff-added') && 
                        !row.classList.contains('diff-deleted') && 
                        !row.classList.contains('diff-modified')) {
                        row.style.display = 'none';
                    }
                } else {
                    // Show all rows
                    row.style.display = '';
                }
            });
        });
    }
}

/**
 * Initialize expandable rows
 */
function initializeExpandableRows() {
    const expandableRows = document.querySelectorAll('.expandable-row');
    
    expandableRows.forEach(row => {
        row.addEventListener('click', function() {
            // Get the row data
            const rowData = JSON.parse(this.getAttribute('data-row-details'));
            
            // Create modal content
            let modalContent = '<div class="table-responsive"><table class="coral-table coral-table-striped">';
            modalContent += '<thead><tr><th>Column</th><th>Source Value</th><th>Target Value</th></tr></thead>';
            modalContent += '<tbody>';
            
            // Add row data
            for (const [column, values] of Object.entries(rowData)) {
                const sourceValue = values.source || '';
                const targetValue = values.target || '';
                const isDifferent = sourceValue !== targetValue;
                
                modalContent += `<tr ${isDifferent ? 'class="diff-modified"' : ''}>`;
                modalContent += `<td>${column}</td>`;
                modalContent += `<td>${sourceValue}</td>`;
                modalContent += `<td>${targetValue}</td>`;
                modalContent += '</tr>';
            }
            
            modalContent += '</tbody></table></div>';
            
            // Set modal content
            document.getElementById('rowDetailsModalBody').innerHTML = modalContent;
            document.getElementById('rowDetailsModalLabel').textContent = 'Row Details: ' + this.getAttribute('data-row-id');
            
            // Show modal using Bootstrap
            const rowDetailsModal = new bootstrap.Modal(document.getElementById('rowDetailsModal'));
            rowDetailsModal.show();
        });
    });
}

/**
 * Filter table to show only rows with differences
 * @param {string} tableId - The ID of the table to filter
 * @param {boolean} showOnlyDifferences - Whether to show only rows with differences
 */
function filterTableDifferences(tableId, showOnlyDifferences) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        if (showOnlyDifferences) {
            // If we're showing only differences, hide rows without diff classes
            if (!row.classList.contains('diff-added') && 
                !row.classList.contains('diff-deleted') && 
                !row.classList.contains('diff-modified')) {
                row.style.display = 'none';
            }
        } else {
            // Show all rows
            row.style.display = '';
        }
    });
}
