from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DecimalField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional
from models import UserRole, CarStatus, PurchaseStatus

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=64)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class CarForm(FlaskForm):
    make = StringField('Make', validators=[DataRequired(), Length(min=1, max=64)])
    model = StringField('Model', validators=[DataRequired(), Length(min=1, max=64)])
    year = IntegerField('Year', validators=[DataRequired(), NumberRange(min=1900, max=2030)])
    color = StringField('Color', validators=[DataRequired(), Length(min=1, max=32)])
    mileage = IntegerField('Mileage', validators=[DataRequired(), NumberRange(min=0)])
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)], places=2)
    vin = StringField('VIN', validators=[DataRequired(), Length(min=17, max=17)])
    fuel_type = SelectField('Fuel Type', choices=[
        ('Gasoline', 'Gasoline'),
        ('Diesel', 'Diesel'),
        ('Hybrid', 'Hybrid'),
        ('Electric', 'Electric'),
        ('Other', 'Other')
    ], default='Gasoline')
    transmission = SelectField('Transmission', choices=[
        ('Automatic', 'Automatic'),
        ('Manual', 'Manual'),
        ('CVT', 'CVT')
    ], default='Automatic')
    engine_size = StringField('Engine Size', validators=[Optional(), Length(max=16)])
    description = TextAreaField('Description', validators=[Optional()])
    status = SelectField('Status', choices=[
        (CarStatus.AVAILABLE.value, 'Available'),
        (CarStatus.SOLD.value, 'Sold'),
        (CarStatus.RESERVED.value, 'Reserved')
    ], default=CarStatus.AVAILABLE.value)
    submit = SubmitField('Save Car')

class PurchaseForm(FlaskForm):
    down_payment = DecimalField('Down Payment', validators=[DataRequired(), NumberRange(min=0)], places=2)
    financing_needed = BooleanField('Financing Required')
    notes = TextAreaField('Additional Notes', validators=[Optional()])
    submit = SubmitField('Submit Purchase Request')

class UserManagementForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=64)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    role = SelectField('Role', choices=[
        (UserRole.CUSTOMER.value, 'Customer'),
        (UserRole.SALES.value, 'Sales Representative'),
        (UserRole.ADMIN.value, 'Administrator')
    ])
    is_active = BooleanField('Active User')
    submit = SubmitField('Save User')

class PurchaseManagementForm(FlaskForm):
    status = SelectField('Status', choices=[
        (PurchaseStatus.PENDING.value, 'Pending'),
        (PurchaseStatus.APPROVED.value, 'Approved'),
        (PurchaseStatus.REJECTED.value, 'Rejected'),
        (PurchaseStatus.COMPLETED.value, 'Completed')
    ])
    sales_person_id = SelectField('Assign Sales Person', coerce=int, validators=[Optional()])
    financing_approved = BooleanField('Financing Approved')
    notes = TextAreaField('Management Notes', validators=[Optional()])
    submit = SubmitField('Update Purchase')

class SearchForm(FlaskForm):
    search_term = StringField('Search Cars', validators=[Optional()])
    make = SelectField('Make', choices=[('', 'All Makes')], validators=[Optional()])
    min_price = DecimalField('Min Price', validators=[Optional(), NumberRange(min=0)], places=2)
    max_price = DecimalField('Max Price', validators=[Optional(), NumberRange(min=0)], places=2)
    min_year = IntegerField('Min Year', validators=[Optional(), NumberRange(min=1900)])
    max_year = IntegerField('Max Year', validators=[Optional(), NumberRange(min=1900)])
    submit = SubmitField('Search')
