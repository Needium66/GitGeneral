from app import db
from flask_login import UserMixin
from enum import Enum
from datetime import datetime
from sqlalchemy import Enum as SQLEnum

class UserRole(Enum):
    CUSTOMER = "customer"
    SALES = "sales"
    ADMIN = "admin"

class CarStatus(Enum):
    AVAILABLE = "available"
    SOLD = "sold"
    RESERVED = "reserved"

class PurchaseStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(SQLEnum(UserRole), nullable=False, default=UserRole.CUSTOMER)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    purchases = db.relationship('Purchase', backref='customer', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def has_role(self, role):
        return self.role == role
    
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    def is_sales(self):
        return self.role == UserRole.SALES
    
    def is_customer(self):
        return self.role == UserRole.CUSTOMER

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(64), nullable=False)
    model = db.Column(db.String(64), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(32), nullable=False)
    mileage = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    vin = db.Column(db.String(17), unique=True, nullable=False)
    status = db.Column(SQLEnum(CarStatus), nullable=False, default=CarStatus.AVAILABLE)
    description = db.Column(db.Text)
    fuel_type = db.Column(db.String(32), nullable=False, default='Gasoline')
    transmission = db.Column(db.String(32), nullable=False, default='Automatic')
    engine_size = db.Column(db.String(16))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    purchases = db.relationship('Purchase', backref='car', lazy=True)
    
    def __repr__(self):
        return f'<Car {self.year} {self.make} {self.model}>'
    
    @property
    def display_name(self):
        return f"{self.year} {self.make} {self.model}"
    
    @property
    def formatted_price(self):
        return f"${self.price:,.2f}"

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
    sales_person_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(SQLEnum(PurchaseStatus), nullable=False, default=PurchaseStatus.PENDING)
    purchase_price = db.Column(db.Numeric(10, 2), nullable=False)
    down_payment = db.Column(db.Numeric(10, 2), default=0)
    financing_approved = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Define relationship to sales person
    sales_person = db.relationship('User', foreign_keys=[sales_person_id], backref='sales_made')
    
    def __repr__(self):
        return f'<Purchase {self.id}>'
    
    @property
    def formatted_price(self):
        return f"${self.purchase_price:,.2f}"
    
    @property
    def formatted_down_payment(self):
        return f"${self.down_payment:,.2f}"
