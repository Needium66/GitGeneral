############################
#Gemini in action
#################################################################################################################
# This Python code provides a foundational structure for the Patient Management Microservice, demonstrating how to:
###################################################################################################################
# Use FastAPI for building a RESTful API.
# Define data models with Pydantic for request/response validation.
# Interact with AWS DynamoDB for non-relational patient profiles.
# Interact with AWS RDS (PostgreSQL) for structured EHR data using psycopg2.
# Include basic error handling and logging.
# Provide placeholder environment variables for sensitive configurations, emphasizing the need for secure management (e.g., AWS Secrets Manager).
################################################################################################################################################
#Next Steps:
#################################################################################################################################################
# Deployment: Deploy on AWS EKS or ECS, or as a Lambda function (Preferred EKS)
###############################################################################
# Authentication & Authorization: Integrate with AWS Cognito or Fusion Auth (as per the architecture) to secure these API endpoints.
# All endpoints should require authentication, and role-based access control (RBAC) should be implemented
# to ensure only authorized users (patients, doctors, admins) can access specific data.
#######################################################################################################################################
# Data Models: Expand the Patient Profile and EHRRecord models with all necessary fields, including relationships to other services
# (e.g., doctor_id linking to a Doctor Management service).
#######################################################################################################################################
# Error Handling & Validation: Implement more granular error handling and input validation beyond basic Pydantic checks.
#######################################################################################################################################
# Asynchronous Operations: For higher concurrency, ensure database interactions are truly asynchronous if using an async driver or by offloading long-running tasks.
#####################################################################################################################################################################
# Testing: Comprehensive unit, integration, and end-to-end tests are crucial.
#############################################################################################################################
# Monitoring & Logging: Enhance logging details and ensure logs are sent to Grafana/DatadogCloudWatch (Preferes Grafana/Loki)
#############################################################################################################################################
# Security Best Practices: Regularly review security configurations, least privilege IAM roles, network security groups, and data encryption(KMS key).
#############################################################################################
# Database Migrations: Use a tool like Alembic for managing schema changes in PostgreSQL.
# Alembic is a lightweight database migration tool for usage with the SQLAlchemy Database (Toolkit for Python)
################################################################################################################
# S3 Integration: For lab_results_s3_url, you'd need a separate microservice or utility to handle file uploads to S3, generating pre-signed URLs for secure access.
################################################################################################################################################
# TO DO: Microservices for other features#
# Booking                                #
# Payment                                #
# Pharmacy                               #
# Doctor Locator                         #
# Telemedicine                           #
##########################################
#############################################################################################################################################
# Code Description for the Patient Management Service Microservice Backend
#
# This code defines a patient management microservice using the FastAPI framework.
# It's designed to handle patient profiles and their Electronic Health Records (EHRs) by interacting with two different databases:
# AWS DynamoDB for patient profiles and AWS RDS (PostgreSQL) for EHRs.

# Key Libraries Used:

# fastapi: A modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints.
# pydantic: Used for data validation and settings management using Python type hints. It ensures that the data received by the API matches the expected structure.
# boto3: The Amazon Web Services (AWS) SDK for Python, used here to interact with DynamoDB.
# os: Provides a way of using operating system-dependent functionality, used here to read environment variables for configuration.
# psycopg2: A PostgreSQL adapter for Python, used to connect to and interact with the RDS (PostgreSQL) database.
# typing: Provides type hints, which are used extensively for clarity and validation with FastAPI and Pydantic.
# json: Used for working with JSON data, specifically for handling the serialization and deserialization of list/dictionary fields in DynamoDB.
# logging: Used to log messages (informational, errors, etc.) during the application's execution.
# Code Breakdown
# Imports and Logging Configuration
# from fastapi import FastAPI, HTTPException, status
# from pydantic import BaseModel, Field
# import boto3
# import os
# import psycopg2
# from typing import Optional, Dict, Any
# import json
# import logging

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
# Use code with caution
# This section imports all the necessary libraries. It also sets up basic logging, configuring it to display informational messages and above, including a timestamp, the logger's name, the severity level, and the message itself. The logger object is then created for use throughout the application.

