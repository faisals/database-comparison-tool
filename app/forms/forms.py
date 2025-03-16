"""
Forms for the Database Comparison Tool.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SelectMultipleField, SubmitField, widgets
from wtforms.validators import DataRequired, Length

class ConnectionForm(FlaskForm):
    """Form for adding a new database connection"""
    connection_name = StringField('Connection Name', validators=[DataRequired(), Length(min=1, max=50)])
    server = StringField('Server', validators=[DataRequired()])
    database = StringField('Database', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    driver = StringField('Driver', default='ODBC Driver 17 for SQL Server')
    submit = SubmitField('Add Connection')

class DatabaseSelectionForm(FlaskForm):
    """Form for selecting database connections to compare"""
    connection1 = SelectField('Source Connection', validators=[DataRequired()])
    connection2 = SelectField('Target Connection', validators=[DataRequired()])
    submit = SubmitField('Compare Databases')

class TableSelectionForm(FlaskForm):
    """Form for selecting tables to compare"""
    table1 = SelectField('Source Table', validators=[DataRequired()])
    table2 = SelectField('Target Table', validators=[DataRequired()])
    submit = SubmitField('Select Tables')

class MultiCheckboxField(SelectMultipleField):
    """Custom field for multiple checkbox selection"""
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class ColumnSelectionForm(FlaskForm):
    """Form for selecting columns to compare"""
    columns = MultiCheckboxField('Columns to Compare')
    compare_data = BooleanField('Compare Data', default=True)
    submit = SubmitField('Compare Columns')

class ComparisonTypeForm(FlaskForm):
    """Form for selecting the type of comparison to perform"""
    comparison_type = SelectField(
        'Comparison Type', 
        choices=[
            ('schema', 'Database Schema Comparison (Tables Only)'),
            ('data', 'Table Data Comparison')
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Continue')
