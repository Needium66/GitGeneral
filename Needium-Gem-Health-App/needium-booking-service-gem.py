###########################################################################################
# Develop the Python code for the NINC booking microservice.                              #
# This service will handle the creation, retrieval, and management of patient appointments#
# leveraging AWS DynamoDB for data storage and AWS SNS for sending notifications.         #
###########################################################################################
# The Code:
###########################################################################################
# booking_service.py

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import boto3
import os
import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
APPOINTMENTS_TABLE_NAME = os.getenv("APPOINTMENTS_TABLE_NAME", "NINCAppointments")
SNS_TOPIC_ARN_APPOINTMENTS = os.getenv("SNS_TOPIC_ARN_APPOINTMENTS", "arn:aws:sns:us-east-1:123456789012:NINCAppointmentNotifications") # Replace with your actual SNS Topic ARN

# --- Enums ---
class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class AppointmentType(str, Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    TELEMEDICINE = "telemedicine"
    LAB_WORK = "lab_work"

# --- Pydantic Models for Data Validation and Serialization ---

class AppointmentCreate(BaseModel):
    """
    Model for creating a new appointment.
    """
    patient_id: str = Field(..., description="ID of the patient booking the appointment.")
    doctor_id: str = Field(..., description="ID of the doctor for the appointment.")
    start_time: datetime = Field(..., description="Appointment start time (ISO 8601 format).")
    end_time: datetime = Field(..., description="Appointment end time (ISO 8601 format).")
    appointment_type: AppointmentType = Field(..., description="Type of appointment (e.g., consultation, telemedicine).")
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    """
    Model for returning appointment details.
    """
    appointment_id: str
    patient_id: str
    doctor_id: str
    start_time: datetime
    end_time: datetime
    appointment_type: AppointmentType
    status: AppointmentStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# --- AWS Service Clients ---

def get_dynamodb_client():
    """
    Initializes and returns a DynamoDB client.
    """
    try:
        return boto3.client('dynamodb', region_name=AWS_REGION)
    except Exception as e:
        logger.error(f"Error initializing DynamoDB client: {e}")
        raise

def get_sns_client():
    """
    Initializes and returns an SNS client.
    """
    try:
        return boto3.client('sns', region_name=AWS_REGION)
    except Exception as e:
        logger.error(f"Error initializing SNS client: {e}")
        raise

# --- Service Class for Data Operations ---

class BookingService:
    """
    Handles operations related to Appointments in DynamoDB and sends notifications via SNS.
    """
    def __init__(self):
        self.dynamodb = get_dynamodb_client()
        self.sns = get_sns_client()
        self.table_name = APPOINTMENTS_TABLE_NAME

    def _dynamodb_item_to_appointment_response(self, item: Dict[str, Any]) -> AppointmentResponse:
        """
        Converts a DynamoDB item dictionary to an AppointmentResponse Pydantic model.
        """
        try:
            return AppointmentResponse(
                appointment_id=item['appointment_id']['S'],
                patient_id=item['patient_id']['S'],
                doctor_id=item['doctor_id']['S'],
                start_time=datetime.fromisoformat(item['start_time']['S']),
                end_time=datetime.fromisoformat(item['end_time']['S']),
                appointment_type=AppointmentType(item['appointment_type']['S']),
                status=AppointmentStatus(item['status']['S']),
                notes=item.get('notes', {}).get('S'),
                created_at=datetime.fromisoformat(item['created_at']['S']),
                updated_at=datetime.fromisoformat(item['updated_at']['S'])
            )
        except KeyError as e:
            logger.error(f"Missing key in DynamoDB item: {e}. Item: {item}")
            raise ValueError(f"Invalid DynamoDB item format: {e}")
        except Exception as e:
            logger.error(f"Error converting DynamoDB item to AppointmentResponse: {e}. Item: {item}")
            raise

    def create_appointment(self, appointment_data: AppointmentCreate) -> AppointmentResponse:
        """
        Creates a new appointment in DynamoDB and sends a notification.
        Includes a basic check for time conflicts for the specific doctor.
        """
        appointment_id = str(uuid.uuid4())
        current_time = datetime.now()

        # Basic availability check: Check for existing appointments for this doctor that overlap
        # In a real system, this would be more robust, potentially involving a dedicated
        # availability service or a more complex query/transaction.
        existing_appointments = self.get_appointments_by_doctor(
            appointment_data.doctor_id,
            start_date=appointment_data.start_time.isoformat(),
            end_date=(appointment_data.end_time + timedelta(days=1)).isoformat() # Check beyond the end time
        )

        for existing_app in existing_appointments:
            # Check for overlaps, ignoring cancelled or no-show appointments
            if existing_app.status not in [AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]:
                if (appointment_data.start_time < existing_app.end_time and
                    appointment_data.end_time > existing_app.start_time):
                    logger.warning(f"Time conflict detected for doctor {appointment_data.doctor_id} with existing appointment {existing_app.appointment_id}.")
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Doctor is not available at the requested time. Please choose another slot."
                    )

        item = {
            'appointment_id': {'S': appointment_id},
            'patient_id': {'S': appointment_data.patient_id},
            'doctor_id': {'S': appointment_data.doctor_id},
            'start_time': {'S': appointment_data.start_time.isoformat()},
            'end_time': {'S': appointment_data.end_time.isoformat()},
            'appointment_type': {'S': appointment_data.appointment_type.value},
            'status': {'S': AppointmentStatus.PENDING.value}, # Default to pending, can be confirmed later
            'notes': {'S': appointment_data.notes} if appointment_data.notes else {'NULL': True},
            'created_at': {'S': current_time.isoformat()},
            'updated_at': {'S': current_time.isoformat()}
        }

        try:
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=item,
                ConditionExpression="attribute_not_exists(appointment_id)" # Ensure unique ID
            )
            created_appointment = self._dynamodb_item_to_appointment_response(item)
            logger.info(f"Appointment {appointment_id} created successfully for patient {appointment_data.patient_id} with doctor {appointment_data.doctor_id}.")

            # Send notification
            self._send_appointment_notification(
                appointment_id,
                appointment_data.patient_id,
                appointment_data.doctor_id,
                appointment_data.start_time,
                AppointmentStatus.PENDING,
                "New appointment booked."
            )
            return created_appointment
        except self.dynamodb.exceptions.ConditionalCheckFailedException:
            logger.error(f"Appointment ID {appointment_id} already exists (highly unlikely due to UUID).")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Appointment ID conflict.")
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create appointment: {e}")

    def get_appointment(self, appointment_id: str) -> Optional[AppointmentResponse]:
        """
        Retrieves a single appointment by its ID.
        """
        try:
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={'appointment_id': {'S': appointment_id}}
            )
            item = response.get('Item')
            if item:
                return self._dynamodb_item_to_appointment_response(item)
            return None
        except Exception as e:
            logger.error(f"Error getting appointment {appointment_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve appointment: {e}")

    def get_appointments_by_patient(self, patient_id: str) -> List[AppointmentResponse]:
        """
        Retrieves all appointments for a given patient using a GSI.
        """
        try:
            response = self.dynamodb.query(
                TableName=self.table_name,
                IndexName='patient_id-index', # Ensure this GSI exists
                KeyConditionExpression='patient_id = :patient_id',
                ExpressionAttributeValues={':patient_id': {'S': patient_id}}
            )
            appointments = [self._dynamodb_item_to_appointment_response(item) for item in response.get('Items', [])]
            logger.info(f"Retrieved {len(appointments)} appointments for patient {patient_id}.")
            return appointments
        except Exception as e:
            logger.error(f"Error getting appointments for patient {patient_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve patient appointments: {e}")

    def get_appointments_by_doctor(self, doctor_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[AppointmentResponse]:
        """
        Retrieves all appointments for a given doctor, optionally filtered by date range, using a GSI.
        """
        key_condition_expression = 'doctor_id = :doctor_id'
        expression_attribute_values = {':doctor_id': {'S': doctor_id}}

        if start_date and end_date:
            key_condition_expression += ' AND start_time BETWEEN :start_date AND :end_date'
            expression_attribute_values[':start_date'] = {'S': start_date}
            expression_attribute_values[':end_date'] = {'S': end_date}
        elif start_date:
            key_condition_expression += ' AND start_time >= :start_date'
            expression_attribute_values[':start_date'] = {'S': start_date}
        elif end_date:
            key_condition_expression += ' AND start_time <= :end_date'
            expression_attribute_values[':end_date'] = {'S': end_date}

        try:
            response = self.dynamodb.query(
                TableName=self.table_name,
                IndexName='doctor_id-start_time-index', # Ensure this GSI exists
                KeyConditionExpression=key_condition_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            appointments = [self._dynamodb_item_to_appointment_response(item) for item in response.get('Items', [])]
            logger.info(f"Retrieved {len(appointments)} appointments for doctor {doctor_id}.")
            return appointments
        except Exception as e:
            logger.error(f"Error getting appointments for doctor {doctor_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve doctor appointments: {e}")

    def update_appointment_status(self, appointment_id: str, new_status: AppointmentStatus) -> AppointmentResponse:
        """
        Updates the status of an existing appointment.
        """
        current_time = datetime.now().isoformat()
        try:
            response = self.dynamodb.update_item(
                TableName=self.table_name,
                Key={'appointment_id': {'S': appointment_id}},
                UpdateExpression="SET #s = :new_status, updated_at = :updated_at",
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={
                    ':new_status': {'S': new_status.value},
                    ':updated_at': {'S': current_time}
                },
                ReturnValues="ALL_NEW"
            )
            updated_item = response.get('Attributes')
            if not updated_item:
                logger.warning(f"Appointment {appointment_id} not found for status update.")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")

            updated_appointment = self._dynamodb_item_to_appointment_response(updated_item)
            logger.info(f"Appointment {appointment_id} status updated to {new_status.value}.")

            # Send notification about status change
            self._send_appointment_notification(
                appointment_id,
                updated_appointment.patient_id,
                updated_appointment.doctor_id,
                updated_appointment.start_time,
                new_status,
                f"Appointment status updated to {new_status.value}."
            )
            return updated_appointment
        except HTTPException:
            raise # Re-raise if it's already an HTTPException
        except Exception as e:
            logger.error(f"Error updating status for appointment {appointment_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update appointment status: {e}")

    def _send_appointment_notification(self, appointment_id: str, patient_id: str, doctor_id: str, start_time: datetime, status: AppointmentStatus, message: str):
        """
        Sends an SNS notification for an appointment event.
        In a real application, you'd fetch patient's preferred contact (email/phone)
        from the Patient Management Service and send targeted notifications (SES for email, SNS for SMS).
        For simplicity, this sends to a generic SNS topic.
        """
        notification_payload = {
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "start_time": start_time.isoformat(),
            "status": status.value,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        try:
            self.sns.publish(
                TopicArn=SNS_TOPIC_ARN_APPOINTMENTS,
                Message=json.dumps(notification_payload),
                Subject="NINC Appointment Notification"
            )
            logger.info(f"Notification sent for appointment {appointment_id} (status: {status.value}).")
        except Exception as e:
            logger.error(f"Failed to send SNS notification for appointment {appointment_id}: {e}")
            # Do not re-raise, as notification failure shouldn't block main operation

# --- FastAPI Application Setup ---

app = FastAPI(
    title="NINC Booking Microservice",
    description="API for managing patient and doctor appointments.",
    version="1.0.0"
)

# Initialize service instances
booking_service = BookingService()

# --- API Endpoints ---

@app.post("/appointments", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_new_appointment(appointment_data: AppointmentCreate):
    """
    Creates a new appointment.
    Performs a basic check for doctor's availability.
    """
    return booking_service.create_appointment(appointment_data)

@app.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_single_appointment(appointment_id: str):
    """
    Retrieves a single appointment by its ID.
    """
    appointment = booking_service.get_appointment(appointment_id)
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return appointment

@app.get("/appointments/patient/{patient_id}", response_model=List[AppointmentResponse])
async def get_patient_appointments(patient_id: str):
    """
    Retrieves all appointments for a specific patient.
    """
    return booking_service.get_appointments_by_patient(patient_id)

@app.get("/appointments/doctor/{doctor_id}", response_model=List[AppointmentResponse])
async def get_doctor_appointments(doctor_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """
    Retrieves all appointments for a specific doctor, optionally filtered by date range.
    Date format: YYYY-MM-DDTHH:MM:SSZ (e.g., "2024-07-01T00:00:00Z")
    """
    return booking_service.get_appointments_by_doctor(doctor_id, start_date, end_date)

@app.put("/appointments/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(appointment_id: str, new_status: AppointmentStatus):
    """
    Updates the status of an existing appointment.
    """
    return booking_service.update_appointment_status(appointment_id, new_status)

# --- Example DynamoDB Table Creation and GSI Commands ---
# You would run these AWS CLI commands or use CloudFormation/Terraform to set up your DynamoDB table.
"""
# Create the main Appointments table
aws dynamodb create-table \
    --table-name NINCAppointments \
    --attribute-definitions \
        AttributeName=appointment_id,AttributeType=S \
        AttributeName=patient_id,AttributeType=S \
        AttributeName=doctor_id,AttributeType=S \
        AttributeName=start_time,AttributeType=S \
    --key-schema \
        AttributeName=appointment_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --global-secondary-indexes \
        '[
            {
                "IndexName": "patient_id-index",
                "KeySchema": [
                    {"AttributeName": "patient_id", "KeyType": "HASH"}
                ],
                "Projection": {
                    "ProjectionType": "ALL"
                },
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5
                }
            },
            {
                "IndexName": "doctor_id-start_time-index",
                "KeySchema": [
                    {"AttributeName": "doctor_id", "KeyType": "HASH"},
                    {"AttributeName": "start_time", "KeyType": "RANGE"}
                ],
                "Projection": {
                    "ProjectionType": "ALL"
                },
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5
                }
            }
        ]'

# If using provisioned capacity instead of PAY_PER_REQUEST:
# --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
"""

# To run this FastAPI application locally:
# 1. Install dependencies: pip install fastapi uvicorn "python-dotenv[extra]" boto3 pydantic
# 2. Create a .env file with your AWS credentials/endpoints and SNS Topic ARN:
#    AWS_REGION=us-east-1
#    APPOINTMENTS_TABLE_NAME=NINCAppointments
#    SNS_TOPIC_ARN_APPOINTMENTS=arn:aws:sns:us-east-1:123456789012:NINCAppointmentNotifications
# 3. Ensure your AWS CLI is configured with credentials that have access to DynamoDB and SNS.
# 4. Run the application: uvicorn booking_service:app --reload --port 8001
# 5. Access the API documentation at http://127.0.0.1:8001/docs


################################################################################################
#Code Explanation:
##############################################################################################

# Python Code Explanation
# This code defines a FastAPI application that acts as a booking microservice.
# It handles appointment scheduling by interacting with AWS DynamoDB for data storage and 
# AWS Simple Notification Service (SNS) for sending notifications about appointment events.

# Imports
# The code begins by importing necessary libraries:

# FastAPI, HTTPException, and status from fastapi: Used to build the web API. FastAPI is the main class, HTTPException is used to raise HTTP errors, and status provides convenient access to HTTP status codes.
# BaseModel and Field from pydantic: Used for data validation and serialization/deserialization. BaseModel is the base class for creating data models, and Field is used to add extra information or validation to model fields.
# boto3: The AWS SDK for Python, used to interact with AWS services like DynamoDB and SNS.
# os: Provides a way to interact with the operating system, used here to read environment variables.
# uuid: Used to generate unique identifiers for appointments.
# json: Used for encoding and decoding JSON data, particularly for SNS messages.
# logging: Used for logging messages about the application's activity.
# datetime and timedelta from datetime: Used for working with dates and times.
# Optional, List, Dict, Any, Union from typing: Used for type hinting, which improves code readability and maintainability.
# Enum from enum: Used to create enumerated types for appointment statuses and types.
# from fastapi import FastAPI, HTTPException, status
# from pydantic import BaseModel, Field
# import boto3
# import os
# import uuid
# import json
# import logging
# from datetime import datetime, timedelta
# from typing import Optional, List, Dict, Any, Union
# from enum import Enum
# Use code with caution
# Logging Configuration
# This section sets up basic logging for the application, configuring it to log messages with a level of INFO or higher and specifying the format for the log messages.

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
# Use code with caution
# Configuration Variables
# These variables store configuration settings for the application, primarily related to AWS services. They are read from environment variables if available, otherwise they use default values.

# AWS_REGION: The AWS region where the services are located.
# APPOINTMENTS_TABLE_NAME: The name of the DynamoDB table used to store appointments.
# SNS_TOPIC_ARN_APPOINTMENTS: The Amazon Resource Name (ARN) of the SNS topic used for appointment notifications. Note: The default value is a placeholder and should be replaced with your actual SNS topic ARN.
# # --- Configuration ---
# AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
# APPOINTMENTS_TABLE_NAME = os.getenv("APPOINTMENTS_TABLE_NAME", "NINCAppointments")
# SNS_TOPIC_ARN_APPOINTMENTS = os.getenv("SNS_TOPIC_ARN_APPOINTMENTS", "arn:aws:sns:us-east-1:123456789012:NINCAppointmentNotifications") # Replace with your actual SNS Topic ARN
# Use code with caution
# Enumerated Types
# These Enum classes define the possible values for appointment status and type, making the code more readable and less prone to errors from typos.

# AppointmentStatus: Defines the possible states of an appointment (PENDING, CONFIRMED, CANCELLED, COMPLETED, NO_SHOW).
# AppointmentType: Defines the different types of appointments (CONSULTATION, FOLLOW_UP, TELEMEDICINE, LAB_WORK).
# # --- Enums ---
# class AppointmentStatus(str, Enum):
#     PENDING = "pending"
#     CONFIRMED = "confirmed"
#     CANCELLED = "cancelled"
#     COMPLETED = "completed"
#     NO_SHOW = "no_show"

# class AppointmentType(str, Enum):
#     CONSULTATION = "consultation"
#     FOLLOW_UP = "follow_up"
#     TELEMEDICINE = "telemedicine"
#     LAB_WORK = "lab_work"
# Use code with caution
# Pydantic Models
# These classes, based on Pydantic's BaseModel, define the structure and validation rules for the data involved in creating and responding with appointment information.

# AppointmentCreate: Represents the data required to create a new appointment. It includes fields for patient_id, doctor_id, start_time, end_time, appointment_type, and an optional notes. The Field class is used to add descriptions and specify that certain fields are required (...).
# AppointmentResponse: Represents the structure of an appointment object returned by the API. It includes all fields from AppointmentCreate plus appointment_id, status, created_at, and updated_at.
# # --- Pydantic Models for Data Validation and Serialization ---

# class AppointmentCreate(BaseModel):
#     """
#     Model for creating a new appointment.
#     """
#     patient_id: str = Field(..., description="ID of the patient booking the appointment.")
#     doctor_id: str = Field(..., description="ID of the doctor for the appointment.")
#     start_time: datetime = Field(..., description="Appointment start time (ISO 8601 format).")
#     end_time: datetime = Field(..., description="Appointment end time (ISO 8601 format).")
#     appointment_type: AppointmentType = Field(..., description="Type of appointment (e.g., consultation, telemedicine).")
#     notes: Optional[str] = None

# class AppointmentResponse(BaseModel):
#     """
#     Model for returning appointment details.
#     """
#     appointment_id: str
#     patient_id: str
#     doctor_id: str
#     start_time: datetime
#     end_time: datetime
#     appointment_type: AppointmentType
#     status: AppointmentStatus
#     notes: Optional[str] = None
#     created_at: datetime
#     updated_at: datetime
# Use code with caution
# AWS Service Client Initialization
# These functions initialize and return boto3 clients for interacting with DynamoDB and SNS. They include basic error handling for client initialization.

# get_dynamodb_client(): Creates and returns a boto3 client for DynamoDB, using the configured AWS_REGION.
# get_sns_client(): Creates and returns a boto3 client for SNS, using the configured AWS_REGION.
# # --- AWS Service Clients ---

# def get_dynamodb_client():
#     """
#     Initializes and returns a DynamoDB client.
#     """
#     try:
#         return boto3.client('dynamodb', region_name=AWS_REGION)
#     except Exception as e:
#         logger.error(f"Error initializing DynamoDB client: {e}")
#         raise

# def get_sns_client():
#     """
#     Initializes and returns an SNS client.
#     """
#     try:
#         return boto3.client('sns', region_name=AWS_REGION)
#     except Exception as e:
#         logger.error(f"Error initializing SNS client: {e}")
#         raise
# Use code with caution
# Booking Service Class
# The BookingService class encapsulates the core logic for managing appointments. It handles interactions with DynamoDB to create, retrieve, and update appointments, and it uses SNS to send notifications.

# __init__(): The constructor initializes the DynamoDB and SNS clients and stores the DynamoDB table name.
# _dynamodb_item_to_appointment_response(): A helper method to convert an item retrieved from DynamoDB (which is a dictionary with specific format) into an AppointmentResponse Pydantic model. It includes error handling for missing keys or other conversion issues.
# create_appointment(): This method handles the creation of a new appointment. It generates a unique ID, performs a basic check for doctor availability by querying existing appointments, constructs the item to be saved in DynamoDB, uses put_item to add the item to the table, and sends an SNS notification about the new appointment. It includes error handling for potential conflicts or DynamoDB errors.
# get_appointment(): Retrieves a single appointment from DynamoDB based on its appointment_id using the get_item operation. It returns an AppointmentResponse object or None if the appointment is not found.
# get_appointments_by_patient(): Retrieves all appointments for a specific patient by querying a Global Secondary Index (GSI) on the patient_id attribute. It returns a list of AppointmentResponse objects.
# get_appointments_by_doctor(): Retrieves all appointments for a specific doctor, optionally filtered by a date range, by querying a GSI on the doctor_id and start_time attributes. It returns a list of AppointmentResponse objects.
# update_appointment_status(): Updates the status of an existing appointment in DynamoDB using the update_item operation. It also updates the updated_at timestamp and sends an SNS notification about the status change.
# _send_appointment_notification(): A helper method to send a notification message to the configured SNS topic. It constructs a JSON payload with relevant appointment details and publishes it to SNS. Error handling is included, but notification failures do not prevent the main operation from completing.
# # --- Service Class for Data Operations ---

# class BookingService:
#     """
#     Handles operations related to Appointments in DynamoDB and sends notifications via SNS.
#     """
#     def __init__(self):
#         self.dynamodb = get_dynamodb_client()
#         self.sns = get_sns_client()
#         self.table_name = APPOINTMENTS_TABLE_NAME

#     def _dynamodb_item_to_appointment_response(self, item: Dict[str, Any]) -> AppointmentResponse:
#         """
#         Converts a DynamoDB item dictionary to an AppointmentResponse Pydantic model.
#         """
#         try:
#             return AppointmentResponse(
#                 appointment_id=item['appointment_id']['S'],
#                 patient_id=item['patient_id']['S'],
#                 doctor_id=item['doctor_id']['S'],
#                 start_time=datetime.fromisoformat(item['start_time']['S']),
#                 end_time=datetime.fromisoformat(item['end_time']['S']),
#                 appointment_type=AppointmentType(item['appointment_type']['S']),
#                 status=AppointmentStatus(item['status']['S']),
#                 notes=item.get('notes', {}).get('S'),
#                 created_at=datetime.fromisoformat(item['created_at']['S']),
#                 updated_at=datetime.fromisoformat(item['updated_at']['S'])
#             )
#         except KeyError as e:
#             logger.error(f"Missing key in DynamoDB item: {e}. Item: {item}")
#             raise ValueError(f"Invalid DynamoDB item format: {e}")
#         except Exception as e:
#             logger.error(f"Error converting DynamoDB item to AppointmentResponse: {e}. Item: {item}")
#             raise

#     def create