# Configuration
# # --- Configuration ---
# # It's crucial to manage sensitive configurations via environment variables
# # or AWS Secrets Manager in a real-world production environment.
# AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
# DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "NINCPatientProfiles")
# RDS_DB_HOST = os.getenv("RDS_DB_HOST", "your-rds-endpoint.amazonaws.com")
# RDS_DB_NAME = os.getenv("RDS_DB_NAME", "ninc_ehr")
# RDS_DB_USER = os.getenv("RDS_DB_USER", "ninc_user")
# RDS_DB_PASSWORD = os.getenv("RDS_DB_PASSWORD", "your_db_password") # Use Secrets Manager!
# Use code with caution
# This block defines configuration variables for connecting to AWS services and the RDS database. It uses os.getenv to read values from environment variables, providing default values if the environment variables are not set. Important: The code includes comments emphasizing that sensitive credentials like RDS_DB_PASSWORD should be managed securely in production, preferably via a service like AWS Secrets Manager, rather than directly in environment variables or code.

# Pydantic Models
# # --- Pydantic Models for Data Validation and Serialization ---

# class PatientProfile(BaseModel):
#     """
#     Represents the patient's demographic and unstructured medical history.
#     Stored in DynamoDB.
#     """
#     patient_id: str = Field(..., description="Unique identifier for the patient.")
#     first_name: str
#     last_name: str
#     date_of_birth: str = Field(..., example="YYYY-MM-DD")
#     gender: Optional[str] = None
#     contact_email: str
#     contact_phone: Optional[str] = None
#     address: Optional[Dict[str, str]] = None
#     allergies: Optional[list[str]] = []
#     past_conditions: Optional[list[str]] = []
#     notes: Optional[str] = None
#     # Add other relevant unstructured data

# class EHRRecord(BaseModel):
#     """
#     Represents structured Electronic Health Record data.
#     Stored in RDS (PostgreSQL).
#     """
#     ehr_id: Optional[str] = Field(None, description="Unique identifier for the EHR record (auto-generated by DB for new records).")
#     patient_id: str = Field(..., description="Foreign key to PatientProfile.")
#     visit_date: str = Field(..., example="YYYY-MM-DDTHH:MM:SSZ")
#     doctor_id: str
#     diagnosis: str
#     prescription: Optional[str] = None
#     lab_results_s3_url: Optional[str] = None # Link to S3 for large files
#     # Add other structured clinical data

# class PatientFullRecord(BaseModel):
#     """
#     Combines patient profile and EHR records for a comprehensive view.
#     """
#     profile: PatientProfile
#     ehr_records: list[EHRRecord] = []
# Use code with caution
# Here, Pydantic BaseModel classes are defined. These models serve two main purposes:

# Data Validation: They define the expected structure and data types for the data exchanged with the API. If incoming data doesn't match a model, FastAPI automatically returns a validation error.
# Data Serialization/Deserialization: They handle converting Python objects to JSON (for API responses) and JSON to Python objects (for API requests).
# PatientProfile: Models the data stored in DynamoDB, representing demographic and unstructured medical history.
# EHRRecord: Models the structured data stored in RDS (PostgreSQL).
# PatientFullRecord: A composite model used for a specific API endpoint that combines the data from a PatientProfile and a list of EHRRecords.
# The Field function from pydantic is used to add extra information about fields, like descriptions and examples, which are used by FastAPI to generate interactive API documentation. Optional from typing indicates that a field can be None.

# AWS Service Clients
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

# def get_rds_connection():
#     """
#     Establishes and returns a PostgreSQL connection to RDS.
#     In a production environment, use a connection pool.
#     """
#     try:
#         conn = psycopg2.connect(
#             host=RDS_DB_HOST,
#             database=RDS_DB_NAME,
#             user=RDS_DB_USER,
#             password=RDS_DB_PASSWORD
#         )
#         return conn
#     except Exception as e:
#         logger.error(f"Error connecting to RDS: {e}")
#         raise
# Use code with caution
# These functions are responsible for creating connections to the databases.

