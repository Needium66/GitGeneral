from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

Base = declarative_base()

# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String)
    date_of_birth = Column(String)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)
    insurance_provider = Column(String)
    insurance_policy_number = Column(String)
    created_at = Column(DateTime, default=func.now())

class Doctor(Base):
    __tablename__ = "doctors"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    consultation_fee = Column(Numeric(10, 2), nullable=False)
    rating = Column(Numeric(3, 2), default=0)
    review_count = Column(Integer, default=0)
    availability = Column(JSON, default=lambda: [])
    image_url = Column(String)
    created_at = Column(DateTime, default=func.now())

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    doctor_id = Column(Integer, nullable=False)
    appointment_date = Column(String, nullable=False)
    appointment_time = Column(String, nullable=False)
    appointment_type = Column(String, nullable=False)  # 'in-person' | 'telemedicine'
    status = Column(String, nullable=False, default="scheduled")  # 'scheduled' | 'confirmed' | 'completed' | 'cancelled'
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())

class Prescription(Base):
    __tablename__ = "prescriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    doctor_id = Column(Integer, nullable=False)
    medication_name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    refills_remaining = Column(Integer, nullable=False, default=0)
    instructions = Column(Text)
    prescribed_date = Column(String, nullable=False)
    expiry_date = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")  # 'active' | 'expired' | 'refill_due'
    created_at = Column(DateTime, default=func.now())

class Pharmacy(Base):
    __tablename__ = "pharmacies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    hours = Column(String, nullable=False)
    distance = Column(Numeric(5, 2))

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    appointment_id = Column(Integer)
    description = Column(String, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    insurance_paid = Column(Numeric(10, 2), default=0)
    patient_responsibility = Column(Numeric(10, 2), nullable=False)
    status = Column(String, nullable=False, default="pending")  # 'pending' | 'paid' | 'overdue'
    due_date = Column(String, nullable=False)
    paid_date = Column(String)
    payment_method = Column(String)
    created_at = Column(DateTime, default=func.now())

class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    type = Column(String, nullable=False)  # 'card' | 'bank'
    card_last4 = Column(String)
    card_type = Column(String)
    expiry_month = Column(String)
    expiry_year = Column(String)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

# Pydantic Models for API
class UserBase(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class DoctorBase(BaseModel):
    first_name: str
    last_name: str
    specialty: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    zip_code: str
    consultation_fee: float
    availability: Optional[List[str]] = []
    image_url: Optional[str] = None

class DoctorCreate(DoctorBase):
    pass

class DoctorResponse(DoctorBase):
    id: int
    rating: float
    review_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class AppointmentBase(BaseModel):
    user_id: int
    doctor_id: int
    appointment_date: str
    appointment_time: str
    appointment_type: str
    status: str = "scheduled"
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentResponse(AppointmentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PrescriptionBase(BaseModel):
    user_id: int
    doctor_id: int
    medication_name: str
    dosage: str
    quantity: int
    refills_remaining: int = 0
    instructions: Optional[str] = None
    prescribed_date: str
    expiry_date: str
    status: str = "active"

class PrescriptionCreate(PrescriptionBase):
    pass

class PrescriptionResponse(PrescriptionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PharmacyBase(BaseModel):
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    phone: str
    hours: str
    distance: Optional[float] = None

class PharmacyCreate(PharmacyBase):
    pass

class PharmacyResponse(PharmacyBase):
    id: int

    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    user_id: int
    appointment_id: Optional[int] = None
    description: str
    total_amount: float
    insurance_paid: float = 0
    patient_responsibility: float
    status: str = "pending"
    due_date: str
    paid_date: Optional[str] = None
    payment_method: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentMethodBase(BaseModel):
    user_id: int
    type: str
    card_last4: Optional[str] = None
    card_type: Optional[str] = None
    expiry_month: Optional[str] = None
    expiry_year: Optional[str] = None
    is_default: bool = False

class PaymentMethodCreate(PaymentMethodBase):
    pass

class PaymentMethodResponse(PaymentMethodBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True