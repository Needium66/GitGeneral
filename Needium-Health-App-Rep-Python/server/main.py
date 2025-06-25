from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import os

from database import get_db, create_tables
from models import *
from seed_data import seed_database

app = FastAPI(title="NINC Health API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and seed data
@app.on_event("startup")
async def startup_event():
    create_tables()
    seed_database()

# User endpoints
@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/api/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: dict, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in user_update.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

# Doctor endpoints
@app.get("/api/doctors", response_model=List[DoctorResponse])
async def get_doctors(
    specialty: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Doctor)
    
    if specialty and specialty != "All Specialties":
        query = query.filter(Doctor.specialty.ilike(f"%{specialty}%"))
    
    if location:
        query = query.filter(
            (Doctor.city.ilike(f"%{location}%")) | 
            (Doctor.zip_code.contains(location))
        )
    
    return query.all()

@app.get("/api/doctors/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor

@app.post("/api/doctors", response_model=DoctorResponse)
async def create_doctor(doctor: DoctorCreate, db: Session = Depends(get_db)):
    db_doctor = Doctor(**doctor.dict())
    db.add(db_doctor)
    db.commit()
    db.refresh(db_doctor)
    return db_doctor

# Appointment endpoints
@app.get("/api/appointments/user/{user_id}", response_model=List[AppointmentResponse])
async def get_user_appointments(user_id: int, db: Session = Depends(get_db)):
    return db.query(Appointment).filter(Appointment.user_id == user_id).all()

@app.get("/api/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment

@app.post("/api/appointments", response_model=AppointmentResponse)
async def create_appointment(appointment: AppointmentCreate, db: Session = Depends(get_db)):
    db_appointment = Appointment(**appointment.dict())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

@app.put("/api/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(appointment_id: int, appointment_update: dict, db: Session = Depends(get_db)):
    db_appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    for key, value in appointment_update.items():
        setattr(db_appointment, key, value)
    
    db.commit()
    db.refresh(db_appointment)
    return db_appointment

# Prescription endpoints
@app.get("/api/prescriptions/user/{user_id}", response_model=List[PrescriptionResponse])
async def get_user_prescriptions(user_id: int, db: Session = Depends(get_db)):
    return db.query(Prescription).filter(Prescription.user_id == user_id).all()

@app.post("/api/prescriptions", response_model=PrescriptionResponse)
async def create_prescription(prescription: PrescriptionCreate, db: Session = Depends(get_db)):
    db_prescription = Prescription(**prescription.dict())
    db.add(db_prescription)
    db.commit()
    db.refresh(db_prescription)
    return db_prescription

@app.put("/api/prescriptions/{prescription_id}", response_model=PrescriptionResponse)
async def update_prescription(prescription_id: int, prescription_update: dict, db: Session = Depends(get_db)):
    db_prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not db_prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    for key, value in prescription_update.items():
        setattr(db_prescription, key, value)
    
    db.commit()
    db.refresh(db_prescription)
    return db_prescription

# Pharmacy endpoints
@app.get("/api/pharmacies", response_model=List[PharmacyResponse])
async def get_pharmacies(zip_code: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Pharmacy)
    if zip_code:
        query = query.filter(Pharmacy.zip_code == zip_code)
    return query.all()

# Payment endpoints
@app.get("/api/payments/user/{user_id}", response_model=List[PaymentResponse])
async def get_user_payments(user_id: int, db: Session = Depends(get_db)):
    return db.query(Payment).filter(Payment.user_id == user_id).all()

@app.post("/api/payments", response_model=PaymentResponse)
async def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    db_payment = Payment(**payment.dict())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

@app.put("/api/payments/{payment_id}", response_model=PaymentResponse)
async def update_payment(payment_id: int, payment_update: dict, db: Session = Depends(get_db)):
    db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    for key, value in payment_update.items():
        setattr(db_payment, key, value)
    
    db.commit()
    db.refresh(db_payment)
    return db_payment

# Payment Method endpoints
@app.get("/api/payment-methods/user/{user_id}", response_model=List[PaymentMethodResponse])
async def get_user_payment_methods(user_id: int, db: Session = Depends(get_db)):
    return db.query(PaymentMethod).filter(PaymentMethod.user_id == user_id).all()

@app.post("/api/payment-methods", response_model=PaymentMethodResponse)
async def create_payment_method(payment_method: PaymentMethodCreate, db: Session = Depends(get_db)):
    db_payment_method = PaymentMethod(**payment_method.dict())
    db.add(db_payment_method)
    db.commit()
    db.refresh(db_payment_method)
    return db_payment_method

@app.delete("/api/payment-methods/{payment_method_id}")
async def delete_payment_method(payment_method_id: int, db: Session = Depends(get_db)):
    db_payment_method = db.query(PaymentMethod).filter(PaymentMethod.id == payment_method_id).first()
    if not db_payment_method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    
    db.delete(db_payment_method)
    db.commit()
    return {"message": "Payment method deleted successfully"}

# Serve static files (React app)
if os.path.exists("../client/dist"):
    app.mount("/", StaticFiles(directory="../client/dist", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)