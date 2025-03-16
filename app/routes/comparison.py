"""
Comparison routes for the Database Comparison Tool.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify

from app.models.database import DatabaseConnection
from app.models.connection_repository import ConnectionRepository
from app.forms.forms import TableSelectionForm, ColumnSelectionForm, ComparisonTypeForm
from app.utils.comparison import compare_schemas as compare_table_schemas, compare_data, compare_create_table_scripts
from app.utils.formatting import format_data_as_html

comparison_bp = Blueprint('comparison', __name__, url_prefix='/comparison')

# Helper function for database schema comparison
def compare_db_schemas(db1, db2, table1, table2, selected_columns):
    """Compare schemas between two database tables"""
    # Get schema for both tables
    schema1 = db1.get_table_schema(table1)
    schema2 = db2.get_table_schema(table2)
    
    # Filter schemas to only include selected columns if any are specified
    if selected_columns:
        schema1 = [col for col in schema1 if col['name'] in selected_columns]
        schema2 = [col for col in schema2 if col['name'] in selected_columns]
    
    # Use the utility function to compare the schemas
    return compare_table_schemas(schema1, schema2)

# Helper function for database data comparison
def compare_db_data(db1, db2, table1, table2, selected_columns, row_limit=50):
    """Compare data between two database tables"""
    # Get data for both tables
    data1 = db1.get_table_data(table1, columns=selected_columns, limit=row_limit)
    data2 = db2.get_table_data(table2, columns=selected_columns, limit=row_limit)
    
    # Use the utility function to compare the data
    return compare_data(data1, data2, selected_columns)

def compare_data_directly(data1, data2, selected_columns):
    """Direct comparison of data between two tables, without using the utility function"""
    # Create a simple comparison structure
    differences = []
    rows_with_differences = 0
    
    # Get the minimum number of rows to compare
    min_rows = min(len(data1['rows']), len(data2['rows']))
    
    # Compare each row
    for i in range(min_rows):
        row1 = data1['rows'][i]
        row2 = data2['rows'][i]
        
        # Check for differences in this row
        row_diffs = {}
        for col in selected_columns:
            val1 = row1.get(col)
            val2 = row2.get(col)
            
            # Compare values (handle None/NULL)
            if val1 != val2:
                row_diffs[col] = {
                    'source': 'NULL' if val1 is None else str(val1),
                    'target': 'NULL' if val2 is None else str(val2)
                }
        
        # If differences found, add to the list
        if row_diffs:
            differences.append({
                'row_index': i,
                'differences': row_diffs
            })
            rows_with_differences += 1
    
    # Create comparison result structure
    return {
        'summary': {
            'source_total_rows': data1['total_rows'],
            'target_total_rows': data2['total_rows'],
            'total_rows_compared': min_rows,
            'rows_with_differences': rows_with_differences,
            'columns_compared': selected_columns,
            'row_count_difference': abs(data1['total_rows'] - data2['total_rows'])
        },
        'columns': selected_columns,
        'source_data': data1,
        'target_data': data2,
        'data_differences': differences
    }

# Initialize connection repository
connection_repository = ConnectionRepository(
    server='localhost',
    database='dbcomparetool',
    username='graph',
    password='Openup123#'
)

@comparison_bp.route('/select_comparison_type', methods=['GET', 'POST'])
def select_comparison_type():
    """Select the type of comparison to perform"""
    # Get connection names from session
    conn1_name = session.get('connection1')
    conn2_name = session.get('connection2')
    
    if not conn1_name or not conn2_name:
        flash('Please select two connections to compare.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get connection details from repository
    conn1 = connection_repository.get_connection_by_name(conn1_name)
    conn2 = connection_repository.get_connection_by_name(conn2_name)
    
    if not conn1 or not conn2:
        flash('One or both selected connections do not exist.', 'danger')
        return redirect(url_for('main.index'))
    
    form = ComparisonTypeForm()
    
    if form.validate_on_submit():
        # Store comparison type in session
        session['comparison_type'] = form.comparison_type.data
        
        if form.comparison_type.data == 'schema':
            # Redirect to schema comparison
            return redirect(url_for('comparison.compare_schemas'))
        else:
            # Redirect to table selection for data comparison
            return redirect(url_for('comparison.select_tables'))
    
    return render_template('select_comparison_type.html', form=form, conn1=conn1, conn2=conn2)

@comparison_bp.route('/compare_schemas', methods=['GET'])
def compare_schemas():
    """Compare database schemas"""
    # Get connection names from session
    conn1_name = session.get('connection1')
    conn2_name = session.get('connection2')
    
    if not conn1_name or not conn2_name:
        flash('Please select two connections to compare.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get connection details from repository
    conn1 = connection_repository.get_connection_by_name(conn1_name)
    conn2 = connection_repository.get_connection_by_name(conn2_name)
    
    if not conn1 or not conn2:
        flash('One or both selected connections do not exist.', 'danger')
        return redirect(url_for('main.index'))
    
    # Store connection details in session for the AJAX endpoint
    session['conn1'] = conn1
    session['conn2'] = conn2
    
    return render_template(
        'schema_comparison.html', 
        conn1=conn1, 
        conn2=conn2,
        comparison_in_progress=True
    )

@comparison_bp.route('/api/schema_comparison_progress', methods=['GET'])
def schema_comparison_progress():
    """API endpoint to get schema comparison progress and results"""
    # Get connection details from session
    conn1 = session.get('conn1')
    conn2 = session.get('conn2')
    
    if not conn1 or not conn2:
        return jsonify({
            'status': 'error',
            'message': 'Connection details not found in session'
        }), 400
    
    # Create database connections
    db1 = DatabaseConnection(
        server=conn1['server'],
        database=conn1['database'],
        username=conn1['username'],
        password=conn1['password'],
        driver=conn1['driver']
    )
    
    db2 = DatabaseConnection(
        server=conn2['server'],
        database=conn2['database'],
        username=conn2['username'],
        password=conn2['password'],
        driver=conn2['driver']
    )
    
    # Connect to databases
    if not db1.connect():
        return jsonify({
            'status': 'error',
            'message': f'Failed to connect to {conn1["name"]}. Please check your connection details.'
        }), 500
        
    if not db2.connect():
        db1.disconnect()
        return jsonify({
            'status': 'error',
            'message': f'Failed to connect to {conn2["name"]}. Please check your connection details.'
        }), 500
    
    try:
        # Get all tables from both databases
        tables1 = db1.get_tables()
        tables2 = db2.get_tables()
        
        # Compare schemas
        schema_comparison = []
        all_tables = sorted(set(tables1) | set(tables2))
        total_tables = len(all_tables)
        
        # Get the offset parameter for pagination
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # Calculate end index, ensuring it doesn't exceed the total
        end_index = min(offset + limit, total_tables)
        
        # Get the subset of tables to process in this batch
        current_tables = all_tables[offset:end_index]
        
        # Process the current batch of tables
        for table_name in current_tables:
            in_db1 = table_name in tables1
            in_db2 = table_name in tables2
            
            if in_db1 and in_db2:
                # Get schema for both tables
                schema1 = db1.get_table_schema(table_name)
                schema2 = db2.get_table_schema(table_name)
                
                # Compare columns
                column_comparison = compare_table_schemas(schema1, schema2)
                
                schema_comparison.append({
                    'table_name': table_name,
                    'in_db1': True,
                    'in_db2': True,
                    'columns': column_comparison.get('differences', []),
                    'differences': len(column_comparison.get('differences', [])) > 0
                })
            else:
                schema_comparison.append({
                    'table_name': table_name,
                    'in_db1': in_db1,
                    'in_db2': in_db2,
                    'columns': [],
                    'differences': in_db1 != in_db2
                })
        
        # Calculate progress
        progress = min(100, int((end_index / total_tables) * 100))
        
        # Check if we've processed all tables
        is_complete = end_index >= total_tables
        
        # Return the results
        return jsonify({
            'status': 'success',
            'progress': progress,
            'processed_tables': end_index,
            'total_tables': total_tables,
            'current_batch': schema_comparison,
            'is_complete': is_complete,
            'next_offset': end_index if not is_complete else None
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'status': 'error',
            'message': f'An error occurred during comparison: {str(e)}'
        }), 500
        
    finally:
        # Disconnect from databases
        db1.disconnect()
        db2.disconnect()

@comparison_bp.route('/api/create_table_script/<table_name>', methods=['GET'])
def get_create_table_script(table_name):
    """API endpoint to get and compare CREATE TABLE scripts for a specific table"""
    # Get connection details from session
    conn1 = session.get('conn1')
    conn2 = session.get('conn2')
    
    if not conn1 or not conn2:
        return jsonify({
            'status': 'error',
            'message': 'Connection details not found in session'
        }), 400
    
    # Create database connections
    db1 = DatabaseConnection(
        server=conn1['server'],
        database=conn1['database'],
        username=conn1['username'],
        password=conn1['password'],
        driver=conn1['driver']
    )
    
    db2 = DatabaseConnection(
        server=conn2['server'],
        database=conn2['database'],
        username=conn2['username'],
        password=conn2['password'],
        driver=conn2['driver']
    )
    
    # Connect to databases
    if not db1.connect():
        return jsonify({
            'status': 'error',
            'message': f'Failed to connect to {conn1["name"]}. Please check your connection details.'
        }), 500
        
    if not db2.connect():
        db1.disconnect()
        return jsonify({
            'status': 'error',
            'message': f'Failed to connect to {conn2["name"]}. Please check your connection details.'
        }), 500
    
    try:
        # Get CREATE TABLE scripts for the table from both databases
        script1 = db1.get_create_table_script(table_name)
        script2 = db2.get_create_table_script(table_name)
        
        # Compare the scripts
        script_comparison = compare_create_table_scripts(script1, script2)
        
        # Return the results
        return jsonify({
            'status': 'success',
            'comparison': script_comparison
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'status': 'error',
            'message': f'An error occurred during script comparison: {str(e)}'
        }), 500
        
    finally:
        # Disconnect from databases
        db1.disconnect()
        db2.disconnect()

@comparison_bp.route('/select_tables', methods=['GET', 'POST'])
def select_tables():
    """Select tables to compare"""
    # Get connection names from session
    conn1_name = session.get('connection1')
    conn2_name = session.get('connection2')
    
    if not conn1_name or not conn2_name:
        flash('Please select two connections to compare.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get connection details from repository
    conn1 = connection_repository.get_connection_by_name(conn1_name)
    conn2 = connection_repository.get_connection_by_name(conn2_name)
    
    if not conn1 or not conn2:
        flash('One or both selected connections do not exist.', 'danger')
        return redirect(url_for('main.index'))
    
    # Create database connections
    db1 = DatabaseConnection(
        server=conn1['server'],
        database=conn1['database'],
        username=conn1['username'],
        password=conn1['password'],
        driver=conn1['driver']
    )
    
    db2 = DatabaseConnection(
        server=conn2['server'],
        database=conn2['database'],
        username=conn2['username'],
        password=conn2['password'],
        driver=conn2['driver']
    )
    
    # Connect to databases
    if not db1.connect():
        flash(f'Failed to connect to {conn1["name"]}. Please check your connection details.', 'danger')
        return redirect(url_for('main.index'))
        
    if not db2.connect():
        db1.disconnect()
        flash(f'Failed to connect to {conn2["name"]}. Please check your connection details.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Get tables from both databases
        tables1 = db1.get_tables()
        tables2 = db2.get_tables()
        
        # Create form with dynamic choices
        form = TableSelectionForm()
        form.table1.choices = [(table, table) for table in tables1]
        form.table2.choices = [(table, table) for table in tables2]
        
        if form.validate_on_submit():
            # Store selected tables in session
            session['table1'] = form.table1.data
            session['table2'] = form.table2.data
            
            # Redirect to column selection
            return redirect(url_for('comparison.select_columns'))
        
        return render_template(
            'select_tables.html', 
            form=form, 
            conn1=conn1, 
            conn2=conn2,
            tables1=tables1,
            tables2=tables2
        )
        
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('main.index'))
        
    finally:
        # Disconnect from databases
        db1.disconnect()
        db2.disconnect()

@comparison_bp.route('/select_columns', methods=['GET', 'POST'])
def select_columns():
    """Select columns to compare"""
    # Get connection and table names from session
    conn1_name = session.get('connection1')
    conn2_name = session.get('connection2')
    table1 = session.get('table1')
    table2 = session.get('table2')
    
    if not conn1_name or not conn2_name or not table1 or not table2:
        flash('Please select connections and tables to compare.', 'danger')
        return redirect(url_for('comparison.select_tables'))
    
    # Get connection details from repository
    conn1 = connection_repository.get_connection_by_name(conn1_name)
    conn2 = connection_repository.get_connection_by_name(conn2_name)
    
    if not conn1 or not conn2:
        flash('One or both selected connections do not exist.', 'danger')
        return redirect(url_for('main.index'))
    
    # Create database connections
    db1 = DatabaseConnection(
        server=conn1['server'],
        database=conn1['database'],
        username=conn1['username'],
        password=conn1['password'],
        driver=conn1['driver']
    )
    
    db2 = DatabaseConnection(
        server=conn2['server'],
        database=conn2['database'],
        username=conn2['username'],
        password=conn2['password'],
        driver=conn2['driver']
    )
    
    # Connect to databases
    if not db1.connect():
        flash(f'Failed to connect to {conn1["name"]}. Please check your connection details.', 'danger')
        return redirect(url_for('main.index'))
        
    if not db2.connect():
        db1.disconnect()
        flash(f'Failed to connect to {conn2["name"]}. Please check your connection details.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Get schema for both tables
        schema1 = db1.get_table_schema(table1)
        schema2 = db2.get_table_schema(table2)
        
        # Extract column names
        columns1 = [col['name'] for col in schema1]
        columns2 = [col['name'] for col in schema2]
        
        # Find common columns
        common_columns = list(set(columns1) & set(columns2))
        
        # Handle form submission
        if request.method == 'POST':
            # Get selected columns from form
            selected_columns = request.form.getlist('columns')
            row_limit = int(request.form.get('row_limit', 50))
            compare_data = request.form.get('compare_data') == 'on'
            
            # Store in session
            session['selected_columns'] = selected_columns
            session['row_limit'] = row_limit
            session['compare_data'] = compare_data
            
            # Redirect to comparison results
            return redirect(url_for('comparison.compare_results'))
        
        # Create form with dynamic choices
        form = ColumnSelectionForm()
        form.columns.choices = [(col, col) for col in common_columns]
        
        return render_template(
            'select_columns.html', 
            form=form, 
            conn1=conn1, 
            conn2=conn2,
            table1=table1,
            table2=table2,
            common_columns=common_columns,
            only_in_table1=list(set(columns1) - set(columns2)),
            only_in_table2=list(set(columns2) - set(columns1)),
            source_schema=schema1,
            target_schema=schema2,
            source_connection=conn1['name'],
            target_connection=conn2['name']
        )
        
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('comparison.select_tables'))
        
    finally:
        # Disconnect from databases
        db1.disconnect()
        db2.disconnect()

@comparison_bp.route('/compare_results', methods=['GET'])
def compare_results():
    """Display comparison results"""
    # Get connection, table, and column names from session
    conn1_name = session.get('connection1')
    conn2_name = session.get('connection2')
    table1 = session.get('table1')
    table2 = session.get('table2')
    selected_columns = session.get('selected_columns', [])
    row_limit = session.get('row_limit', 50)
    
    print(f"DEBUG: Selected columns from session: {selected_columns}")
    print(f"DEBUG: Row limit: {row_limit}")
    
    if not conn1_name or not conn2_name or not table1 or not table2:
        flash('Please select connections and tables to compare.', 'danger')
        return redirect(url_for('comparison.select_tables'))
    
    if not selected_columns:
        flash('Please select at least one column to compare.', 'warning')
        return redirect(url_for('comparison.select_columns'))
    
    # Get connection details from repository
    conn1 = connection_repository.get_connection_by_name(conn1_name)
    conn2 = connection_repository.get_connection_by_name(conn2_name)
    
    if not conn1 or not conn2:
        flash('One or both selected connections do not exist.', 'danger')
        return redirect(url_for('main.index'))
    
    # Create database connections
    db1 = DatabaseConnection(
        server=conn1['server'],
        database=conn1['database'],
        username=conn1['username'],
        password=conn1['password'],
        driver=conn1['driver']
    )
    
    db2 = DatabaseConnection(
        server=conn2['server'],
        database=conn2['database'],
        username=conn2['username'],
        password=conn2['password'],
        driver=conn2['driver']
    )
    
    # Connect to databases
    if not db1.connect():
        flash(f'Failed to connect to {conn1["name"]}. Please check your connection details.', 'danger')
        return redirect(url_for('main.index'))
        
    if not db2.connect():
        db1.disconnect()
        flash(f'Failed to connect to {conn2["name"]}. Please check your connection details.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Verify selected columns exist in both tables
        schema1 = db1.get_table_schema(table1)
        schema2 = db2.get_table_schema(table2)
        
        columns1 = [col['name'] for col in schema1]
        columns2 = [col['name'] for col in schema2]
        
        # Filter selected columns to only those that exist in both tables
        valid_columns = [col for col in selected_columns if col in columns1 and col in columns2]
        
        if not valid_columns:
            flash('None of the selected columns exist in both tables.', 'warning')
            return redirect(url_for('comparison.select_columns'))
        
        print(f"DEBUG: Valid columns for comparison: {valid_columns}")
        
        # Get data for both tables with valid columns
        try:
            data1 = db1.get_table_data(table1, columns=valid_columns, limit=row_limit)
            data2 = db2.get_table_data(table2, columns=valid_columns, limit=row_limit)
            
            print(f"DEBUG: Data1 keys: {data1.keys() if data1 else 'None'}")
            print(f"DEBUG: Data2 keys: {data2.keys() if data2 else 'None'}")
            print(f"DEBUG: Data1 columns: {data1.get('columns', [])}")
            print(f"DEBUG: Data2 columns: {data2.get('columns', [])}")
            print(f"DEBUG: Data1 row count: {data1.get('total_rows', 0)}")
            print(f"DEBUG: Data2 row count: {data2.get('total_rows', 0)}")
            
            try:
                # Try using our direct comparison function
                comparison_result = compare_data_directly(data1, data2, valid_columns)
                print(f"DEBUG: Direct comparison result: {comparison_result.keys()}")
            except Exception as compare_error:
                print(f"DEBUG: Error in direct comparison: {str(compare_error)}")
                # Fall back to a very simple structure
                comparison_result = {
                    'summary': {
                        'source_total_rows': data1.get('total_rows', 0),
                        'target_total_rows': data2.get('total_rows', 0),
                        'total_rows_compared': 0,
                        'rows_with_differences': 0,
                        'columns_compared': valid_columns,
                        'row_count_difference': abs(data1.get('total_rows', 0) - data2.get('total_rows', 0))
                    },
                    'columns': valid_columns,
                    'data_differences': []
                }
                print(f"DEBUG: Fallback comparison created with keys: {comparison_result.keys()}")
            
            # Format data for display
            try:
                formatted_data = format_data_as_html(comparison_result)
                print(f"DEBUG: Formatted data length: {len(formatted_data)}")
            except Exception as format_error:
                print(f"DEBUG: Error formatting data: {str(format_error)}")
                formatted_data = "<div class='alert alert-warning'>Error formatting comparison data.</div>"
            
            return render_template(
                'data_comparison.html', 
                conn1=conn1, 
                conn2=conn2,
                table1=table1,
                table2=table2,
                selected_columns=valid_columns,
                comparison_result=comparison_result,
                formatted_data=formatted_data
            )
            
        except Exception as e:
            print(f"DEBUG: Error in data comparison: {str(e)}")
            flash(f'Error comparing data: {str(e)}', 'danger')
            return redirect(url_for('comparison.select_columns'))
        
    except Exception as e:
        print(f"DEBUG: Error in compare_results: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('comparison.select_columns'))
        
    finally:
        # Disconnect from databases
        db1.disconnect()
        db2.disconnect()
