"""
Main routes for the Database Comparison Tool.
"""
from flask import Blueprint, render_template, session, redirect, url_for, request

from app.forms.forms import DatabaseSelectionForm
from app.models.connection_repository import ConnectionRepository

main_bp = Blueprint('main', __name__)

# Initialize connection repository
connection_repository = ConnectionRepository(
    server='localhost',
    database='dbcomparetool',
    username='graph',
    password='Openup123#'
)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """Home page with saved connections"""
    # Ensure the repository tables exist
    connection_repository.ensure_tables_exist()
    
    # Get all connections from the repository
    all_connections = connection_repository.get_all_connections()
    
    # Create form with connection choices
    form = DatabaseSelectionForm()
    
    # Check if we have any connections
    no_connections = len(all_connections) == 0
    
    # Populate connection choices only if we have connections
    if not no_connections:
        connection_choices = [(conn['name'], conn['name']) for conn in all_connections]
        form.connection1.choices = connection_choices
        form.connection2.choices = connection_choices
        
        if form.validate_on_submit():
            # Store only the connection names in session
            session['connection1'] = form.connection1.data
            session['connection2'] = form.connection2.data
            
            # Update last used date
            connection_repository.update_last_used_date(form.connection1.data)
            connection_repository.update_last_used_date(form.connection2.data)
            
            return redirect(url_for('comparison.select_comparison_type'))
    
    return render_template('index.html', form=form, connections=all_connections, no_connections=no_connections)
