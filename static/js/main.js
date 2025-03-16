/**
 * Main JavaScript file for the Database Table Comparison Tool
 */

document.addEventListener('DOMContentLoaded', function() {
    // Enable Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Enable Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Add hover effect to table rows
    const tableRows = document.querySelectorAll('.table-hover tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.classList.add('table-active');
        });
        row.addEventListener('mouseleave', function() {
            this.classList.remove('table-active');
        });
    });
    
    // Handle table filter input
    const tableFilterInput = document.getElementById('tableFilter');
    if (tableFilterInput) {
        tableFilterInput.addEventListener('keyup', function() {
            const filterValue = this.value.toLowerCase();
            const tableRows = document.querySelectorAll('.filterable-table tbody tr');
            
            tableRows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.indexOf(filterValue) > -1) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Handle table selection synchronization
    const table1Select = document.getElementById('table1');
    const table2Select = document.getElementById('table2');
    
    if (table1Select && table2Select) {
        // Function to find matching table name in the other select
        const findMatchingTable = (sourceName, targetSelect) => {
            for (let i = 0; i < targetSelect.options.length; i++) {
                if (targetSelect.options[i].value.toLowerCase() === sourceName.toLowerCase()) {
                    return i;
                }
            }
            return -1;
        };
        
        // Auto-select matching table when one is selected
        table1Select.addEventListener('change', function() {
            const matchIndex = findMatchingTable(this.value, table2Select);
            if (matchIndex > -1) {
                table2Select.selectedIndex = matchIndex;
            }
        });
        
        table2Select.addEventListener('change', function() {
            const matchIndex = findMatchingTable(this.value, table1Select);
            if (matchIndex > -1) {
                table1Select.selectedIndex = matchIndex;
            }
        });
    }
    
    // Column selection functionality
    const selectAllBtn = document.getElementById('select-all-columns');
    const deselectAllBtn = document.getElementById('deselect-all-columns');
    const columnCheckboxes = document.querySelectorAll('.column-checkbox input[type="checkbox"]');
    
    if (selectAllBtn && deselectAllBtn && columnCheckboxes.length > 0) {
        // Select all columns
        selectAllBtn.addEventListener('click', function(e) {
            e.preventDefault();
            columnCheckboxes.forEach(checkbox => {
                checkbox.checked = true;
            });
            updateSelectedCount();
        });
        
        // Deselect all columns
        deselectAllBtn.addEventListener('click', function(e) {
            e.preventDefault();
            columnCheckboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            updateSelectedCount();
        });
        
        // Update selected columns count
        const updateSelectedCount = () => {
            const selectedCount = document.querySelectorAll('.column-checkbox input[type="checkbox"]:checked').length;
            const countElement = document.getElementById('selected-columns-count');
            if (countElement) {
                countElement.textContent = selectedCount;
            }
        };
        
        // Add event listeners to all checkboxes
        columnCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateSelectedCount);
        });
        
        // Initialize count
        updateSelectedCount();
    }
    
    // Row limit slider functionality
    const rowLimitSlider = document.getElementById('row_limit');
    const rowLimitValue = document.getElementById('row_limit_value');
    
    if (rowLimitSlider && rowLimitValue) {
        rowLimitSlider.addEventListener('input', function() {
            rowLimitValue.textContent = this.value;
        });
    }
    
    // Filter columns by name
    const columnFilterInput = document.getElementById('column-filter');
    if (columnFilterInput) {
        columnFilterInput.addEventListener('input', function() {
            const filterValue = this.value.toLowerCase();
            const columnItems = document.querySelectorAll('.column-checkbox');
            
            columnItems.forEach(item => {
                const columnName = item.textContent.toLowerCase();
                if (columnName.includes(filterValue)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
    
    // Comparison results table functionality
    const diffTables = document.querySelectorAll('.diff-table');
    
    if (diffTables.length > 0) {
        // Add filter functionality to diff tables
        diffTables.forEach(table => {
            const tableId = table.id;
            const filterInput = document.getElementById(`${tableId}-filter`);
            
            if (filterInput) {
                filterInput.addEventListener('input', function() {
                    const filterValue = this.value.toLowerCase();
                    const rows = table.querySelectorAll('tbody tr');
                    
                    rows.forEach(row => {
                        const text = row.textContent.toLowerCase();
                        if (text.includes(filterValue)) {
                            row.style.display = '';
                        } else {
                            row.style.display = 'none';
                        }
                    });
                });
            }
        });
        
        // Toggle view between showing all rows and only differences
        const diffToggleBtns = document.querySelectorAll('.toggle-diff-only');
        
        diffToggleBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                
                const tableId = this.getAttribute('data-table-id');
                const table = document.getElementById(tableId);
                
                if (table) {
                    const rows = table.querySelectorAll('tbody tr');
                    const showDiffOnly = this.getAttribute('data-show-diff-only') === 'true';
                    
                    rows.forEach(row => {
                        if (showDiffOnly && !row.classList.contains('diff-row')) {
                            row.style.display = 'none';
                        } else {
                            row.style.display = '';
                        }
                    });
                    
                    // Toggle state
                    this.setAttribute('data-show-diff-only', showDiffOnly ? 'false' : 'true');
                    this.innerHTML = showDiffOnly ? 
                        '<i class="bi bi-eye"></i> Show All Rows' : 
                        '<i class="bi bi-eye-slash"></i> Show Differences Only';
                }
            });
        });
    }
    
    // Initialize any charts for data comparison
    const chartContainers = document.querySelectorAll('.chart-container');
    
    if (chartContainers.length > 0 && typeof Chart !== 'undefined') {
        chartContainers.forEach(container => {
            const canvas = container.querySelector('canvas');
            const datasetStr = container.getAttribute('data-chart');
            
            if (canvas && datasetStr) {
                try {
                    const dataset = JSON.parse(datasetStr);
                    new Chart(canvas, dataset);
                } catch (e) {
                    console.error('Error initializing chart:', e);
                }
            }
        });
    }
});
