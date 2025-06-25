# =============================================================================
# NINC SAAS Health App - Backend Microservices (Python/FastAPI)
#
# This code provides a simplified, illustrative example of two core microservices:
# - Patient Service: Manages patient registration and profiles.
# - Appointment Service: Handles appointment scheduling.
#
# A real-world application would require more robust database integrations (e.g., Cloud SQL),
# comprehensive error handling, advanced security, and full API gateway integration.
#
# Project Structure:
# ninc_backend/
# ├── patient_service/
# │   ├── main.py
# │   ├── models.py
# │   ├── database.py
# │   ├── Dockerfile
# │   └── requirements.txt
# └── appointment_service/
#     ├── main.py
#     ├── models.py
#     ├── database.py
#     ├── Dockerfile
#     └── requirements.txt
# =============================================================================

# =============================================================================
# Patient Service - main.py
# Description: FastAPI application for managing patient data.
# =============================================================================
# patient_service/main.py
from fastapi import FastAPI, HTTPException, status
from typing import List, Dict, Optional
import uuid
from datetime import datetime

# Import models and database simulation
from .models import Patient, PatientCreate, PatientUpdate
from .database import patients_db # Simulated in-memory database

app = FastAPI(
    title="NINC Patient Service",
    description="API for managing patient registration and profiles.",
    version="1.0.0"
)

@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint for the Patient Service.
    """
    return {"message": "Welcome to NINC Patient Service API!"}

@app.post("/patients", response_model=Patient, status_code=status.HTTP_201_CREATED, tags=["Patients"])
async def create_patient(patient_data: PatientCreate):
    """
    Registers a new patient in the system.
    """
    patient_id = str(uuid.uuid4())
    current_time = datetime.utcnow()
    new_patient = Patient(
        id=patient_id,
        created_at=current_time,
        updated_at=current_time,
        **patient_data.dict()
    )
    patients_db[patient_id] = new_patient
    print(f"Patient created: {new_patient.name} (ID: {new_patient.id})")
    # In a real application, save to Cloud SQL:
    # await save_patient_to_cloud_sql(new_patient)
    return new_patient

@app.get("/patients", response_model=List[Patient], tags=["Patients"])
async def get_all_patients():
    """
    Retrieves a list of all registered patients.
    """
    return list(patients_db.values())

@app.get("/patients/{patient_id}", response_model=Patient, tags=["Patients"])
async def get_patient(patient_id: str):
    """
    Retrieves a single patient by their ID.
    """
    patient = patients_db.get(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found."
        )
    return patient

@app.put("/patients/{patient_id}", response_model=Patient, tags=["Patients"])
async def update_patient(patient_id: str, patient_update: PatientUpdate):
    """
    Updates an existing patient's profile information.
    """
    patient = patients_db.get(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found."
        )

    # Update fields from the request, excluding unset fields (Pydantic feature)
    update_data = patient_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(patient, key, value)
    patient.updated_at = datetime.utcnow() # Update timestamp
    patients_db[patient_id] = patient # Update in simulated DB
    print(f"Patient updated: {patient.name} (ID: {patient.id})")
    # In a real application, update in Cloud SQL:
    # await update_patient_in_cloud_sql(patient)
    return patient

@app.delete("/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Patients"])
async def delete_patient(patient_id: str):
    """
    Deletes a patient from the system.
    Note: In a real healthcare app, patient data is rarely truly deleted due to compliance.
    A "soft delete" (marking as inactive) is more common.
    """
    if patient_id not in patients_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID '{patient_id}' not found."
        )
    del patients_db[patient_id]
    print(f"Patient deleted (simulated): ID {patient_id}")
    # In a real application, perform soft delete or actual delete in Cloud SQL:
    # await delete_patient_from_cloud_sql(patient_id)
    return {} # No content for 204 response

# =============================================================================
# Patient Service - models.py
# Description: Pydantic models for data validation and serialization.
# =============================================================================
# patient_service/models.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class PatientBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., regex=r"^\+?\d{10,15}$") # Basic phone number regex
    date_of_birth: str = Field(..., example="YYYY-MM-DD") # Consider `date` type for actual use
    address: Optional[str] = None

class PatientCreate(PatientBase):
    pass # No additional fields needed for creation

class PatientUpdate(PatientBase):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None

class Patient(PatientBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True # For SQLAlchemy ORM compatibility, though not used here

# =============================================================================
# Patient Service - database.py
# Description: Placeholder for database connection and operations.
# For demonstration, a simple in-memory dictionary is used.
# In a real application, this would connect to Cloud SQL (PostgreSQL).
# =============================================================================
# patient_service/database.py
from typing import Dict
from .models import Patient

# Simulated in-memory database
patients_db: Dict[str, Patient] = {}

# Example functions for real database interaction (conceptual)
# async def connect_to_cloud_sql():
#     """Establishes connection to Cloud SQL PostgreSQL database."""
#     # Using SQLAlchemy ORM and asyncpg driver
#     pass

# async def save_patient_to_cloud_sql(patient: Patient):
#     """Saves a patient record to Cloud SQL."""
#     pass

# async def get_patient_from_cloud_sql(patient_id: str) -> Optional[Patient]:
#     """Retrieves a patient record from Cloud SQL."""
#     pass

# async def update_patient_in_cloud_sql(patient: Patient):
#     """Updates a patient record in Cloud SQL."""
#     pass

# async def delete_patient_from_cloud_sql(patient_id: str):
#     """Deletes (or soft deletes) a patient record from Cloud SQL."""
#     pass


# =============================================================================
# Patient Service - Dockerfile
# Description: Dockerfile for containerizing the Patient Service.
# =============================================================================
# patient_service/Dockerfile
FROM python:3.9-slim-buster

WORKDIR /app

# Install dependencies
COPY patient_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY patient_service/ .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using Uvicorn (ASGI server for FastAPI)
# Using 0.0.0.0 to bind to all available network interfaces
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# =============================================================================
# Patient Service - requirements.txt
# Description: Python dependencies for the Patient Service.
# =============================================================================
# patient_service/requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0 # Useful for managing settings/secrets
# psycopg2-binary==2.9.9 # Uncomment and use for PostgreSQL
# sqlalchemy[asyncio]==2.0.25 # Uncomment and use for SQLAlchemy ORM


# =============================================================================
# Appointment Service - main.py
# Description: FastAPI application for managing appointment data.
# =============================================================================
# appointment_service/main.py
from fastapi import FastAPI, HTTPException, status
from typing import List, Dict, Optional
import uuid
from datetime import datetime, timedelta

# Import models and database simulation
from .models import Appointment, AppointmentCreate, AppointmentUpdate, DoctorAvailability, TimeSlot
from .database import appointments_db, doctor_availability_db # Simulated in-memory database

app = FastAPI(
    title="NINC Appointment Service",
    description="API for managing patient appointments and doctor availability.",
    version="1.0.0"
)

@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint for the Appointment Service.
    """
    return {"message": "Welcome to NINC Appointment Service API!"}

