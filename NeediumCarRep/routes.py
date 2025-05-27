from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import or_, and_
from app import db
from models import User, Car, Purchase, UserRole, CarStatus, PurchaseStatus
from forms import (LoginForm, RegistrationForm, CarForm, PurchaseForm, 
                  UserManagementForm, PurchaseManagementForm, SearchForm)
from functools import wraps

# Create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def sales_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (not current_user.is_admin() and not current_user.is_sales()):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Main routes
@main_bp.route('/')
def index():
    # Get featured cars (latest 6 available cars)
    featured_cars = Car.query.filter_by(status=CarStatus.AVAILABLE).order_by(Car.created_at.desc()).limit(6).all()
    return render_template('index.html', featured_cars=featured_cars)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        # Admin dashboard stats
        total_users = User.query.count()
        total_cars = Car.query.count()
        available_cars = Car.query.filter_by(status=CarStatus.AVAILABLE).count()
        pending_purchases = Purchase.query.filter_by(status=PurchaseStatus.PENDING).count()
        recent_purchases = Purchase.query.order_by(Purchase.created_at.desc()).limit(5).all()
        
        return render_template('dashboard.html', 
                             total_users=total_users,
                             total_cars=total_cars,
                             available_cars=available_cars,
                             pending_purchases=pending_purchases,
                             recent_purchases=recent_purchases)
    
    elif current_user.is_sales():
        # Sales dashboard
        my_sales = Purchase.query.filter_by(sales_person_id=current_user.id).count()
        pending_assignments = Purchase.query.filter(
            Purchase.status == PurchaseStatus.PENDING,
            Purchase.sales_person_id.is_(None)
        ).count()
        my_pending = Purchase.query.filter_by(
            sales_person_id=current_user.id,
            status=PurchaseStatus.PENDING
        ).count()
        recent_purchases = Purchase.query.filter_by(sales_person_id=current_user.id).order_by(Purchase.created_at.desc()).limit(5).all()
        
        return render_template('dashboard.html',
                             my_sales=my_sales,
                             pending_assignments=pending_assignments,
                             my_pending=my_pending,
                             recent_purchases=recent_purchases)
    
    else:
        # Customer dashboard
        my_purchases = Purchase.query.filter_by(customer_id=current_user.id).order_by(Purchase.created_at.desc()).all()
        return render_template('dashboard.html', my_purchases=my_purchases)

@main_bp.route('/inventory')
def inventory():
    form = SearchForm()
    
    # Get all unique makes for filter dropdown
    makes = db.session.query(Car.make.distinct()).order_by(Car.make).all()
    form.make.choices = [('', 'All Makes')] + [(make[0], make[0]) for make in makes]
    
    # Start with base query for available cars
    query = Car.query.filter_by(status=CarStatus.AVAILABLE)
    
    # Apply filters if form is submitted
    if form.validate_on_submit():
        if form.search_term.data:
            search = f"%{form.search_term.data}%"
            query = query.filter(or_(
                Car.make.ilike(search),
                Car.model.ilike(search),
                Car.description.ilike(search)
            ))
        
        if form.make.data:
            query = query.filter(Car.make == form.make.data)
        
        if form.min_price.data:
            query = query.filter(Car.price >= form.min_price.data)
        
        if form.max_price.data:
            query = query.filter(Car.price <= form.max_price.data)
        
        if form.min_year.data:
            query = query.filter(Car.year >= form.min_year.data)
        
        if form.max_year.data:
            query = query.filter(Car.year <= form.max_year.data)
    
    cars = query.order_by(Car.created_at.desc()).all()
    return render_template('inventory.html', cars=cars, form=form)

@main_bp.route('/car/<int:car_id>')
def car_detail(car_id):
    car = Car.query.get_or_404(car_id)
    return render_template('car_detail.html', car=car)

