"""
Comparison routes for the Database Comparison Tool.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from app.models.database import DatabaseConnection
from app.models.connection_repository import ConnectionRepository
from app.forms.forms import TableSelectionForm, ColumnSelectionForm, ComparisonTypeForm
from app.utils.comparison import compare_schemas as compare_table_schemas, compare_data
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
def compare_db_data(db1, db2, table1, table2, selected_columns):
    """Compare data between two database tables"""
    # Get data for both tables
    data1 = db1.get_table_data(table1, selected_columns)
    data2 = db2.get_table_data(table2, selected_columns)
    
    # Use the utility function to compare the data
    return compare_data(data1, data2, selected_columns)

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
        flash(f'Failed to connect to {conn1_name}. Please check your connection details.', 'danger')
        return redirect(url_for('main.index'))
        
    if not db2.connect():
        db1.disconnect()
        flash(f'Failed to connect to {conn2_name}. Please check your connection details.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all tables from both databases
    tables1 = db1.get_tables()
    tables2 = db2.get_tables()
    
    # Compare schemas
    schema_comparison = []
    all_tables = sorted(set(tables1) | set(tables2))
    
    for table_name in all_tables:
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
                'differences': True
            })
    
    # Disconnect from databases
    db1.disconnect()
    db2.disconnect()
    
    return render_template(
        'schema_comparison.html', 
        conn1=conn1, 
        conn2=conn2, 
        schema_comparison=schema_comparison
    )

@comparison_bp.route('/select_tables', methods=['GET', 'POST'])
def select_tables():
    """Select tables to compare"""
    # Check if comparison type is set and is 'data'
    comparison_type = session.get('comparison_type')
    if not comparison_type:
        return redirect(url_for('comparison.select_comparison_type'))
    
    if comparison_type != 'data':
        return redirect(url_for('comparison.select_comparison_type'))
    
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
        flash(f'Failed to connect to source database: {conn1_name}', 'danger')
        return redirect(url_for('main.index'))
    
    if not db2.connect():
        db1.disconnect()
        flash(f'Failed to connect to target database: {conn2_name}', 'danger')
        return redirect(url_for('main.index'))
    
    # Get tables from both databases
    tables1 = db1.get_tables()
    tables2 = db2.get_tables()
    
    # Create form
    form = TableSelectionForm()
    form.table1.choices = [(t, t) for t in tables1]
    form.table2.choices = [(t, t) for t in tables2]
    
    if form.validate_on_submit():
        table1 = form.table1.data
        table2 = form.table2.data
        
        # Store selected tables in session
        session['selected_tables'] = {
            'conn1': conn1_name,
            'conn2': conn2_name,
            'table1': table1,
            'table2': table2
        }
        
        # Clean up connections
        db1.disconnect()
        db2.disconnect()
        
        # Redirect to column selection page
        return redirect(url_for('comparison.select_columns'))
    
    # Clean up connections
    db1.disconnect()
    db2.disconnect()
    
    return render_template('select_tables.html', form=form, conn1=conn1_name, conn2=conn2_name)

@comparison_bp.route('/select_columns', methods=['GET', 'POST'])
def select_columns():
    """Select columns to compare"""
    # Get selected tables from session
    selected_tables = session.get('selected_tables')
    if not selected_tables:
        flash('Please select tables to compare first.', 'danger')
        return redirect(url_for('main.index'))
    
    conn1_name = selected_tables['conn1']
    conn2_name = selected_tables['conn2']
    table1 = selected_tables['table1']
    table2 = selected_tables['table2']
    
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
    if not db1.connect() or not db2.connect():
        flash('Failed to connect to databases.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get schemas for both tables
    source_schema = db1.get_table_schema(table1)
    target_schema = db2.get_table_schema(table2)
    
    # Get all unique column names
    all_columns = sorted(list(set([col['name'] for col in source_schema] + [col['name'] for col in target_schema])))
    
    # Create form with all columns
    form = ColumnSelectionForm()
    form.columns.choices = [(col, col) for col in all_columns]
    
    if form.validate_on_submit():
        selected_columns = form.columns.data
        compare_data_flag = form.compare_data.data
        
        # Store selections in session
        session['comparison_options'] = {
            'selected_columns': selected_columns,
            'compare_data': compare_data_flag
        }
        
        # Clean up connections
        db1.disconnect()
        db2.disconnect()
        
        # Redirect to results page
        return redirect(url_for('comparison.compare_results'))
    
    # Clean up connections
    db1.disconnect()
    db2.disconnect()
    
    return render_template(
        'select_columns.html', 
        form=form, 
        source_connection=conn1_name,
        target_connection=conn2_name,
        table1=table1, 
        table2=table2,
        source_schema=source_schema,
        target_schema=target_schema
    )

@comparison_bp.route('/compare_results', methods=['GET'])
def compare_results():
    """Display comparison results"""
    # Get selected tables and columns from session
    selected_tables = session.get('selected_tables')
    comparison_options = session.get('comparison_options')
    
    if not selected_tables or not comparison_options:
        flash('Please select tables and columns to compare first.', 'danger')
        return redirect(url_for('main.index'))
    
    conn1_name = selected_tables['conn1']
    conn2_name = selected_tables['conn2']
    table1 = selected_tables['table1']
    table2 = selected_tables['table2']
    selected_columns = comparison_options['selected_columns']
    compare_data_flag = comparison_options['compare_data']
    
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
    if not db1.connect() or not db2.connect():
        flash('Failed to connect to databases.', 'danger')
        return redirect(url_for('main.index'))
    
    # Compare schemas
    schema_diff = compare_db_schemas(db1, db2, table1, table2, selected_columns)
    
    # Compare data if requested
    if compare_data_flag:
        data_diff = compare_db_data(db1, db2, table1, table2, selected_columns)
    else:
        data_diff = None
    
    # Clean up connections
    db1.disconnect()
    db2.disconnect()
    
    # Render results
    return render_template(
        'compare_results.html', 
        source_connection=conn1_name,
        target_connection=conn2_name,
        table1=table1, 
        table2=table2,
        schema_diff=schema_diff,
        data_diff=data_diff
    )