@app.post("/appointments", response_model=Appointment, status_code=status.HTTP_201_CREATED, tags=["Appointments"])
async def create_appointment(appointment_data: AppointmentCreate):
    """
    Creates a new appointment for a patient with a doctor.
    """
    # Simulate checking doctor availability (in a real app, this would query doctor_locator-service)
    doctor_id = appointment_data.doctor_id
    requested_time = appointment_data.appointment_time
    # Simple check for demo: is doctor available at the exact minute?
    # A real system would check slot availability, duration, and manage overlaps.
    if doctor_id not in doctor_availability_db:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Doctor {doctor_id} availability not found."
        )

    # Basic availability check: check if the exact slot is not booked
    # This is highly simplified. A real system would manage slots, not exact timestamps.
    for appt in appointments_db.values():
        if appt.doctor_id == doctor_id and appt.appointment_time == requested_time:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Appointment slot already taken for this doctor."
            )

    appointment_id = str(uuid.uuid4())
    current_time = datetime.utcnow()
    new_appointment = Appointment(
        id=appointment_id,
        created_at=current_time,
        updated_at=current_time,
        status="scheduled", # Initial status
        **appointment_data.dict()
    )
    appointments_db[appointment_id] = new_appointment
    print(f"Appointment created: ID {new_appointment.id} for Patient {new_appointment.patient_id} with Doctor {new_appointment.doctor_id}")
    # In a real app, trigger reminders via Pub/Sub or Cloud Tasks
    # await send_appointment_confirmation_email(new_appointment)
    return new_appointment

