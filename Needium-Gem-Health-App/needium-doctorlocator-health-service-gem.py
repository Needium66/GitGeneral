#########################################################################################################################
#Develop the Python code for the Doctor Locator microservice, focusing on searching for and retrieving doctor information.
#########################################################################################################################
#The Code:
################################################################
# doctor_locator_service.py

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import boto3
import os
import json
import logging
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

# Import for OpenSearch (Elasticsearch) client. Install 'opensearch-py' or 'elasticsearch'
# For AWS OpenSearch, it's typically 'opensearch-py'
# pip install opensearch-py
from opensearchpy import OpenSearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth # For signing requests to OpenSearch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# DynamoDB table for full doctor profiles (main source of truth)
DOCTOR_PROFILES_TABLE = os.getenv("DOCTOR_PROFILES_TABLE", "NINCDoctorProfiles")

# AWS OpenSearch (Elasticsearch) configuration
# This should be your OpenSearch Service endpoint without https://
OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "your-opensearch-domain.us-east-1.es.amazonaws.com")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", 443))
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "ninc_doctors")

# --- Pydantic Models for Data Validation and Serialization ---

class DoctorProfile(BaseModel):
    """
    Represents a doctor's detailed profile.
    Primary storage in DynamoDB, indexed in OpenSearch for search.
    """
    doctor_id: str = Field(..., description="Unique identifier for the doctor.")
    first_name: str
    last_name: str
    specialty: str = Field(..., description="Medical specialty of the doctor (e.g., 'Pediatrics', 'Cardiology').")
    location: Dict[str, Union[str, float]] = Field(..., description="Geographic location details including city, state, and lat/lon.")
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    bio: Optional[str] = None
    ratings: Optional[float] = Field(None, ge=1.0, le=5.0, description="Average patient rating.")
    years_of_experience: Optional[int] = Field(None, ge=0)
    # Add other relevant doctor attributes, e.g., insurance accepted, languages spoken, clinic affiliation.

class DoctorSearchRequest(BaseModel):
    """
    Model for requesting a doctor search.
    """
    specialty: Optional[str] = Field(None, description="Filter by medical specialty.")
    city: Optional[str] = Field(None, description="Filter by city.")
    state: Optional[str] = Field(None, description="Filter by state.")
    # For proximity search, you might add 'latitude', 'longitude', 'radius_km'
    # For availability, this service would query the Booking Service
    min_rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Minimum average rating.")
    page_size: int = Field(10, gt=0, description="Number of results per page.")
    page_number: int = Field(1, ge=1, description="Current page number.")

class DoctorSearchResponse(BaseModel):
    """
    Model for returning doctor search results.
    """
    total_results: int
    doctors: List[DoctorProfile]

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