# get_dynamodb_client(): Uses the boto3 library to create a client for interacting with AWS DynamoDB in the specified AWS_REGION.
# get_rds_connection(): Uses the psycopg2 library to establish a connection to the PostgreSQL database running on AWS RDS using the configured host, database name, user, and password. Both functions include basic error handling and logging.
# Service Classes
# # --- Service Classes for Data Operations ---

# class PatientProfileService:
#     """
#     Handles operations related to Patient Profiles in DynamoDB.
#     """
#     def __init__(self):
#         self.dynamodb = get_dynamodb_client()
#         self.table_name = DYNAMODB_TABLE_NAME

#     def get_patient_profile(self, patient_id: str) -> Optional[PatientProfile]:
#         """
#         Retrieves a patient profile by ID from DynamoDB.
#         """
#         try:
#             response = self.dynamodb.get_item(
#                 TableName=self.table_name,
#                 Key={'patient_id': {'S': patient_id}}
#             )
#             item = response.get('Item')
#             if item:
#                 # Convert DynamoDB item format to Python dict, then to Pydantic model
#                 profile_data = {k: v[list(v.keys())[0]] for k, v in item.items()}
#                 # Handle specific types like lists or nested dicts if stored as JSON strings
#                 if 'address' in profile_data and isinstance(profile_data['address'], str):
#                     profile_data['address'] = json.loads(profile_data['address'])
#                 if 'allergies' in profile_data and isinstance(profile_data['allergies'], str):
#                     profile_data['allergies'] = json.loads(profile_data['allergies'])
#                 if 'past_conditions' in profile_data and isinstance(profile_data['past_conditions'], str):
#                     profile_data['past_conditions'] = json.loads(profile_data['past_conditions'])

#                 return PatientProfile(**profile_data)
#             return None
#         except Exception as e:
#             logger.error(f"Error getting patient profile {patient_id} from DynamoDB: {e}")
#             raise

#     def create_or_update_patient_profile(self, profile: PatientProfile) -> PatientProfile:
#         """
#         Creates or updates a patient profile in DynamoDB.
#         """
#         try:
#             # Convert Pydantic model to DynamoDB item format
#             profile_item = profile.dict()
#             # Convert lists/dicts to JSON strings if needed for DynamoDB attributes
#             if 'address' in profile_item and profile_item['address'] is not None:
#                 profile_item['address'] = json.dumps(profile_item['address'])
#             if 'allergies' in profile_item and profile_item['allergies'] is not None:
#                 profile_item['allergies'] = json.dumps(profile_item['allergies'])
#             if 'past_conditions' in profile_item and profile_item['past_conditions'] is not None:
#                 profile_item['past_conditions'] = json.dumps(profile_item['past_conditions'])

#             # Prepare item for put_item
#             dynamodb_item = {k: {'S': str(v)} if isinstance(v, str) else {'N': str(v)} if isinstance(v, (int, float)) else {'BOOL': v} if isinstance(v, bool) else {'NULL': True} if v is None else {'S': json.dumps(v)} for k, v in profile_item.items()}

#             self.dynamodb.put_item(
#                 TableName=self.table_name,
#                 Item=dynamodb_item
#             )
#             return profile
#         except Exception as e:
#             logger.error(f"Error creating/updating patient profile {profile.patient_id} in DynamoDB: {e}")
#             raise