@main_bp.route('/purchase/<int:car_id>', methods=['GET', 'POST'])
@login_required
def purchase_car(car_id):
    car = Car.query.get_or_404(car_id)
    
    if car.status != CarStatus.AVAILABLE:
        flash('This car is no longer available for purchase.', 'error')
        return redirect(url_for('main.inventory'))
    
    # Check if user already has a pending purchase for this car
    existing_purchase = Purchase.query.filter_by(
        customer_id=current_user.id,
        car_id=car_id,
        status=PurchaseStatus.PENDING
    ).first()
    
    if existing_purchase:
        flash('You already have a pending purchase request for this car.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    form = PurchaseForm()
    
    if form.validate_on_submit():
        purchase = Purchase(
            customer_id=current_user.id,
            car_id=car_id,
            purchase_price=car.price,
            down_payment=form.down_payment.data,
            financing_approved=False,  # Will be reviewed by admin/sales
            notes=form.notes.data
        )
        
        db.session.add(purchase)
        
        # Reserve the car
        car.status = CarStatus.RESERVED
        
        db.session.commit()
        
        flash('Your purchase request has been submitted successfully! We will contact you soon.', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('purchase.html', car=car, form=form)

# Authentication routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return redirect(url_for('auth.login'))
            
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.dashboard')
            return redirect(next_page)
        
        flash('Invalid username or password.', 'error')
    
    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists. Please choose a different one.', 'error')
            return render_template('register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered. Please use a different email or login.', 'error')
            return render_template('register.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            password_hash=generate_password_hash(form.password.data),
            role=UserRole.CUSTOMER  # Default role for new registrations
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

# Admin routes
@admin_bp.route('/')
@admin_required
def admin_dashboard():
    # Get comprehensive stats for admin
    stats = {
        'total_users': User.query.count(),
        'total_cars': Car.query.count(),
        'available_cars': Car.query.filter_by(status=CarStatus.AVAILABLE).count(),
        'sold_cars': Car.query.filter_by(status=CarStatus.SOLD).count(),
        'pending_purchases': Purchase.query.filter_by(status=PurchaseStatus.PENDING).count(),
        'completed_purchases': Purchase.query.filter_by(status=PurchaseStatus.COMPLETED).count(),
        'customer_count': User.query.filter_by(role=UserRole.CUSTOMER).count(),
        'sales_count': User.query.filter_by(role=UserRole.SALES).count(),
    }
    
    recent_purchases = Purchase.query.order_by(Purchase.created_at.desc()).limit(10).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin.html', stats=stats, recent_purchases=recent_purchases, recent_users=recent_users)

@admin_bp.route('/users')
@admin_required
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)

@admin_bp.route('/cars')
@sales_or_admin_required
def manage_cars():
    cars = Car.query.order_by(Car.created_at.desc()).all()
    return render_template('admin_cars.html', cars=cars)

@admin_bp.route('/car/add', methods=['GET', 'POST'])
@sales_or_admin_required
def add_car():
    form = CarForm()
    
    if form.validate_on_submit():
        # Check if VIN already exists
        if Car.query.filter_by(vin=form.vin.data).first():
            flash('A car with this VIN already exists.', 'error')
            return render_template('admin_car_form.html', form=form, title='Add New Car')
        
        car = Car(
            make=form.make.data,
            model=form.model.data,
            year=form.year.data,
            color=form.color.data,
            mileage=form.mileage.data,
            price=form.price.data,
            vin=form.vin.data,
            fuel_type=form.fuel_type.data,
            transmission=form.transmission.data,
            engine_size=form.engine_size.data,
            description=form.description.data,
            status=CarStatus(form.status.data)
        )
        
        db.session.add(car)
        db.session.commit()
        
        flash('Car added successfully!', 'success')
        return redirect(url_for('admin.manage_cars'))
    
    return render_template('admin_car_form.html', form=form, title='Add New Car')

@admin_bp.route('/purchases')
@sales_or_admin_required
def manage_purchases():
    purchases = Purchase.query.order_by(Purchase.created_at.desc()).all()
    return render_template('admin_purchases.html', purchases=purchases)

@admin_bp.route('/purchase/<int:purchase_id>/edit', methods=['GET', 'POST'])
@sales_or_admin_required
def edit_purchase(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    form = PurchaseManagementForm()
    
    # Populate sales person choices
    sales_people = User.query.filter(or_(User.role == UserRole.SALES, User.role == UserRole.ADMIN)).all()
    form.sales_person_id.choices = [(0, 'Not Assigned')] + [(u.id, u.full_name) for u in sales_people]
    
    if form.validate_on_submit():
        purchase.status = PurchaseStatus(form.status.data)
        purchase.sales_person_id = form.sales_person_id.data if form.sales_person_id.data != 0 else None
        purchase.financing_approved = form.financing_approved.data
        if form.notes.data:
            purchase.notes = form.notes.data
        
        # Update car status based on purchase status
        if purchase.status == PurchaseStatus.COMPLETED:
            purchase.car.status = CarStatus.SOLD
            from datetime import datetime
            purchase.completed_at = datetime.utcnow()
        elif purchase.status == PurchaseStatus.REJECTED:
            purchase.car.status = CarStatus.AVAILABLE
        
        db.session.commit()
        flash('Purchase updated successfully!', 'success')
        return redirect(url_for('admin.manage_purchases'))
    
    # Pre-populate form with current values
    form.status.data = purchase.status.value
    form.sales_person_id.data = purchase.sales_person_id or 0
    form.financing_approved.data = purchase.financing_approved
    form.notes.data = purchase.notes
    
    return render_template('admin_purchase_form.html', form=form, purchase=purchase)