@app.get("/appointments", response_model=List[Appointment], tags=["Appointments"])
async def get_all_appointments(patient_id: Optional[str] = None, doctor_id: Optional[str] = None):
    """
    Retrieves a list of all appointments, with optional filtering by patient or doctor ID.
    """
    filtered_appointments = []
    for appt in appointments_db.values():
        if (patient_id is None or appt.patient_id == patient_id) and \
           (doctor_id is None or appt.doctor_id == doctor_id):
            filtered_appointments.append(appt)
    return filtered_appointments

@app.get("/appointments/{appointment_id}", response_model=Appointment, tags=["Appointments"])
async def get_appointment(appointment_id: str):
    """
    Retrieves a single appointment by its ID.
    """
    appointment = appointments_db.get(appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID '{appointment_id}' not found."
        )
    return appointment

@app.put("/appointments/{appointment_id}", response_model=Appointment, tags=["Appointments"])
async def update_appointment(appointment_id: str, appointment_update: AppointmentUpdate):
    """
    Updates an existing appointment (e.g., reschedule, change status).
    """
    appointment = appointments_db.get(appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID '{appointment_id}' not found."
        )

    # Prevent changing patient_id or doctor_id in update for simplicity.
    # A real system would have specific reschedule logic.
    if appointment_update.patient_id and appointment_update.patient_id != appointment.patient_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change patient ID.")
    if appointment_update.doctor_id and appointment_update.doctor_id != appointment.doctor_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change doctor ID.")

    update_data = appointment_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(appointment, key, value)
    appointment.updated_at = datetime.utcnow()
    appointments_db[appointment_id] = appointment
    print(f"Appointment updated: ID {appointment.id} (Status: {appointment.status})")
    return appointment

@app.delete("/appointments/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Appointments"])
async def cancel_appointment(appointment_id: str):
    """
    Cancels an appointment.
    Note: In a real system, cancellation might update status to 'cancelled' rather than deleting.
    """
    appointment = appointments_db.get(appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment with ID '{appointment_id}' not found."
        )
    # Simulate cancellation by changing status, not deletion
    appointment.status = "cancelled"
    appointment.updated_at = datetime.utcnow()
    appointments_db[appointment_id] = appointment
    # del appointments_db[appointment_id] # For actual deletion (less common in health apps)
    print(f"Appointment cancelled: ID {appointment_id}")
    return {}

# Doctor Availability Endpoints (Simplified)
@app.post("/doctors/{doctor_id}/availability", response_model=DoctorAvailability, status_code=status.HTTP_201_CREATED, tags=["Doctor Availability"])
async def set_doctor_availability(doctor_id: str, availability: DoctorAvailability):
    """
    Sets or updates a doctor's availability slots.
    """
    # Simple overwrite for demo. A real system would merge or manage specific slots.
    doctor_availability_db[doctor_id] = availability
    print(f"Doctor {doctor_id} availability updated for {len(availability.available_slots)} slots.")
    return availability

@app.get("/doctors/{doctor_id}/availability", response_model=Optional[DoctorAvailability], tags=["Doctor Availability"])
async def get_doctor_availability(doctor_id: str):
    """
    Retrieves a doctor's availability.
    """
    availability = doctor_availability_db.get(doctor_id)
    if not availability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Availability for Doctor ID '{doctor_id}' not found."
        )
    return availability


# =============================================================================
# Appointment Service - models.py
# Description: Pydantic models for data validation and serialization.
# =============================================================================
# appointment_service/models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class AppointmentBase(BaseModel):
    patient_id: str = Field(..., description="ID of the patient booking the appointment.")
    doctor_id: str = Field(..., description="ID of the doctor for the appointment.")
    appointment_time: datetime = Field(..., description="Scheduled date and time of the appointment (UTC).")
    reason_for_visit: str = Field(..., min_length=10, max_length=500)

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    # Only allow updating status or reason for visit, not patient/doctor/time directly
    status: Optional[str] = Field(None, description="Status of the appointment (e.g., 'scheduled', 'completed', 'cancelled').")
    reason_for_visit: Optional[str] = Field(None, min_length=10, max_length=500)
    # For rescheduling, a separate endpoint or more complex logic would be needed.