# class EHRService:
#     """
#     Handles operations related to Electronic Health Records in RDS (PostgreSQL).
#     """
#     def get_ehr_records_by_patient_id(self, patient_id: str) -> list[EHRRecord]:
#         """
#         Retrieves all EHR records for a given patient ID from RDS.
#         """
#         conn = None
#         try:
#             conn = get_rds_connection()
#             cur = conn.cursor()
#             cur.execute(
#                 """
#                 SELECT ehr_id, patient_id, visit_date, doctor_id, diagnosis, prescription, lab_results_s3_url
#                 FROM ehr_records
#                 WHERE patient_id = %s;
#                 """,
#                 (patient_id,)
#             )
#             records = []
#             for row in cur.fetchall():
#                 # Convert datetime to ISO format string for Pydantic
#                 visit_date_str = row[2].isoformat() if row[2] else None
#                 records.append(EHRRecord(
#                     ehr_id=str(row[0]), # Assuming ehr_id is UUID or similar string
#                     patient_id=row[1],
#                     visit_date=visit_date_str,
#                     doctor_id=row[3],
#                     diagnosis=row[4],
#                     prescription=row[5],
#                     lab_results_s3_url=row[6]
#                 ))
#             cur.close()
#             return records
#         except Exception as e:
#             logger.error(f"Error getting EHR records for patient {patient_id} from RDS: {e}")
#             raise
#         finally:
#             if conn:
#                 conn.close()

#     def create_ehr_record(self, ehr_record: EHRRecord) -> EHRRecord:
#         """
#         Creates a new EHR record in RDS.
#         """
#         conn = None
#         try:
#             conn = get_rds_connection()
#             cur = conn.cursor()
#             cur.execute(
#                 """
#                 INSERT INTO ehr_records (patient_id, visit_date, doctor_id, diagnosis, prescription, lab_results_s3_url)
#                 VALUES (%s, %s, %s, %s, %s, %s)
#                 RETURNING ehr_id;
#                 """,
#                 (
#                     ehr_record.patient_id,
#                     ehr_record.visit_date, # Assuming ISO format string or convertible
#                     ehr_record.doctor_id,
#                     ehr_record.diagnosis,
#                     ehr_record.prescription,
#                     ehr_record.lab_results_s3_url
#                 )
#             )
#             ehr_record.ehr_id = str(cur.fetchone()[0])
#             conn.commit()
#             cur.close()
#             return ehr_record
#         except Exception as e:
#             logger.error(f"Error creating EHR record for patient {ehr_record.patient_id} in RDS: {e}")
#             if conn:
#                 conn.rollback() # Rollback on error
#             raise
#         finally:
#             if conn:
#                 conn.close()
# Use code with caution
# These classes encapsulate the logic for interacting with the specific databases. This separation of concerns makes the code more organized and maintainable.

# PatientProfileService:

# Initializes with a DynamoDB client and the table name.
# get_patient_profile: Retrieves a patient profile item from DynamoDB using get_item. It includes logic to convert the DynamoDB item format (where each value is nested under a type key like 'S' for string) into a standard Python dictionary and then validates it against the PatientProfile Pydantic model. It also handles deserializing JSON strings for fields like address, allergies, and past_conditions.
# create_or_update_patient_profile: Takes a PatientProfile Pydantic model, converts it into a dictionary, serializes list/dictionary fields into JSON strings (as DynamoDB has limitations on nested data types), and then saves/updates the item in DynamoDB using put_item. It includes logic to prepare the item in the specific DynamoDB format.
# EHRService:

# Includes methods to interact with the RDS (PostgreSQL) database.
# get_ehr_records_by_patient_id: Connects to the RDS database, executes a SQL query to fetch all EHR records for a given patient ID, and maps the database rows to a list of EHRRecord Pydantic models. It handles converting PostgreSQL TIMESTAMP values to ISO format strings for the Pydantic model.
# create_ehr_record: Connects to the RDS database, executes a SQL INSERT statement to create a new EHR record. It retrieves the auto-generated ehr_id after insertion and includes basic transaction management (conn.commit() and conn.rollback()).
# FastAPI Application Setup
# # --- FastAPI Application Setup ---

# app = FastAPI(
#     title="NINC Patient Management Microservice",
#     description="API for managing patient profiles and electronic health records.",
#     version="1.0.0"
# )