def get_opensearch_client():
    """
    Initializes and returns an OpenSearch client, configured for AWS authentication.
    """
    try:
        # Get AWS credentials from environment or IAM role
        session = boto3.Session()
        credentials = session.get_credentials()
        aws_auth = AWSRequestsAuth(
            aws_access_key=credentials.access_key,
            aws_secret_access_key=credentials.secret_key,
            aws_token=credentials.token, # Only if using temporary credentials (e.g., EC2 instance profile)
            aws_host=OPENSEARCH_HOST,
            aws_region=AWS_REGION,
            aws_service='es' # 'es' for Elasticsearch/OpenSearch Service
        )

        client = OpenSearch(
            hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
            http_auth=aws_auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
        return client
    except Exception as e:
        logger.error(f"Error initializing OpenSearch client: {e}")
        raise

# --- Service Class for Data Operations ---

class DoctorLocatorService:
    """
    Handles operations related to locating and searching for doctors.
    Interacts with DynamoDB for full profiles and OpenSearch for search.
    """
    def __init__(self):
        self.dynamodb = get_dynamodb_client()
        self.opensearch = get_opensearch_client()
        self.doctor_table_name = DOCTOR_PROFILES_TABLE
        self.opensearch_index = OPENSEARCH_INDEX

        # Ensure OpenSearch index exists (in production, this is handled by deployment pipeline)
        self._ensure_opensearch_index()

    def _ensure_opensearch_index(self):
        """
        Ensures the OpenSearch index exists. Creates it if it doesn't.
        Defines a basic mapping for doctor profiles.
        """
        if not self.opensearch.indices.exists(index=self.opensearch_index):
            logger.info(f"OpenSearch index '{self.opensearch_index}' does not exist. Creating it...")
            index_body = {
                'settings': {
                    'index': {
                        'number_of_shards': 1,
                        'number_of_replicas': 0
                    }
                },
                'mappings': {
                    'properties': {
                        'doctor_id': {'type': 'keyword'},
                        'first_name': {'type': 'text'},
                        'last_name': {'type': 'text'},
                        'specialty': {'type': 'keyword'}, # Use keyword for exact match filtering
                        'location.city': {'type': 'keyword'},
                        'location.state': {'type': 'keyword'},
                        'location.latitude': {'type': 'geo_point'}, # For geo-spatial queries
                        'location.longitude': {'type': 'geo_point'},
                        'bio': {'type': 'text'},
                        'ratings': {'type': 'float'},
                        'years_of_experience': {'type': 'integer'}
                    }
                }
            }
            try:
                response = self.opensearch.indices.create(index=self.opensearch_index, body=index_body)
                if response.get('acknowledged'):
                    logger.info(f"OpenSearch index '{self.opensearch_index}' created successfully.")
                else:
                    logger.error(f"Failed to create OpenSearch index: {response}")
            except Exception as e:
                logger.error(f"Error creating OpenSearch index: {e}")
                # In production, this might be a fatal error, but for a service, we'll log and continue.


    def index_doctor_profile(self, doctor_profile: DoctorProfile):
        """
        Indexes a doctor's profile in OpenSearch.
        This method would typically be called by a Doctor Management service
        when a doctor's profile is created or updated.
        """
        try:
            # Prepare document for OpenSearch. Flatten nested objects if necessary for mapping.
            doc = doctor_profile.dict()
            # If lat/lon are separate, combine them into a geo_point for OpenSearch
            if 'latitude' in doc.get('location', {}) and 'longitude' in doc.get('location', {}):
                 doc['location']['geo_point'] = {
                     'lat': doc['location']['latitude'],
                     'lon': doc['location']['longitude']
                 }

            response = self.opensearch.index(
                index=self.opensearch_index,
                id=doctor_profile.doctor_id,
                body=doc,
                refresh=True # Make document immediately searchable
            )
            logger.info(f"Doctor {doctor_profile.doctor_id} indexed/updated in OpenSearch: {response['result']}")
            return response
        except Exception as e:
            logger.error(f"Error indexing doctor profile {doctor_profile.doctor_id} in OpenSearch: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to index doctor profile: {e}")

    def get_doctor_profile_from_dynamodb(self, doctor_id: str) -> Optional[DoctorProfile]:
        """
        Retrieves a doctor's full profile from DynamoDB.
        """
        try:
            response = self.dynamodb.get_item(
                TableName=self.doctor_table_name,
                Key={'doctor_id': {'S': doctor_id}}
            )
            item = response.get('Item')
            if item:
                # Convert DynamoDB item format to Python dict, then to Pydantic model
                profile_data = {k: v[list(v.keys())[0]] for k, v in item.items()}
                # Handle specific types like nested dicts if stored as JSON strings
                if 'location' in profile_data and isinstance(profile_data['location'], str):
                    profile_data['location'] = json.loads(profile_data['location'])
                return DoctorProfile(**profile_data)
            return None
        except Exception as e:
            logger.error(f"Error getting doctor profile {doctor_id} from DynamoDB: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve doctor profile from DynamoDB: {e}")

    def search_doctors(self, search_request: DoctorSearchRequest) -> DoctorSearchResponse:
        """
        Searches for doctors in OpenSearch based on provided criteria.
        """
        query_body = {
            "query": {
                "bool": {
                    "must": []
                }
            },
            "from": (search_request.page_number - 1) * search_request.page_size,
            "size": search_request.page_size
        }

        if search_request.specialty:
            query_body["query"]["bool"]["must"].append({
                "term": {"specialty.keyword": search_request.specialty.lower()} # Assuming lowercase for search
            })
        if search_request.city:
            query_body["query"]["bool"]["must"].append({
                "term": {"location.city.keyword": search_request.city.lower()}
            })
        if search_request.state:
            query_body["query"]["bool"]["must"].append({
                "term": {"location.state.keyword": search_request.state.lower()}
            })
        if search_request.min_rating:
            query_body["query"]["bool"]["must"].append({
                "range": {"ratings": {"gte": search_request.min_rating}}
            })

        # If no specific 'must' clauses, match all (otherwise bool must be empty)
        if not query_body["query"]["bool"]["must"]:
            query_body["query"] = {"match_all": {}}

        try:
            response = self.opensearch.search(
                index=self.opensearch_index,
                body=query_body
            )
            hits = response['hits']['hits']
            total_results = response['hits']['total']['value']

            doctors = []
            for hit in hits:
                # Retrieve full profile from DynamoDB using the doctor_id from OpenSearch
                doctor_id = hit['_source']['doctor_id']
                full_profile = self.get_doctor_profile_from_dynamodb(doctor_id)
                if full_profile:
                    doctors.append(full_profile)
                else:
                    logger.warning(f"Doctor {doctor_id} found in OpenSearch but not in DynamoDB. Skipping.")

            logger.info(f"Search found {total_results} results, returning {len(doctors)} doctors.")
            return DoctorSearchResponse(total_results=total_results, doctors=doctors)
        except Exception as e:
            logger.error(f"Error searching for doctors in OpenSearch: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to search for doctors: {e}")

# --- FastAPI Application Setup ---

app = FastAPI(
    title="NINC Doctor Locator Microservice",
    description="API for finding and retrieving doctor information.",
    version="1.0.0"
)

# Initialize service instance
doctor_locator_service = DoctorLocatorService()

# --- API Endpoints ---

@app.post("/doctors/search", response_model=DoctorSearchResponse)
async def search_for_doctors(search_request: DoctorSearchRequest):
    """
    Searches for doctors based on criteria such as specialty, city, state, and minimum rating.
    """
    return doctor_locator_service.search_doctors(search_request)

@app.get("/doctors/{doctor_id}", response_model=DoctorProfile)
async def get_doctor_details(doctor_id: str):
    """
    Retrieves the full profile details for a specific doctor by their ID.
    """
    doctor_profile = doctor_locator_service.get_doctor_profile_from_dynamodb(doctor_id)
    if not doctor_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return doctor_profile

@app.post("/doctors/index", status_code=status.HTTP_202_ACCEPTED)
async def index_doctor(doctor_profile: DoctorProfile):
    """
    Internal endpoint to index or re-index a doctor's profile in OpenSearch.
    In a real system, this would be triggered by events from a Doctor Management service,
    not directly exposed to the public internet without strong authentication/authorization.
    """
    await doctor_locator_service.index_doctor_profile(doctor_profile)
    return {"message": "Doctor profile indexing initiated."}

# --- Example AWS Resource Setup Commands ---
# You would run these AWS CLI commands or use CloudFormation/Terraform to set up your AWS resources.

"""
# 1. Create DynamoDB Table for Doctor Profiles (main data store)
aws dynamodb create-table \
    --table-name NINCDoctorProfiles \
    --attribute-definitions \
        AttributeName=doctor_id,AttributeType=S \
    --key-schema \
        AttributeName=doctor_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# 2. Create AWS OpenSearch Service Domain
# This is a more involved setup, often done via CloudFormation or AWS Console.
# Example CLI (simplified):
# aws opensearch create-domain \
#     --domain-name ninc-doctors-domain \
#     --engine-version OpenSearch_2.11 \
#     --cluster-config InstanceType=t3.small.search,InstanceCount=1 \
#     --ebs-options Iops=3000,VolumeSize=10,VolumeType=gp3 \
#     --node-to-node-encryption-options Enabled=true \
#     --encryption-at-rest-options Enabled=true,KmsKeyId=alias/aws/aes_default \
#     --domain-endpoint-options EnforceHTTPS=true,TLSSecurityPolicy=Policy-Min-TLS-1-2-2019-06 \
#     --access-policies '{
#         "Version": "2012-10-17",
#         "Statement": [
#             {
#                 "Effect": "Allow",
#                 "Principal": {
#                     "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:user/your-admin-user" # Or role for ECS/Lambda
#                 },
#                 "Action": "es:*",
#                 "Resource": "arn:aws:es:YOUR_REGION:YOUR_ACCOUNT_ID:domain/ninc-doctors-domain/*"
#             }
#         ]
#     }'
# Remember to update YOUR_ACCOUNT_ID and YOUR_REGION.
# The `access-policies` should grant the IAM role used by this microservice `es:ESHttp*` or `es:search` permissions.

# 3. Ensure IAM Role for your FastAPI application has:
#    - DynamoDB permissions: dynamodb:GetItem, dynamodb:PutItem (if indexing doctor data)
#    - OpenSearch permissions: es:ESHttpGet, es:ESHttpPost (for search and indexing)
#    - KMS permissions: if you need to encrypt/decrypt anything within this service (not explicitly used for PII in this example, but good practice).
"""

# To run this FastAPI application locally:
# 1. Install dependencies: pip install fastapi uvicorn "python-dotenv[extra]" boto3 pydantic opensearch-py aws-requests-auth
# 2. Create a .env file with your AWS credentials/endpoints:
#    AWS_REGION=us-east-1
#    DOCTOR_PROFILES_TABLE=NINCDoctorProfiles
#    OPENSEARCH_HOST=your-opensearch-domain.us-east-1.es.amazonaws.com # Replace with your actual domain endpoint
#    OPENSEARCH_PORT=443
#    OPENSEARCH_INDEX=ninc_doctors
# 3. Ensure your AWS CLI is configured with credentials that have access to DynamoDB and OpenSearch.
# 4. Run the application: uvicorn doctor_locator_service:app --reload --port 8003
# 5. Access the API documentation at http://127.0.0.1:8003/docs


###########################################################################
#Code Description:
##########################################################################

# Overview
# This Python code defines a microservice using the FastAPI framework to find and retrieve doctor information. 
# It interacts with two AWS services: DynamoDB and OpenSearch (or Elasticsearch).

# DynamoDB is used as the primary data store for the complete doctor profiles, holding all detailed information.

# OpenSearch is used for searching doctor profiles efficiently based on various criteria like specialty, location, and ratings. OpenSearch acts as an index of the data stored in DynamoDB.

# The service provides three API endpoints:

# /doctors/search (POST): To search for doctors based on specified criteria.
# /doctors/{doctor_id} (GET): To retrieve the full profile of a specific doctor using their ID.
# /doctors/index (POST): An internal endpoint to index or re-index a doctor's profile in OpenSearch.
# Code Breakdown
# # doctor_locator_service.py

# from fastapi import FastAPI, HTTPException, status
# from pydantic import BaseModel, Field
# import boto3
# import os
# import json
# import logging
# from typing import Optional, List, Dict, Any, Union
# from datetime import datetime

# # Import for OpenSearch (Elasticsearch) client. Install 'opensearch-py' or 'elasticsearch'
# # For AWS OpenSearch, it's typically 'opensearch-py'
# # pip install opensearch-py
# from opensearchpy import OpenSearch, RequestsHttpConnection
# from aws_requests_auth.aws_auth import AWSRequestsAuth # For signing requests to OpenSearch

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
# Use code with caution
# This block imports necessary libraries.

# FastAPI, HTTPException, status: For building the web API and handling HTTP responses/errors.
# pydantic, BaseModel, Field: For defining data models and validating request/response data.
# boto3: The AWS SDK for Python, used to interact with AWS services like DynamoDB and OpenSearch.
# os: Used to access environment variables for configuration.
# json: For handling JSON data.
# logging: For logging information and errors.
# typing: Provides type hints for better code readability and maintainability.
# datetime: Though imported, it's not explicitly used in the provided code snippet.
# OpenSearch, RequestsHttpConnection from opensearchpy: The client library for interacting with OpenSearch.
# AWSRequestsAuth from aws_requests_auth.aws_auth: Used to sign requests to AWS-managed OpenSearch domains, which require AWS SigV4 authentication.
# # --- Configuration ---
# AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# # DynamoDB table for full doctor profiles (main source of truth)
# DOCTOR_PROFILES_TABLE = os.getenv("DOCTOR_PROFILES_TABLE", "NINCDoctorProfiles")

# # AWS OpenSearch (Elasticsearch) configuration
# # This should be your OpenSearch Service endpoint without https://
# OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "your-opensearch-domain.us-east-1.es.amazonaws.com")
# OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", 443))
# OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "ninc_doctors")
# Use code with caution
# This section sets up the configuration for the service. It reads values from environment variables using os.getenv. If an environment variable is not set, it provides a default value.

# AWS_REGION: The AWS region where the services are deployed. Defaults to 'us-east-1'.
# DOCTOR_PROFILES_TABLE: The name of the DynamoDB table storing doctor profiles. Defaults to 'NINCDoctorProfiles'.
# OPENSEARCH_HOST: The endpoint of the AWS OpenSearch domain. Defaults to a placeholder. You must replace this with your actual OpenSearch endpoint.
# OPENSEARCH_PORT: The port for connecting to OpenSearch, typically 443 for HTTPS. Defaults to 443.
# OPENSEARCH_INDEX: The name of the OpenSearch index used for searching doctors. Defaults to 'ninc_doctors'.
# # --- Pydantic Models for Data Validation and Serialization ---

# class DoctorProfile(BaseModel):
#     """
#     Represents a doctor's detailed profile.
#     Primary storage in DynamoDB, indexed in OpenSearch for search.
#     """
#     doctor_id: str = Field(..., description="Unique identifier for the doctor.")
#     first_name: str
#     last_name: str
#     specialty: str = Field(..., description="Medical specialty of the doctor (e.g., 'Pediatrics', 'Cardiology').")
#     location: Dict[str, Union[str, float]] = Field(..., description="Geographic location details including city, state, and lat/lon.")
#     contact_email: Optional[str] = None
#     contact_phone: Optional[str] = None
#     bio: Optional[str] = None
#     ratings: Optional[float] = Field(None, ge=1.0, le=5.0, description="Average patient rating.")
#     years_of_experience: Optional[int] = Field(None, ge=0)
#     # Add other relevant doctor attributes, e.g., insurance accepted, languages spoken, clinic affiliation.

# class DoctorSearchRequest(BaseModel):
#     """
#     Model for requesting a doctor search.
#     """
#     specialty: Optional[str] = Field(None, description="Filter by medical specialty.")
#     city: Optional[str] = Field(None, description="Filter by city.")
#     state: Optional[str] = Field(None, description="Filter by state.")
#     # For proximity search, you might add 'latitude', 'longitude', 'radius_km'
#     # For availability, this service would query the Booking Service
#     min_rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Minimum average rating.")
#     page_size: int = Field(10, gt=0, description="Number of results per page.")
#     page_number: int = Field(1, ge=1, description="Current page number.")

# class DoctorSearchResponse(BaseModel):
#     """
#     Model for returning doctor search results.
#     """
#     total_results: int
#     doctors: List[DoctorProfile]
# Use code with caution
# This section defines Pydantic models. Pydantic is used to define the structure and data types of the data that will be sent and received by the API. It also provides data validation.

# DoctorProfile: Represents the detailed information about a doctor. This model is used for the full profile stored in DynamoDB and indexed in OpenSearch. Field is used to add descriptions and validation constraints (like ge for greater than or equal to, le for less than or equal to). The ... indicates a required field.
# DoctorSearchRequest: Defines the structure of the request body when searching for doctors. It includes optional filters like specialty, city, state, and min_rating, as well as pagination parameters (page_size, page_number).
# DoctorSearchResponse: Defines the structure of the response body for doctor search results. It includes the total_results found and a list of doctors (each being a DoctorProfile object).
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

# def get_opensearch_client():
#     """
#     Initializes and returns an OpenSearch client, configured for AWS authentication.
#     """
#     try:
#         # Get AWS credentials from environment or IAM role
#         session = boto3.Session()
#         credentials = session.get_credentials()
#         aws_auth = AWSRequestsAuth(
#             aws_access_key=credentials.access_key,
#             aws_secret_access_key=credentials.secret_key,
#             aws_token=credentials.token, # Only if using temporary credentials (e.g., EC2 instance profile)
#             aws_host=OPENSEARCH_HOST,
#             aws_region=AWS_REGION,
#             aws_service='es' # 'es' for Elasticsearch/OpenSearch Service
#         )

#         client = OpenSearch(
#             hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
#             http_auth=aws_auth,
#             use_ssl=True,
#             verify_certs=True,
#             connection_class=RequestsHttpConnection
#         )
#         return client
#     except Exception as e:
#         logger.error(f"Error initializing OpenSearch client: {e}")
#         raise
# Use code with caution
# This section contains functions to initialize the AWS service clients:

# get_dynamodb_client(): Creates and returns a boto3 client for DynamoDB in the specified AWS_REGION. Includes error handling and logging.
# get_opensearch_client(): Creates and returns an opensearchpy client for OpenSearch. This function specifically handles AWS authentication (AWSRequestsAuth) using credentials obtained from the current AWS session (which could be from environment variables, IAM roles, etc.). It configures the client to connect to the specified OPENSEARCH_HOST and OPENSEARCH_PORT using HTTPS and verifying SSL certificates. Includes error handling and logging.
# # --- Service Class for Data Operations ---

# class DoctorLocatorService:
#     """
#     Handles operations related to locating and searching for doctors.
#     Interacts with DynamoDB for full profiles and OpenSearch for search.
#     """
#     def __init__(self):
#         self.dynamodb = get_dynamodb_client()
#         self.opensearch = get_opensearch_client()
#         self.doctor_table_name = DOCTOR_PROFILES_TABLE
#         self.opensearch_index = OPENSEARCH_INDEX

#         # Ensure OpenSearch index exists (in production, this is handled by deployment pipeline)
#         self._ensure_opensearch_index()

#     def _ensure_opensearch_index(self):
#         """
#         Ensures the OpenSearch index exists. Creates it if it doesn't.
#         Defines a basic mapping for doctor profiles.
#         """
#         if not self.opensearch.indices.exists(index=self.opensearch_index):
#             logger.info(f"OpenSearch index '{self.opensearch_index}' does not exist. Creating it...")
#             index_body = {
#                 'settings': {
#                     'index': {
#                         'number_of_shards': 1,
#                         'number_of_replicas': 0
#                     }
#                 },
#                 'mappings': {
#                     'properties': {
#                         'doctor_id': {'type': 'keyword'},
#                         'first_name': {'type': 'text'},
#                         'last_name': {'type': 'text'},
#                         'specialty': {'type': 'keyword'}, # Use keyword for exact match filtering
#                         'location.city': {'type': 'keyword'},
#                         'location.state': {'type': 'keyword'},
#                         'location.latitude': {'type': 'geo_point'}, # For geo-spatial queries
#                         'location.longitude': {'type': 'geo_point'},
#                         'bio': {'type': 'text'},
#                         'ratings': {'type': 'float'},
#                         'years_of_experience': {'type': 'integer'}
#                     }
#                 }
#             }
#             try:
#                 response = self.opensearch.indices.create(index=self.opensearch_index, body=index_body)
#                 if response.get('acknowledged'):
#                     logger.info(f"OpenSearch index '{self.opensearch_index}' created successfully.")
#                 else:
#                     logger.error(f"Failed to create OpenSearch index: {response}")
#             except Exception as e:
#                 logger.error(f"Error creating OpenSearch index: {e}")
#                 # In production, this might be a fatal error, but for a service, we'll log and continue.


#     def index_doctor_profile(self, doctor_profile: DoctorProfile):
#         """
#         Indexes a doctor's profile in OpenSearch.
#         This method would typically be called by a Doctor Management service
#         when a doctor's profile is created or updated.
#         """
#         try:
#             # Prepare document for OpenSearch. Flatten nested objects if necessary for mapping.
#             doc = doctor_profile.dict()
#             # If lat/lon are separate, combine them into a geo_point for OpenSearch
#             if 'latitude' in doc.get('location', {}) and 'longitude' in doc.get('location', {}):
#                  doc['location']['geo_point'] = {
#                      'lat': doc['location']['latitude'],
#                      'lon': doc['location']['longitude']
#                  }

#             response = self.opensearch.index(
#                 index=self.opensearch_index,
#                 id=doctor_profile.doctor_id,
#                 body=doc,
#                 refresh=True # Make document immediately searchable
#             )
#             logger.info(f"Doctor {doctor_profile.doctor_id} indexed/updated in OpenSearch: {response['result']}")
#             return response
#         except Exception as e:
#             logger.error(f"Error indexing doctor profile {doctor_profile.doctor_id} in OpenSearch: {e}")
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to index doctor profile: {e}")

#     def get_doctor_profile_from_dynamodb(self, doctor_id: str) -> Optional[DoctorProfile]:
#         """
#         Retrieves a doctor's full profile from DynamoDB.
#         """
#         try:
#             response = self.dynamodb.get_item(
#                 TableName=self.doctor_table_name,
#                 Key={'doctor_id': {'S': doctor_id}}
#             )
#             item = response.get('Item')
#             if item:
#                 # Convert DynamoDB item format to Python dict, then to Pydantic model
#                 profile_data = {k: v[list(v.keys())[0]] for k, v in item.items()}
#                 # Handle specific types like nested dicts if stored as JSON strings
#                 if 'location' in profile_data and isinstance(profile_data['location'], str):
#                     profile_data['location'] = json.loads(profile_data['location'])
#                 return DoctorProfile(**profile_data)
#             return None
#         except Exception as e:
#             logger.error(f"Error getting doctor profile {doctor_id} from DynamoDB: {e}")
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve doctor profile from DynamoDB: {e}")

#     def search_doctors(self, search_request: DoctorSearchRequest) -> DoctorSearchResponse:
#         """
#         Searches for doctors in OpenSearch based on provided criteria.
#         """
#         query_body = {
#             "query": {
#                 "bool": {
#                     "must": []
#                 }
#             },
#             "from": (search_request.page_number - 1) * search_request.page_size,
#             "size": search_request.page_size
#         }

#         if search_request.specialty

