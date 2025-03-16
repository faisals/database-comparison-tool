"""
Connection management routes for the Database Comparison Tool.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.forms.forms import ConnectionForm
from app.models.connection_repository import ConnectionRepository
from app.models.database import DatabaseConnection

connections_bp = Blueprint('connections', __name__, url_prefix='/connections')

# Initialize connection repository
connection_repository = ConnectionRepository(
    server='localhost',
    database='dbcomparetool',
    username='graph',
    password='Openup123#'
)

@connections_bp.route('/')
def list_connections():
    """List all saved database connections"""
    # Ensure the repository tables exist
    connection_repository.ensure_tables_exist()
    
    # Get all connections from the repository
    connections = connection_repository.get_all_connections()
    
    return render_template('list_connections.html', connections=connections)

@connections_bp.route('/add_connection', methods=['GET', 'POST'])
def add_connection():
    """Add a new database connection"""
    form = ConnectionForm()
    
    if form.validate_on_submit():
        connection_name = form.connection_name.data
        
        # Ensure the repository tables exist
        connection_repository.ensure_tables_exist()
        
        # Save connection to the repository
        success = connection_repository.save_connection(
            connection_name=connection_name,
            server=form.server.data,
            database=form.database.data,
            username=form.username.data,
            password=form.password.data,
            driver=form.driver.data
        )
        
        if success:
            flash(f'Connection "{connection_name}" added successfully!', 'success')
            return redirect(url_for('connections.list_connections'))
        else:
            flash('Failed to save connection. Please try again.', 'danger')
    
    return render_template('add_connection.html', form=form)

@connections_bp.route('/edit/<connection_name>', methods=['GET', 'POST'])
def edit_connection(connection_name):
    """Edit an existing database connection"""
    # Get connection from the repository
    connection = connection_repository.get_connection_by_name(connection_name)
    
    if not connection:
        flash(f'Connection "{connection_name}" not found.', 'danger')
        return redirect(url_for('connections.list_connections'))
    
    form = ConnectionForm()
    
    if request.method == 'GET':
        # Populate form with existing connection data
        form.connection_name.data = connection['name']
        form.server.data = connection['server']
        form.database.data = connection['database']
        form.username.data = connection['username']
        form.password.data = connection['password']
        form.driver.data = connection['driver']
    
    if form.validate_on_submit():
        new_connection_name = form.connection_name.data
        
        # If name changed, delete old connection and create new one
        if new_connection_name != connection_name:
            connection_repository.delete_connection(connection_name)
        
        # Save connection to the repository
        success = connection_repository.save_connection(
            connection_name=new_connection_name,
            server=form.server.data,
            database=form.database.data,
            username=form.username.data,
            password=form.password.data,
            driver=form.driver.data
        )
        
        if success:
            flash(f'Connection "{new_connection_name}" updated successfully!', 'success')
            return redirect(url_for('connections.list_connections'))
        else:
            flash('Failed to update connection. Please try again.', 'danger')
    
    return render_template('edit_connection.html', form=form, connection_name=connection_name)

@connections_bp.route('/remove/<connection_name>')
def remove_connection(connection_name):
    """Remove a saved connection"""
    # Delete connection from the repository
    success = connection_repository.delete_connection(connection_name)
    
    if success:
        flash(f'Connection "{connection_name}" removed.', 'success')
    else:
        flash(f'Failed to remove connection "{connection_name}".', 'danger')
    
    return redirect(url_for('connections.list_connections'))

@connections_bp.route('/use/<connection_name>')
def use_connection(connection_name):
    """Use a saved connection and update its last used date"""
    # Get connection from the repository
    connection = connection_repository.get_connection_by_name(connection_name)
    
    if not connection:
        flash(f'Connection "{connection_name}" not found.', 'danger')
        return redirect(url_for('connections.list_connections'))
    
    # Update last used date
    connection_repository.update_last_used_date(connection_name)
    
    # Store connection info in session for use in the application
    session['current_connection'] = {
        'name': connection['name'],
        'server': connection['server'],
        'database': connection['database'],
        'username': connection['username'],
        'password': connection['password'],
        'driver': connection['driver']
    }
    
    flash(f'Now using connection "{connection_name}".', 'success')
    return redirect(url_for('main.index'))

@connections_bp.route('/test_connection/<connection_name>')
def test_connection(connection_name):
    """Test a database connection"""
    # Get connection details from repository
    connection = connection_repository.get_connection_by_name(connection_name)
    
    if not connection:
        flash(f'Connection "{connection_name}" not found.', 'danger')
        return redirect(url_for('connections.list_connections'))
    
    # Create database connection
    db = DatabaseConnection(
        server=connection['server'],
        database=connection['database'],
        username=connection['username'],
        password=connection['password'],
        driver=connection['driver']
    )
    
    # Try to connect
    success = db.connect()
    
    if success:
        db.disconnect()
        flash(f'Successfully connected to {connection_name}!', 'success')
    else:
        flash(f'Failed to connect to {connection_name}. Please check your connection details.', 'danger')
    
    return redirect(url_for('connections.list_connections'))