# # Initialize service instances
# patient_profile_service = PatientProfileService()
# ehr_service = EHRService()
# Use code with caution
# This section initializes the FastAPI application instance, named app. The title, description, and version arguments are used to populate the automatically generated API documentation (usually available at /docs). It also creates instances of the PatientProfileService and EHRService classes, which will be used by the API endpoints to perform database operations.

# API Endpoints
# # --- API Endpoints ---

# @app.post("/patients/profile", response_model=PatientProfile, status_code=status.HTTP_201_CREATED)
# async def create_patient_profile(profile: PatientProfile):
#     """
#     Creates a new patient profile or updates an existing one.
#     """
#     try:
#         # In a real app, you'd likely generate patient_id server-side
#         # or integrate with an identity service like Cognito.
#         # For simplicity, we assume patient_id is provided in the request.
#         created_profile = patient_profile_service.create_or_update_patient_profile(profile)
#         logger.info(f"Patient profile {profile.patient_id} created/updated successfully.")
#         return created_profile
#     except Exception as e:
#         logger.error(f"Failed to create/update patient profile: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Internal server error: {e}"
#         )

# @app.get("/patients/profile/{patient_id}", response_model=PatientProfile)
# async def get_patient_profile(patient_id: str):
#     """
#     Retrieves a patient profile by ID.
#     """
#     try:
#         profile = patient_profile_service.get_patient_profile(patient_id)
#         if not profile:
#             logger.warning(f"Patient profile with ID {patient_id} not found.")
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")
#         logger.info(f"Retrieved patient profile for ID {patient_id}.")
#         return profile
#     except Exception as e:
#         logger.error(f"Failed to retrieve patient profile: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Internal server error: {e}"
#         )

# @app.post("/patients/{patient_id}/ehr", response_model=EHRRecord, status_code=status.HTTP_201_CREATED)
# async def create_patient_ehr_record(patient_id: str, ehr_record: EHRRecord):
#     """
#     Creates a new EHR record for a specific patient.
#     Ensures the patient_id in the path matches the one in the request body.
#     """
#     if patient_id != ehr_record.patient_id:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Patient ID in path does not match patient ID in EHR record."
#         )
#     try:
#         created_ehr = ehr_service.create_ehr_record(ehr_record)
#         logger.info(f"EHR record created successfully for patient {patient_id}.")
#         return created_ehr
#     except Exception as e:
#         logger.error(f"Failed to create EHR record for patient {patient_id}: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Internal server error: {e}"
#         )

# @app.get("/patients/{patient_id}/ehr", response_model=list[EHRRecord])
# async def get_patient_ehr_records(patient_id: str):
#     """
#     Retrieves all EHR records for a specific patient.
#     """
#     try:
#         ehr_records = ehr_service.get_ehr_records_by_patient_id(patient_id)
#         logger.info(f"Retrieved {len(ehr_records)} EHR records for patient {patient_id}.")
#         return ehr_records
#     except Exception as e:
#         logger.error(f"Failed to retrieve EHR records for patient {patient_id}: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Internal server error: {e}"
#         )

# @app.get("/patients/full_record/{patient_id}", response_model=PatientFullRecord)
# async def get_patient_full_record(patient_id: str):
#     """
#     Retrieves the full patient record, including profile and all associated EHRs.
#     This demonstrates joining data from different databases.
#     """
#     try:
#         profile = patient_profile_service.get_patient_profile(patient_id)
#         if not profile:
#             logger.warning(f"Patient with ID {patient_id} not found for full record retrieval.")
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

#         ehr_records = ehr_service.get_ehr_records_by_patient_id(patient_id)

#         full_record = PatientFullRecord(profile=profile, ehr_records=ehr_records)
#         logger.info(f"Retrieved full record for patient {patient_id}.")
#         return full_record
#     except Exception as e:
#         logger.error(f"Failed to retrieve full record for patient {patient_id}: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Internal server error: {e}"
#         )
# Use code with caution
# These sections define the API endpoints using FastAPI decorators (@app.post, @app.get). Each function decorated represents an endpoint that handles incoming HTTP requests.