class Appointment(AppointmentBase):
    id: str
    status: str # e.g., 'scheduled', 'completed', 'cancelled'
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime

class DoctorAvailability(BaseModel):
    doctor_id: str
    date: str = Field(..., example="YYYY-MM-DD") # Date for which availability is set
    available_slots: List[TimeSlot] = []


# =============================================================================
# Appointment Service - database.py
# Description: Placeholder for database connection and operations.
# For demonstration, simple in-memory dictionaries are used.
# In a real application, this would connect to Cloud SQL (PostgreSQL).
# =============================================================================
# appointment_service/database.py
from typing import Dict, List
from .models import Appointment, DoctorAvailability

# Simulated in-memory databases
appointments_db: Dict[str, Appointment] = {}
doctor_availability_db: Dict[str, DoctorAvailability] = {}

# Populate with some dummy doctor availability for testing
from datetime import datetime, timedelta
# Dummy doctor 1: available morning
doctor_availability_db["doc-123"] = DoctorAvailability(
    doctor_id="doc-123",
    date="2025-07-01",
    available_slots=[
        TimeSlot(start_time=datetime(2025, 7, 1, 9, 0, 0), end_time=datetime(2025, 7, 1, 9, 30, 0)),
        TimeSlot(start_time=datetime(2025, 7, 1, 9, 30, 0), end_time=datetime(2025, 7, 1, 10, 0, 0)),
        TimeSlot(start_time=datetime(2025, 7, 1, 10, 0, 0), end_time=datetime(2025, 7, 1, 10, 30, 0)),
        TimeSlot(start_time=datetime(2025, 7, 1, 10, 30, 0), end_time=datetime(2025, 7, 1, 11, 0, 0)),
    ]
)
# Dummy doctor 2: available afternoon
doctor_availability_db["doc-456"] = DoctorAvailability(
    doctor_id="doc-456",
    date="2025-07-01",
    available_slots=[
        TimeSlot(start_time=datetime(2025, 7, 1, 13, 0, 0), end_time=datetime(2025, 7, 1, 13, 30, 0)),
        TimeSlot(start_time=datetime(2025, 7, 1, 13, 30, 0), end_time=datetime(2025, 7, 1, 14, 0, 0)),
        TimeSlot(start_time=datetime(2025, 7, 1, 14, 0, 0), end_time=datetime(2025, 7, 1, 14, 30, 0)),
    ]
)

# Example functions for real database interaction (conceptual)
# async def connect_to_cloud_sql():
#     """Establishes connection to Cloud SQL PostgreSQL database."""
#     pass

# async def save_appointment_to_cloud_sql(appointment: Appointment):
#     """Saves an appointment record to Cloud SQL."""
#     pass

# async def get_appointment_from_cloud_sql(appointment_id: str) -> Optional[Appointment]:
#     """Retrieves an appointment record from Cloud SQL."""
#     pass

# async def update_appointment_in_cloud_sql(appointment: Appointment):
#     """Updates an appointment record in Cloud SQL."""
#     pass

# async def get_doctor_availability_from_cloud_sql(doctor_id: str, date: str) -> Optional[DoctorAvailability]:
#     """Retrieves doctor availability from Cloud SQL."""
#     pass

# async def update_doctor_availability_in_cloud_sql(availability: DoctorAvailability):
#     """Updates doctor availability in Cloud SQL."""
#     pass


# =============================================================================
# Appointment Service - Dockerfile
# Description: Dockerfile for containerizing the Appointment Service.
# =============================================================================
# appointment_service/Dockerfile
FROM python:3.9-slim-buster

WORKDIR /app

# Install dependencies
COPY appointment_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY appointment_service/ .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using Uvicorn (ASGI server for FastAPI)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# =============================================================================
# Appointment Service - requirements.txt
# Description: Python dependencies for the Appointment Service.
# =============================================================================
# appointment_service/requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0 # Useful for managing settings/secrets
# psycopg2-binary==2.9.9 # Uncomment and use for PostgreSQL
# sqlalchemy[asyncio]==2.0.25 # Uncomment and use for SQLAlchemy ORM
