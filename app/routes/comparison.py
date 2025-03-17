"""
Comparison routes for the Database Comparison Tool.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from app.models.database import DatabaseConnection
from app.models.connection_repository import ConnectionRepository
from app.forms.forms import TableSelectionForm, ColumnSelectionForm, ComparisonTypeForm
from app.utils.comparison import compare_schemas as compare_table_schemas, compare_data, compare_create_table_scripts
from app.utils.formatting import format_data_as_html

import os
import json
import uuid
import tempfile

comparison_bp = Blueprint('comparison', __name__, url_prefix='/comparison')

# Create a temp directory for storing comparison results
TEMP_DIR = os.path.join(tempfile.gettempdir(), 'db_comparison_results')
os.makedirs(TEMP_DIR, exist_ok=True)

def get_temp_file_path(session_id, filename):
    """Generate a temporary file path based on session ID"""
    session_dir = os.path.join(TEMP_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    return os.path.join(session_dir, filename)

def save_comparison_data(session_id, data, filename):
    """Save comparison data to a temporary file"""
    file_path = get_temp_file_path(session_id, filename)
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return file_path

def load_comparison_data(session_id, filename):
    """Load comparison data from a temporary file"""
    file_path = get_temp_file_path(session_id, filename)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

def cleanup_temp_files(session_id):
    """Clean up temporary files for a session"""
    session_dir = os.path.join(TEMP_DIR, session_id)
    if os.path.exists(session_dir):
        for filename in os.listdir(session_dir):
            os.remove(os.path.join(session_dir, filename))
        os.rmdir(session_dir)

connection_repository = ConnectionRepository(
    server='localhost',
    database='dbcomparetool',
    username='graph',
    password='Openup123#'
)

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
    session['source_connection'] = {
        'name': conn1['name'],
        'server': conn1['server'],
        'database': conn1['database'],
        'username': conn1['username'],
        'password': conn1['password'],
        'driver': conn1['driver']
    }
    session['target_connection'] = {
        'name': conn2['name'],
        'server': conn2['server'],
        'database': conn2['database'],
        'username': conn2['username'],
        'password': conn2['password'],
        'driver': conn2['driver']
    }
    
    return render_template(
        'schema_comparison.html', 
        conn1=conn1, 
        conn2=conn2,
        comparison_in_progress=True
    )

@comparison_bp.route('/api/schema_comparison_progress', methods=['GET'])
def schema_comparison_progress():
    """API endpoint to get schema comparison progress and results"""
    try:
        # Ensure we have a session ID
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        session_id = session['session_id']
        
        # Get connection details from session
        source_conn = session.get('source_connection')
        target_conn = session.get('target_connection')
        
        # Get comparison metadata from temp storage
        metadata = load_comparison_data(session_id, 'metadata.json')
        if metadata:
            all_tables = metadata.get('all_tables')
            total_tables = metadata.get('total_tables')
        else:
            all_tables = None
            total_tables = None
        
        # If connection details are not in session, try fallback to connection names
        if not source_conn or not target_conn:
            conn1_name = session.get('connection1')
            conn2_name = session.get('connection2')
            
            if not conn1_name or not conn2_name:
                return jsonify({
                    'status': 'error',
                    'message': 'Connection details not found in session. Please start a new comparison.'
                }), 400
                
            # Get connection details from repository
            conn1 = connection_repository.get_connection_by_name(conn1_name)
            conn2 = connection_repository.get_connection_by_name(conn2_name)
            
            if not conn1 or not conn2:
                return jsonify({
                    'status': 'error',
                    'message': 'One or both selected connections do not exist.'
                }), 400
                
            # Store connection details in session for future requests
            source_conn = {
                'name': conn1['name'],
                'server': conn1['server'],
                'database': conn1['database'],
                'username': conn1['username'],
                'password': conn1['password'],
                'driver': conn1['driver']
            }
            target_conn = {
                'name': conn2['name'],
                'server': conn2['server'],
                'database': conn2['database'],
                'username': conn2['username'],
                'password': conn2['password'],
                'driver': conn2['driver']
            }
            
            session['source_connection'] = source_conn
            session['target_connection'] = target_conn
        
        # Get the offset parameter for pagination
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 25, type=int)  # Process 25 tables per request
        
        # Create database connections and process tables if no results yet or continuing pagination
        if all_tables is None or offset > 0:
            try:
                db1 = DatabaseConnection(
                    server=source_conn['server'],
                    database=source_conn['database'],
                    username=source_conn['username'],
                    password=source_conn['password'],
                    driver=source_conn['driver']
                )
                
                db2 = DatabaseConnection(
                    server=target_conn['server'],
                    database=target_conn['database'],
                    username=target_conn['username'],
                    password=target_conn['password'],
                    driver=target_conn['driver']
                )
                
                # Connect to databases
                if not db1.connect():
                    return jsonify({
                        'status': 'error',
                        'message': f'Failed to connect to {source_conn["name"]}. Please check your connection details.'
                    }), 500
                    
                if not db2.connect():
                    db1.disconnect()
                    return jsonify({
                        'status': 'error',
                        'message': f'Failed to connect to {target_conn["name"]}. Please check your connection details.'
                    }), 500
                
                try:
                    # Get all tables from both databases (only once)
                    if all_tables is None:
                        tables1 = db1.get_tables()
                        tables2 = db2.get_tables()
                        all_tables = sorted(set(tables1) | set(tables2))
                        total_tables = len(all_tables)
                        
                        # Save metadata to temp file
                        metadata = {
                            'all_tables': all_tables,
                            'total_tables': total_tables,
                            'processed_offset': 0
                        }
                        save_comparison_data(session_id, metadata, 'metadata.json')
                        
                        # Initialize results file
                        save_comparison_data(session_id, [], 'results.json')
                    
                    if total_tables == 0:
                        return jsonify({
                            'status': 'complete',
                            'progress': 100,
                            'processed_tables': 0,
                            'total_tables': 0,
                            'current_table': None,
                            'results': []
                        })
                    
                    # Process only a subset of tables for this request
                    end_idx = min(offset + limit, total_tables)
                    tables_to_process = all_tables[offset:end_idx]
                    
                    if offset < total_tables:
                        # Load existing results
                        schema_comparison = load_comparison_data(session_id, 'results.json') or []
                        
                        # Process tables in the current batch
                        for table_name in tables_to_process:
                            in_db1 = table_name in db1.get_tables()
                            in_db2 = table_name in db2.get_tables()
                            
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
                        
                        # Update schema_comparison in temp file
                        save_comparison_data(session_id, schema_comparison, 'results.json')
                        
                        # Update processed offset in metadata
                        metadata['processed_offset'] = end_idx
                        save_comparison_data(session_id, metadata, 'metadata.json')
                        
                    # Calculate progress based on the number of processed tables
                    processed_tables = min(end_idx, total_tables)
                    progress = min(100, int((processed_tables / total_tables) * 100))
                    is_complete = processed_tables >= total_tables
                    
                    # Current table being processed
                    current_table = all_tables[offset] if offset < total_tables else None
                    
                    # If comparison is complete, return the full results
                    results = None
                    if is_complete:
                        results = load_comparison_data(session_id, 'results.json')
                    
                    # Return the results
                    return jsonify({
                        'status': 'in_progress' if not is_complete else 'complete',
                        'progress': progress,
                        'processed_tables': processed_tables,
                        'total_tables': total_tables,
                        'current_table': current_table,
                        'next_offset': end_idx if not is_complete else None,
                        'results': results
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
                    
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to initialize database connections: {str(e)}'
                }), 500
        else:
            # We already have metadata from a previous request
            # Load current results
            schema_comparison = load_comparison_data(session_id, 'results.json') or []
            processed_tables = len(schema_comparison)
            progress = min(100, int((processed_tables / total_tables) * 100))
            is_complete = processed_tables >= total_tables
            
            # Return the current progress
            return jsonify({
                'status': 'in_progress' if not is_complete else 'complete',
                'progress': progress,
                'processed_tables': processed_tables,
                'total_tables': total_tables,
                'current_table': all_tables[offset] if offset < len(all_tables) else None,
                'next_offset': offset + limit if not is_complete else None,
                'results': schema_comparison if is_complete else None
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }), 500

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

@comparison_bp.route('/schema/scripts/<table_name>', methods=['GET'])
def get_table_scripts(table_name):
    """Get CREATE TABLE scripts for a specific table"""
    try:
        # Ensure we have a session ID
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        # Get connection details from session
        source_conn = session.get('source_connection')
        target_conn = session.get('target_connection')
        
        # If connection details are not in session, try fallback to connection names
        if not source_conn or not target_conn:
            conn1_name = session.get('connection1')
            conn2_name = session.get('connection2')
            
            if not conn1_name or not conn2_name:
                return jsonify({
                    'status': 'error',
                    'message': 'Connection details not found in session. Please start a new comparison.'
                }), 400
                
            # Get connection details from repository
            conn1 = connection_repository.get_connection_by_name(conn1_name)
            conn2 = connection_repository.get_connection_by_name(conn2_name)
            
            if not conn1 or not conn2:
                return jsonify({
                    'status': 'error',
                    'message': 'One or both selected connections do not exist.'
                }), 400
                
            # Store connection details in session for future requests
            source_conn = {
                'name': conn1['name'],
                'server': conn1['server'],
                'database': conn1['database'],
                'username': conn1['username'],
                'password': conn1['password'],
                'driver': conn1['driver']
            }
            target_conn = {
                'name': conn2['name'],
                'server': conn2['server'],
                'database': conn2['database'],
                'username': conn2['username'],
                'password': conn2['password'],
                'driver': conn2['driver']
            }
            
            session['source_connection'] = source_conn
            session['target_connection'] = target_conn
        
        # Create database connections
        db1 = DatabaseConnection(
            server=source_conn['server'],
            database=source_conn['database'],
            username=source_conn['username'],
            password=source_conn['password'],
            driver=source_conn['driver']
        )
        
        db2 = DatabaseConnection(
            server=target_conn['server'],
            database=target_conn['database'],
            username=target_conn['username'],
            password=target_conn['password'],
            driver=target_conn['driver']
        )
        
        source_script = None
        target_script = None
        
        try:
            # Connect to source database
            if db1.connect():
                # Check if table exists in source
                tables1 = db1.get_tables()
                if table_name in tables1:
                    source_script = db1.get_create_table_script(table_name)
            
            # Connect to target database
            if db2.connect():
                # Check if table exists in target
                tables2 = db2.get_tables()
                if table_name in tables2:
                    target_script = db2.get_create_table_script(table_name)
            
            return jsonify({
                'status': 'success',
                'source_script': source_script,
                'target_script': target_script
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            
            return jsonify({
                'status': 'error',
                'message': f'Error generating scripts: {str(e)}'
            }), 500
            
        finally:
            # Disconnect from databases
            db1.disconnect()
            db2.disconnect()
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to initialize database connections: {str(e)}'
        }), 500

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