# @app.post("/patients/profile", ...): Defines a POST endpoint at /patients/profile. It expects a request body matching the PatientProfile Pydantic model. It uses the patient_profile_service to create or update the profile in DynamoDB. On success, it returns the created/updated PatientProfile with a 201 Created status. Includes error handling.
# @app.get("/patients/profile/{patient_id}", ...): Defines a GET endpoint at /patients/profile/{patient_id}. The {patient_id} in the path is captured as a function argument. It uses the patient_profile_service to retrieve the patient profile from DynamoDB. If the profile is not found, it raises an HTTPException with a 404 Not Found status. Otherwise, it returns the PatientProfile. Includes error handling.
# @app.post("/patients/{patient_id}/ehr", ...): Defines a POST endpoint at /patients/{patient_id}/ehr. It expects a request body matching the EHRRecord Pydantic model and captures patient_id from the path. It includes a validation step to ensure the patient_id in the path matches the patient_id in the request body. It uses the ehr_service to create the EHR record in RDS. Returns the created EHRRecord on success with a 201 Created status. Includes error handling.
# @app.get("/patients/{patient_id}/ehr", ...): Defines a GET endpoint at /patients/{patient_id}/ehr to retrieve all EHR records for a specific patient from RDS using the ehr_service. It returns a list of EHRRecord models. Includes error handling.
# @app.get("/patients/full_record/{patient_id}", ...): Defines a GET endpoint at /patients/full_record/{patient_id} that retrieves both the patient profile from DynamoDB and all associated EHR records from RDS. It then combines them into a PatientFullRecord Pydantic model before returning the response. This demonstrates fetching and combining data from different data sources within a single API endpoint. Includes error handling and handles the case where the patient profile is not found.
# Example Database Schema and Running Instructions
# # --- Example Database Schema for RDS (PostgreSQL) ---
# # This SQL would be used to set up your PostgreSQL database for EHR records.
# # You would run this via a database migration tool or directly.
# """
# CREATE TABLE IF NOT EXISTS ehr_records (
#     ehr_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#     patient_id VARCHAR(255) NOT NULL,
#     visit_date TIMESTAMP WITH TIME ZONE NOT NULL,
#     doctor_id VARCHAR(255) NOT NULL,
#     diagnosis TEXT NOT NULL,
#     prescription TEXT,
#     lab_results_s3_url VARCHAR(2048),
#     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
#     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
# );

# CREATE INDEX IF NOT EXISTS idx_ehr_patient_id ON ehr_records (patient_id);
# """

# # To run this FastAPI application locally:
# # 1. Install dependencies: pip install fastapi uvicorn "python-dotenv[extra]" boto3 psycopg2-binary pydantic
# # 2. Create a .env file with your AWS and RDS credentials/endpoints:
# #    AWS_REGION=us-east-1
# #    DYNAMODB_TABLE_NAME=NINCPatientProfiles
# #    RDS_DB_HOST=your-rds-endpoint.amazonaws.com
# #    RDS_DB_NAME=ninc_ehr
# #    RDS_DB_USER=ninc_user
# #    RDS_DB_PASSWORD=your_db_password
# # 3. Run the application: uvicorn patient_management_service:app --reload --port 8000
# # 4. Access the API documentation at http://127.0.0.1:8000/docs
# Use code with caution
# This final section is commented out and provides helpful information for setting up the database schema for the RDS (PostgreSQL) database and instructions on how to run the FastAPI application locally using uvicorn. It lists the required Python packages and how to set up environment variables (or a .env file) for configuration.

# In summary, this code provides a basic implementation of a patient management microservice using FastAPI to expose API endpoints for creating, retrieving, and managing patient profiles (in DynamoDB) and their associated EHR records (in RDS PostgreSQL).

