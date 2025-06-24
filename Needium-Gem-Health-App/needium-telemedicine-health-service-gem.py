############################################################
#Here is the Python code for the NINC Telemedicine microservice, as requested. 
#This service focuses on managing secure video consultations, leveraging AWS Chime SDK for real-time communication.
###################################################################################################################

# telemedicine_service.py

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
TELEMEDICINE_SESSIONS_TABLE_NAME = os.getenv("TELEMEDICINE_SESSIONS_TABLE_NAME", "NINCTelemedicineSessions")
# S3 Bucket for Chime SDK meeting recordings (must be configured to allow Chime to write)
CHIME_RECORDING_BUCKET = os.getenv("CHIME_RECORDING_BUCKET", "ninc-chime-recordings-your-account-id")

# --- Enums ---
class SessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    ENDED = "ended"
    CANCELLED = "cancelled"

class UserType(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"

# --- Pydantic Models for Data Validation and Serialization ---

class TelemedicineSessionCreate(BaseModel):
    """
    Model for creating a new telemedicine session.
    """
    patient_id: str
    doctor_id: str
    scheduled_start_time: datetime = Field(..., description="Scheduled start time of the session (ISO 8601 format).")
    scheduled_end_time: datetime = Field(..., description="Scheduled end time of the session (ISO 8601 format).")
    description: Optional[str] = None
    # Potentially link to an appointment_id from the Booking Service

class TelemedicineSessionResponse(BaseModel):
    """
    Model for returning telemedicine session details.
    """
    session_id: str
    patient_id: str
    doctor_id: str
    scheduled_start_time: datetime
    scheduled_end_time: datetime
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    status: SessionStatus
    description: Optional[str] = None
    meeting_id: Optional[str] = Field(None, description="AWS Chime SDK Meeting ID.")
    meeting_region: Optional[str] = Field(None, description="AWS Chime SDK Meeting Region.")
    recording_s3_key: Optional[str] = Field(None, description="S3 key for the recorded session file.")
    is_recording_active: bool = False
    created_at: datetime
    updated_at: datetime

class JoinSessionRequest(BaseModel):
    """
    Model for a user requesting to join a telemedicine session.
    """
    user_id: str = Field(..., description="The ID of the user joining (patient_id or doctor_id).")
    user_type: UserType = Field(..., description="The type of user joining (patient, doctor, admin).")
    user_name: str = Field(..., description="Display name for the user in the Chime meeting.")

class ChimeMeetingInfo(BaseModel):
    """
    Details about the Chime meeting to pass to the frontend.
    """
    meeting_id: str
    external_meeting_id: str
    media_region: str
    media_placement: Dict[str, str]

class ChimeAttendeeInfo(BaseModel):
    """
    Details about the Chime attendee to pass to the frontend.
    """
    attendee_id: str
    external_user_id: str
    join_token: str

class JoinSessionResponse(BaseModel):
    """
    Response model for joining a session, containing Chime details.
    """
    session_id: str
    meeting_info: ChimeMeetingInfo
    attendee_info: ChimeAttendeeInfo

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

def get_chime_sdk_meetings_client():
    """
    Initializes and returns an AWS Chime SDK Meetings client.
    """
    try:
        return boto3.client('chime-sdk-meetings', region_name=AWS_REGION)
    except Exception as e:
        logger.error(f"Error initializing Chime SDK Meetings client: {e}")
        raise

# --- Service Class for Data Operations ---

class TelemedicineService:
    """
    Handles operations related to telemedicine sessions, interacting with DynamoDB and AWS Chime SDK.
    """
    def __init__(self):
        self.dynamodb = get_dynamodb_client()
        self.chime_meetings = get_chime_sdk_meetings_client()
        self.sessions_table_name = TELEMEDICINE_SESSIONS_TABLE_NAME
        self.recording_bucket = CHIME_RECORDING_BUCKET

    def _dynamodb_item_to_session_response(self, item: Dict[str, Any]) -> TelemedicineSessionResponse:
        """
        Converts a DynamoDB item dictionary to a TelemedicineSessionResponse Pydantic model.
        """
        try:
            return TelemedicineSessionResponse(
                session_id=item['session_id']['S'],
                patient_id=item['patient_id']['S'],
                doctor_id=item['doctor_id']['S'],
                scheduled_start_time=datetime.fromisoformat(item['scheduled_start_time']['S']),
                scheduled_end_time=datetime.fromisoformat(item['scheduled_end_time']['S']),
                actual_start_time=datetime.fromisoformat(item['actual_start_time']['S']) if 'actual_start_time' in item else None,
                actual_end_time=datetime.fromisoformat(item['actual_end_time']['S']) if 'actual_end_time' in item else None,
                status=SessionStatus(item['status']['S']),
                description=item.get('description', {}).get('S'),
                meeting_id=item.get('meeting_id', {}).get('S'),
                meeting_region=item.get('meeting_region', {}).get('S'),
                recording_s3_key=item.get('recording_s3_key', {}).get('S'),
                is_recording_active=item.get('is_recording_active', {}).get('BOOL', False),
                created_at=datetime.fromisoformat(item['created_at']['S']),
                updated_at=datetime.fromisoformat(item['updated_at']['S'])
            )
        except KeyError as e:
            logger.error(f"Missing key in DynamoDB item for Telemedicine Session: {e}. Item: {item}")
            raise ValueError(f"Invalid DynamoDB item format for Telemedicine Session: {e}")
        except Exception as e:
            logger.error(f"Error converting DynamoDB item to TelemedicineSessionResponse: {e}. Item: {item}")
            raise

    def create_session(self, session_data: TelemedicineSessionCreate) -> TelemedicineSessionResponse:
        """
        Creates a new telemedicine session record. Does NOT create a Chime meeting yet.
        """
        session_id = str(uuid.uuid4())
        current_time = datetime.now()

        item = {
            'session_id': {'S': session_id},
            'patient_id': {'S': session_data.patient_id},
            'doctor_id': {'S': session_data.doctor_id},
            'scheduled_start_time': {'S': session_data.scheduled_start_time.isoformat()},
            'scheduled_end_time': {'S': session_data.scheduled_end_time.isoformat()},
            'status': {'S': SessionStatus.SCHEDULED.value},
            'description': {'S': session_data.description} if session_data.description else {'NULL': True},
            'is_recording_active': {'BOOL': False}, # Default to not recording
            'created_at': {'S': current_time.isoformat()},
            'updated_at': {'S': current_time.isoformat()}
        }

        try:
            self.dynamodb.put_item(
                TableName=self.sessions_table_name,
                Item=item,
                ConditionExpression="attribute_not_exists(session_id)"
            )
            created_session = self._dynamodb_item_to_session_response(item)
            logger.info(f"Telemedicine session {session_id} scheduled for patient {session_data.patient_id} and doctor {session_data.doctor_id}.")
            return created_session
        except self.dynamodb.exceptions.ConditionalCheckFailedException:
            logger.error(f"Session ID {session_id} already exists.")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session ID conflict.")
        except Exception as e:
            logger.error(f"Error creating telemedicine session: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create telemedicine session: {e}")

    def get_session(self, session_id: str) -> Optional[TelemedicineSessionResponse]:
        """
        Retrieves a single telemedicine session by its ID.
        """
        try:
            response = self.dynamodb.get_item(
                TableName=self.sessions_table_name,
                Key={'session_id': {'S': session_id}}
            )
            item = response.get('Item')
            if item:
                return self._dynamodb_item_to_session_response(item)
            return None
        except Exception as e:
            logger.error(f"Error getting telemedicine session {session_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve telemedicine session: {e}")

    def get_sessions_by_patient(self, patient_id: str) -> List[TelemedicineSessionResponse]:
        """
        Retrieves all telemedicine sessions for a given patient. Requires a GSI on patient_id.
        """
        try:
            response = self.dynamodb.query(
                TableName=self.sessions_table_name,
                IndexName='patient_id-index', # Ensure this GSI exists
                KeyConditionExpression='patient_id = :patient_id',
                ExpressionAttributeValues={':patient_id': {'S': patient_id}}
            )
            sessions = [self._dynamodb_item_to_session_response(item) for item in response.get('Items', [])]
            logger.info(f"Retrieved {len(sessions)} sessions for patient {patient_id}.")
            return sessions
        except Exception as e:
            logger.error(f"Error getting sessions for patient {patient_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve patient sessions: {e}")

    def get_sessions_by_doctor(self, doctor_id: str) -> List[TelemedicineSessionResponse]:
        """
        Retrieves all telemedicine sessions for a given doctor. Requires a GSI on doctor_id.
        """
        try:
            response = self.dynamodb.query(
                TableName=self.sessions_table_name,
                IndexName='doctor_id-index', # Ensure this GSI exists
                KeyConditionExpression='doctor_id = :doctor_id',
                ExpressionAttributeValues={':doctor_id': {'S': doctor_id}}
            )
            sessions = [self._dynamodb_item_to_session_response(item) for item in response.get('Items', [])]
            logger.info(f"Retrieved {len(sessions)} sessions for doctor {doctor_id}.")
            return sessions
        except Exception as e:
            logger.error(f"Error getting sessions for doctor {doctor_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve doctor sessions: {e}")

    def join_session(self, session_id: str, join_request: JoinSessionRequest) -> JoinSessionResponse:
        """
        Allows a user to join a telemedicine session.
        If no Chime meeting exists for the session, it creates one.
        Generates an attendee token for the user.
        """
        session = self.get_session(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemedicine session not found.")

        # Basic authorization check: ensure the joining user is the patient or doctor for the session
        # In a real app, this would be integrated with a robust auth system
        if join_request.user_type == UserType.PATIENT and join_request.user_id != session.patient_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to join this session as patient.")
        if join_request.user_type == UserType.DOCTOR and join_request.user_id != session.doctor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to join this session as doctor.")

        meeting_id = session.meeting_id
        meeting_info = None

        # If meeting_id doesn't exist, create a new Chime meeting
        if not meeting_id:
            try:
                # ExternalMeetingId helps link Chime meeting to our internal session_id
                create_meeting_response = self.chime_meetings.create_meeting(
                    ClientRequestToken=str(uuid.uuid4()), # Unique token for idempotency
                    ExternalMeetingId=session_id,
                    MediaRegion=AWS_REGION, # Use the same region for Chime as the service
                    Tags=[
                        {'Key': 'NINCSessionId', 'Value': session_id},
                        {'Key': 'PatientId', 'Value': session.patient_id},
                        {'Key': 'DoctorId', 'Value': session.doctor_id}
                    ]
                )
                meeting = create_meeting_response['Meeting']
                meeting_id = meeting['MeetingId']
                meeting_info = ChimeMeetingInfo(
                    meeting_id=meeting['MeetingId'],
                    external_meeting_id=meeting['ExternalMeetingId'],
                    media_region=meeting['MediaRegion'],
                    media_placement=meeting['MediaPlacement']
                )

                # Update session in DynamoDB with Chime meeting details
                self.dynamodb.update_item(
                    TableName=self.sessions_table_name,
                    Key={'session_id': {'S': session_id}},
                    UpdateExpression="SET meeting_id = :mid, meeting_region = :mregion, #st = :status, actual_start_time = :ast, updated_at = :ua",
                    ExpressionAttributeNames={'#st': 'status'},
                    ExpressionAttributeValues={
                        ':mid': {'S': meeting_id},
                        ':mregion': {'S': AWS_REGION},
                        ':status': {'S': SessionStatus.IN_PROGRESS.value},
                        ':ast': {'S': datetime.now().isoformat()},
                        ':ua': {'S': datetime.now().isoformat()}
                    },
                    ReturnValues="UPDATED_NEW"
                )
                logger.info(f"Created new Chime meeting {meeting_id} for session {session_id}.")

            except Exception as e:
                logger.error(f"Error creating Chime meeting for session {session_id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create Chime meeting.")
        else:
            # If meeting_id exists, fetch existing meeting info
            try:
                get_meeting_response = self.chime_meetings.get_meeting(MeetingId=meeting_id)
                meeting = get_meeting_response['Meeting']
                meeting_info = ChimeMeetingInfo(
                    meeting_id=meeting['MeetingId'],
                    external_meeting_id=meeting['ExternalMeetingId'],
                    media_region=meeting['MediaRegion'],
                    media_placement=meeting['MediaPlacement']
                )
                # Ensure status is 'in_progress'
                if session.status == SessionStatus.SCHEDULED:
                     self.dynamodb.update_item(
                        TableName=self.sessions_table_name,
                        Key={'session_id': {'S': session_id}},
                        UpdateExpression="SET #st = :status, actual_start_time = :ast, updated_at = :ua",
                        ExpressionAttributeNames={'#st': 'status'},
                        ExpressionAttributeValues={
                            ':status': {'S': SessionStatus.IN_PROGRESS.value},
                            ':ast': {'S': datetime.now().isoformat()},
                            ':ua': {'S': datetime.now().isoformat()}
                        },
                        ReturnValues="UPDATED_NEW"
                    )
                logger.info(f"Retrieved existing Chime meeting {meeting_id} for session {session_id}.")

            except self.chime_meetings.exceptions.NotFoundException:
                logger.error(f"Chime meeting {meeting_id} not found for session {session_id}. It might have been ended or deleted.")
                # Clear meeting_id in DynamoDB if it's no longer valid
                self.dynamodb.update_item(
                    TableName=self.sessions_table_name,
                    Key={'session_id': {'S': session_id}},
                    UpdateExpression="REMOVE meeting_id, meeting_region SET #st = :status, updated_at = :ua",
                    ExpressionAttributeNames={'#st': 'status'},
                    ExpressionAttributeValues={
                        ':status': {'S': SessionStatus.ENDED.value}, # Set to ended if meeting not found
                        ':ua': {'S': datetime.now().isoformat()}
                    },
                    ReturnValues="UPDATED_NEW"
                )
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated Chime meeting not found or has ended.")
            except Exception as e:
                logger.error(f"Error fetching Chime meeting {meeting_id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve Chime meeting details.")


        # Create Chime attendee for the user
        try:
            create_attendee_response = self.chime_meetings.create_attendee(
                MeetingId=meeting_id,
                ExternalUserId=f"{join_request.user_type.value}-{join_request.user_id}", # Unique ID for Chime
                Tags=[
                    {'Key': 'UserId', 'Value': join_request.user_id},
                    {'Key': 'UserType', 'Value': join_request.user_type.value},
                    {'Key': 'SessionId', 'Value': session_id}
                ]
            )
            attendee = create_attendee_response['Attendee']
            attendee_info = ChimeAttendeeInfo(
                attendee_id=attendee['AttendeeId'],
                external_user_id=attendee['ExternalUserId'],
                join_token=attendee['JoinToken']
            )
            logger.info(f"Created Chime attendee {attendee['AttendeeId']} for user {join_request.user_id} in meeting {meeting_id}.")

            return JoinSessionResponse(
                session_id=session_id,
                meeting_info=meeting_info,
                attendee_info=attendee_info
            )
        except Exception as e:
            logger.error(f"Error creating Chime attendee for session {session_id} and user {join_request.user_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create Chime attendee.")

    def end_session(self, session_id: str) -> TelemedicineSessionResponse:
        """
        Ends a telemedicine session. Deletes the associated Chime meeting.
        """
        session = self.get_session(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemedicine session not found.")
        if session.status == SessionStatus.ENDED:
            return session # Already ended

        if session.meeting_id:
            try:
                self.chime_meetings.delete_meeting(MeetingId=session.meeting_id)
                logger.info(f"Deleted Chime meeting {session.meeting_id} for session {session_id}.")
            except self.chime_meetings.exceptions.NotFoundException:
                logger.warning(f"Chime meeting {session.meeting_id} for session {session_id} already gone.")
            except Exception as e:
                logger.error(f"Error deleting Chime meeting {session.meeting_id} for session {session_id}: {e}")
                # Log error, but proceed to update DynamoDB as session is conceptually ended

        # Update session status in DynamoDB
        current_time = datetime.now().isoformat()
        try:
            response = self.dynamodb.update_item(
                TableName=self.sessions_table_name,
                Key={'session_id': {'S': session_id}},
                UpdateExpression="SET #st = :status, actual_end_time = :aet, is_recording_active = :ira, updated_at = :ua REMOVE meeting_id, meeting_region",
                ExpressionAttributeNames={'#st': 'status'},
                ExpressionAttributeValues={
                    ':status': {'S': SessionStatus.ENDED.value},
                    ':aet': {'S': current_time},
                    ':ira': {'BOOL': False}, # Ensure recording is marked inactive
                    ':ua': {'S': current_time}
                },
                ReturnValues="ALL_NEW"
            )
            updated_item = response.get('Attributes')
            return self._dynamodb_item_to_session_response(updated_item)
        except Exception as e:
            logger.error(f"Error updating session {session_id} status to ENDED in DynamoDB: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to end telemedicine session: {e}")


    def start_recording(self, session_id: str) -> TelemedicineSessionResponse:
        """
        Starts recording for a given telemedicine session.
        """
        session = self.get_session(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemedicine session not found.")
        if session.status != SessionStatus.IN_PROGRESS or not session.meeting_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is not in progress or no active meeting to record.")
        if session.is_recording_active:
            return session # Already recording

        # Construct S3 key for recording
        recording_s3_key_prefix = f"sessions/{session_id}/"
        # Chime SDK automatically appends a timestamp and file extension (e.g., .mp4, .aac)
        # We'll just store the prefix here, and can list S3 objects later if needed.

        try:
            self.chime_meetings.start_meeting_transcription(
                MeetingId=session.meeting_id,
                ContentIdentificationType='ParticipantIdentification', # For HIPAA/GDPR, consider this or None
                ContentRedactionType='PII', # For HIPAA/GDPR, consider this or None
                RecordingConfiguration={
                    'State': 'Active',
                    'Destination': {
                        'Type': 'S3Bucket',
                        'S3Bucket': self.recording_bucket,
                        'S3Prefix': recording_s3_key_prefix
                    }
                }
            )
            # Update DynamoDB to reflect recording status
            current_time = datetime.now().isoformat()
            response = self.dynamodb.update_item(
                TableName=self.sessions_table_name,
                Key={'session_id': {'S': session_id}},
                UpdateExpression="SET is_recording_active = :ira, recording_s3_key = :rsk, updated_at = :ua",
                ExpressionAttributeValues={
                    ':ira': {'BOOL': True},
                    ':rsk': {'S': recording_s3_key_prefix},
                    ':ua': {'S': current_time}
                },
                ReturnValues="ALL_NEW"
            )
            updated_item = response.get('Attributes')
            logger.info(f"Recording started for session {session_id}. S3 Prefix: {recording_s3_key_prefix}")
            return self._dynamodb_item_to_session_response(updated_item)
        except Exception as e:
            logger.error(f"Error starting recording for session {session_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to start recording: {e}")

    def stop_recording(self, session_id: str) -> TelemedicineSessionResponse:
        """
        Stops recording for a given telemedicine session.
        """
        session = self.get_session(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemedicine session not found.")
        if not session.is_recording_active or not session.meeting_id:
            return session # Not actively recording

        try:
            self.chime_meetings.stop_meeting_transcription(MeetingId=session.meeting_id)
            # Update DynamoDB to reflect recording status
            current_time = datetime.now().isoformat()
            response = self.dynamodb.update_item(
                TableName=self.sessions_table_name,
                Key={'session_id': {'S': session_id}},
                UpdateExpression="SET is_recording_active = :ira, updated_at = :ua",
                ExpressionAttributeValues={
                    ':ira': {'BOOL': False},
                    ':ua': {'S': current_time}
                },
                ReturnValues="ALL_NEW"
            )
            updated_item = response.get('Attributes')
            logger.info(f"Recording stopped for session {session_id}.")
            return self._dynamodb_item_to_session_response(updated_item)
        except Exception as e:
            logger.error(f"Error stopping recording for session {session_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to stop recording: {e}")

# --- FastAPI Application Setup ---

app = FastAPI(
    title="NINC Telemedicine Microservice",
    description="API for managing secure video consultations.",
    version="1.0.0"
)

# Initialize service instance
telemedicine_service = TelemedicineService()

# --- API Endpoints ---

@app.post("/telemedicine/sessions", response_model=TelemedicineSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_new_telemedicine_session(session_data: TelemedicineSessionCreate):
    """
    Schedules a new telemedicine session. Does not start the video call.
    """
    return telemedicine_service.create_session(session_data)

@app.get("/telemedicine/sessions/{session_id}", response_model=TelemedicineSessionResponse)
async def get_single_telemedicine_session(session_id: str):
    """
    Retrieves details of a single telemedicine session.
    """
    session = telemedicine_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemedicine session not found")
    return session

@app.post("/telemedicine/sessions/{session_id}/join", response_model=JoinSessionResponse)
async def join_telemedicine_session(session_id: str, join_request: JoinSessionRequest):
    """
    Allows a user (patient or doctor) to join a telemedicine session.
    Creates an AWS Chime SDK meeting if one doesn't exist and provides attendee details.
    """
    return telemedicine_service.join_session(session_id, join_request)

@app.put("/telemedicine/sessions/{session_id}/end", response_model=TelemedicineSessionResponse)
async def end_telemedicine_session(session_id: str):
    """
    Ends a telemedicine session and deletes the associated AWS Chime SDK meeting.
    """
    return telemedicine_service.end_session(session_id)

@app.put("/telemedicine/sessions/{session_id}/start_recording", response_model=TelemedicineSessionResponse)
async def start_telemedicine_recording(session_id: str):
    """
    Starts recording for an active telemedicine session.
    """
    return telemedicine_service.start_recording(session_id)

@app.put("/telemedicine/sessions/{session_id}/stop_recording", response_model=TelemedicineSessionResponse)
async def stop_telemedicine_recording(session_id: str):
    """
    Stops recording for an active telemedicine session.
    """
    return telemedicine_service.stop_recording(session_id)

@app.get("/telemedicine/sessions/patient/{patient_id}", response_model=List[TelemedicineSessionResponse])
async def get_telemedicine_sessions_by_patient(patient_id: str):
    """
    Retrieves all telemedicine sessions associated with a specific patient.
    """
    return telemedicine_service.get_sessions_by_patient(patient_id)

@app.get("/telemedicine/sessions/doctor/{doctor_id}", response_model=List[TelemedicineSessionResponse])
async def get_telemedicine_sessions_by_doctor(doctor_id: str):
    """
    Retrieves all telemedicine sessions associated with a specific doctor.
    """
    return telemedicine_service.get_sessions_by_doctor(doctor_id)

# --- Example AWS Resource Setup Commands ---
# You would run these AWS CLI commands or use CloudFormation/Terraform to set up your AWS resources.

"""
# 1. Create DynamoDB Table for Telemedicine Sessions
aws dynamodb create-table \
    --table-name NINCTelemedicineSessions \
    --attribute-definitions \
        AttributeName=session_id,AttributeType=S \
        AttributeName=patient_id,AttributeType=S \
        AttributeName=doctor_id,AttributeType=S \
    --key-schema \
        AttributeName=session_id,KeyType=HASH \
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
                "IndexName": "doctor_id-index",
                "KeySchema": [
                    {"AttributeName": "doctor_id", "KeyType": "HASH"}
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

# 2. Create S3 Bucket for Chime SDK Recordings
# Ensure bucket policy allows Chime to write to it. Example bucket policy snippet:
# {
#     "Version": "2012-10-17",
#     "Statement": [
#         {
#             "Sid": "ChimeSDKMeetingRecording",
#             "Effect": "Allow",
#             "Principal": {
#                 "Service": "chime.amazonaws.com"
#             },
#             "Action": "s3:PutObject",
#             "Resource": "arn:aws:s3:::ninc-chime-recordings-your-account-id/*"
#         }
#     ]
# }
aws s3api create-bucket --bucket ninc-chime-recordings-your-account-id --region us-east-1 # Adjust region if needed

# 3. Ensure IAM Role for your FastAPI application (e.g., for ECS Task Role or Lambda Role) has:
#    - DynamoDB permissions: dynamodb:GetItem, dynamodb:PutItem, dynamodb:UpdateItem, dynamodb:Query
#    - AWS Chime SDK Meetings permissions:
#      chime-sdk-meetings:CreateMeeting, chime-sdk-meetings:GetMeeting, chime-sdk-meetings:DeleteMeeting,
#      chime-sdk-meetings:CreateAttendee,
#      chime-sdk-meetings:StartMeetingTranscription, chime-sdk-meetings:StopMeetingTranscription
#    - S3 permissions: if your service directly interacts with S3 for getting recording URLs or managing (beyond Chime itself).
"""

# To run this FastAPI application locally:
# 1. Install dependencies: pip install fastapi uvicorn "python-dotenv[extra]" boto3 pydantic
# 2. Create a .env file with your AWS credentials/endpoints and S3 bucket name:
#    AWS_REGION=us-east-1
#    TELEMEDICINE_SESSIONS_TABLE_NAME=NINCTelemedicineSessions
#    CHIME_RECORDING_BUCKET=ninc-chime-recordings-your-account-id # Replace with your actual bucket name
# 3. Ensure your AWS CLI is configured with credentials that have access to DynamoDB, Chime SDK Meetings, and S3.
# 4. Run the application: uvicorn telemedicine_service:app --reload --port 8005
# 5. Access the API documentation at http://127.0.0.1:8005/docs

#####################################################################################
#Code Description:
#####################################################################################

# This Python code defines a microservice using the FastAPI framework to manage telemedicine sessions.
# It interacts with AWS services, specifically DynamoDB for session data storage and AWS Chime SDK Meetings for video conferencing functionality.

# The code is structured as follows:

# 1. Imports and Configuration
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

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# # --- Configuration ---
# AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
# TELEMEDICINE_SESSIONS_TABLE_NAME = os.getenv("TELEMEDICINE_SESSIONS_TABLE_NAME", "NINCTelemedicineSessions")
# # S3 Bucket for Chime SDK meeting recordings (must be configured to allow Chime to write)
# CHIME_RECORDING_BUCKET = os.getenv("CHIME_RECORDING_BUCKET", "ninc-chime-recordings-your-account-id")
# Use code with caution
# This section imports necessary libraries:

# fastapi for building the web API.
# pydantic for data validation and serialization.
# boto3 for interacting with AWS services.
# os for accessing environment variables.
# uuid for generating unique identifiers.
# json (though not explicitly used in the provided snippet, it's imported).
# logging for recording events and errors.
# datetime and timedelta for handling time and dates.
# typing for type hints.
# enum for defining enumerations.
# It then configures basic logging to output information, warnings, and errors.

# Finally, it defines configuration variables for the AWS region, the name of the DynamoDB table for sessions, and the S3 bucket name for Chime recordings. These values are retrieved from environment variables, with default values provided.

# 2. Enumerations
# # --- Enums ---
# class SessionStatus(str, Enum):
#     SCHEDULED = "scheduled"
#     IN_PROGRESS = "in_progress"
#     ENDED = "ended"
#     CANCELLED = "cancelled"

# class UserType(str, Enum):
#     PATIENT = "patient"
#     DOCTOR = "doctor"
#     ADMIN = "admin"
# Use code with caution
# These blocks define two Enum classes:

# SessionStatus: Represents the possible states of a telemedicine session (scheduled, in_progress, ended, cancelled). Using an Enum provides clarity and prevents typos when referring to session statuses.
# UserType: Represents the types of users who can participate in a session (patient, doctor, admin).
# 3. Pydantic Models
# # --- Pydantic Models for Data Validation and Serialization ---

# class TelemedicineSessionCreate(BaseModel):
#     """
#     Model for creating a new telemedicine session.
#     """
#     patient_id: str
#     doctor_id: str
#     scheduled_start_time: datetime = Field(..., description="Scheduled start time of the session (ISO 8601 format).")
#     scheduled_end_time: datetime = Field(..., description="Scheduled end time of the session (ISO 8601 format).")
#     description: Optional[str] = None
#     # Potentially link to an appointment_id from the Booking Service

# class TelemedicineSessionResponse(BaseModel):
#     """
#     Model for returning telemedicine session details.
#     """
#     session_id: str
#     patient_id: str
#     doctor_id: str
#     scheduled_start_time: datetime
#     scheduled_end_time: datetime
#     actual_start_time: Optional[datetime] = None
#     actual_end_time: Optional[datetime] = None
#     status: SessionStatus
#     description: Optional[str] = None
#     meeting_id: Optional[str] = Field(None, description="AWS Chime SDK Meeting ID.")
#     meeting_region: Optional[str] = Field(None, description="AWS Chime SDK Meeting Region.")
#     recording_s3_key: Optional[str] = Field(None, description="S3 key for the recorded session file.")
#     is_recording_active: bool = False
#     created_at: datetime
#     updated_at: datetime

# class JoinSessionRequest(BaseModel):
#     """
#     Model for a user requesting to join a telemedicine session.
#     """
#     user_id: str = Field(..., description="The ID of the user joining (patient_id or doctor_id).")
#     user_type: UserType = Field(..., description="The type of user joining (patient, doctor, admin).")
#     user_name: str = Field(..., description="Display name for the user in the Chime meeting.")

# class ChimeMeetingInfo(BaseModel):
#     """
#     Details about the Chime meeting to pass to the frontend.
#     """
#     meeting_id: str
#     external_meeting_id: str
#     media_region: str
#     media_placement: Dict[str, str]

# class ChimeAttendeeInfo(BaseModel):
#     """
#     Details about the Chime attendee to pass to the frontend.
#     """
#     attendee_id: str
#     external_user_id: str
#     join_token: str

# class JoinSessionResponse(BaseModel):
#     """
#     Response model for joining a session, containing Chime details.
#     """
#     session_id: str
#     meeting_info: ChimeMeetingInfo
#     attendee_info: ChimeAttendeeInfo
# Use code with caution
# Pydantic BaseModel classes are used to define the structure and data types for requests and responses. This provides automatic data validation and serialization/deserialization.

# TelemedicineSessionCreate: Defines the required data to create a new session (patient ID, doctor ID, scheduled times, and optional description).
# TelemedicineSessionResponse: Defines the structure of the data returned when retrieving session details. It includes session metadata, status, timestamps, and details about the associated Chime meeting and recording.
# JoinSessionRequest: Defines the data required when a user requests to join a session (user ID, user type, and display name).
# ChimeMeetingInfo and ChimeAttendeeInfo: Define the structure of the AWS Chime SDK meeting and attendee details returned to the frontend.
# JoinSessionResponse: Combines session ID with the Chime meeting and attendee information for the join response.
# 4. AWS Service Clients
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

# def get_chime_sdk_meetings_client():
#     """
#     Initializes and returns an AWS Chime SDK Meetings client.
#     """
#     try:
#         return boto3.client('chime-sdk-meetings', region_name=AWS_REGION)
#     except Exception as e:
#         logger.error(f"Error initializing Chime SDK Meetings client: {e}")
#         raise
# Use code with caution
# These functions are responsible for creating and returning initialized clients for interacting with AWS services using boto3.

# get_dynamodb_client(): Creates and returns a client for AWS DynamoDB. It uses the configured AWS_REGION. Includes error handling for initialization issues.
# get_chime_sdk_meetings_client(): Creates and returns a client for the AWS Chime SDK Meetings service. It also uses the configured AWS_REGION and includes error handling.
# 5. TelemedicineService Class
# # --- Service Class for Data Operations ---

# class TelemedicineService:
#     """
#     Handles operations related to telemedicine sessions, interacting with DynamoDB and AWS Chime SDK.
#     """
#     def __init__(self):
#         self.dynamodb = get_dynamodb_client()
#         self.chime_meetings = get_chime_sdk_meetings_client()
#         self.sessions_table_name = TELEMEDICINE_SESSIONS_TABLE_NAME
#         self.recording_bucket = CHIME_RECORDING_BUCKET

#     def _dynamodb_item_to_session_response(self, item: Dict[str, Any]) -> TelemedicineSessionResponse:
#         """
#         Converts a DynamoDB item dictionary to a TelemedicineSessionResponse Pydantic model.
#         """
#         try:
#             return TelemedicineSessionResponse(
#                 session_id=item['session_id']['S'],
#                 patient_id=item['patient_id']['S'],
#                 doctor_id=item['doctor_id']['S'],
#                 scheduled_start_time=datetime.fromisoformat(item['scheduled_start_time']['S']),
#                 scheduled_end_time=datetime.fromisoformat(item['scheduled_end_time']['S']),
#                 actual_start_time=datetime.fromisoformat(item['actual_start_time']['S']) if 'actual_start_time' in item else None,
#                 actual_end_time=datetime.fromisoformat(item['actual_end_time']['S']) if 'actual_end_time' in item else None,
#                 status=SessionStatus(item['status']['S']),
#                 description=item.get('description', {}).get('S'),
#                 meeting_id=item.get('meeting_id', {}).get('S'),
#                 meeting_region=item.get('meeting_region', {}).get('S'),
#                 recording_s3_key=item.get('recording_s3_key', {}).get('S'),
#                 is_recording_active=item.get('is_recording_active', {}).get('BOOL', False),
#                 created_at=datetime.fromisoformat(item['created_at']['S']),
#                 updated_at=datetime.fromisoformat(item['updated_at']['S'])
#             )
#         except KeyError as e:
#             logger.error(f"Missing key in DynamoDB item for Telemedicine Session: {e}. Item: {item}")
#             raise ValueError(f"Invalid DynamoDB item format for Telemedicine Session: {e}")
#         except Exception as e:
#             logger.error(f"Error converting DynamoDB item to TelemedicineSessionResponse: {e}. Item: {item}")
#             raise

#     def create_session(self, session_data: TelemedicineSessionCreate) -> TelemedicineSessionResponse:
#         """
#         Creates a new telemedicine session record. Does NOT create a Chime meeting yet.
#         """
#         session_id = str(uuid.uuid4())
#         current_time = datetime.now()

#         item = {
#             'session_id': {'S': session_id},
#             'patient_id': {'S': session_data.patient_id},
#             'doctor_id': {'S': session_data.doctor_id},
#             'scheduled_start_time': {'S': session_data.scheduled_start_time.isoformat()},
#             'scheduled_end_time': {'S': session_data.scheduled_end_time.isoformat()},
#             'status': {'S': SessionStatus.SCHEDULED.value},
#             'description': {'S': session_data.description} if session_data.description else {'NULL': True},
#             'is_recording_active': {'BOOL': False}, # Default to not recording
#             'created_at': {'S': current_time.isoformat()},
#             'updated_at': {'S': current_time.isoformat()}
#         }

#         try:
#             self.dynamodb.put_item(
#                 TableName=self.sessions_table_name,
#                 Item=item,
#                 ConditionExpression="attribute_not_exists(session_id)"
#             )
#             created_session = self._dynamodb_item_to_session_response(item)
#             logger.info(f"Telemedicine session {session_id} scheduled for patient {session_data.patient_id} and doctor {session_data.doctor_id}.")
#             return created_session
#         except self.dynamodb.exceptions.ConditionalCheckFailedException:
#             logger.error(f"Session ID {session_id} already exists.")
#             raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session ID conflict.")
#         except Exception as e:
#             logger.error(f"Error creating telemedicine session: {e}")
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create telemedicine session: {e}")

#     def get_session(self, session_id: str) -> Optional[TelemedicineSessionResponse]:
#         """
#         Retrieves a single telemedicine session by its ID.
#         """
#         try:
#             response = self.dynamodb.get_item(
#                 TableName=self.sessions_table_name,
#                 Key={'session_id': {'S': session_id}}
#             )
#             item = response.get('Item')
#             if item:
#                 return self._dynamodb_item_to_session_response(item)
#             return None
#         except Exception as e:
#             logger.error(f"Error getting telemedicine session {session_id}: {e}")
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve telemedicine session: {e}")

#     def get_sessions_by_patient(self, patient_id: str) -> List[TelemedicineSessionResponse]:
#         """
#         Retrieves all telemedicine sessions for a given patient. Requires a GSI on patient_id.
#         """
#         try:
#             response = self.dynamodb.query(
#                 TableName=self.sessions_table_name,
#                 IndexName='patient_id-index', # Ensure this GSI exists
#                 KeyConditionExpression='patient_id = :patient_id',
#                 ExpressionAttributeValues={':patient_id': {'S': patient_id}}
#             )
#             sessions = [self._dynamodb_item_to_session_response(item) for item in response.get('Items', [])]
#             logger.info(f"Retrieved {len(sessions)} sessions for patient {patient_id}.")
#             return sessions
#         except Exception as e:
#             logger.error(f"Error getting sessions for patient {patient_id}: {e}")
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve patient sessions: {e}")

#     def get_sessions_by_doctor(self, doctor_id: str) -> List[TelemedicineSessionResponse]:
#         """
#         Retrieves all telemedicine sessions for a given doctor. Requires a GSI on doctor_id.
#         """
#         try:
#             response = self.dynamodb.query(
#                 TableName=self.sessions_table_name,
#                 IndexName='doctor_id-index', # Ensure this GSI exists
#                 KeyConditionExpression='doctor_id = :doctor_id',
#                 ExpressionAttributeValues={':doctor_id': {'S': doctor_id}}
#             )
#             sessions = [self._dynamodb_item_to_session_response(item) for item in response.get('Items', [])]
#             logger.info(f"Retrieved {len(sessions)} sessions for doctor {doctor_id}.")
#             return sessions
#         except Exception as e:
#             logger.error(f"Error getting sessions for doctor {doctor_id}: {e}")
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve doctor sessions: {e}")

#     def join_session(self, session_id: str, join_request: JoinSessionRequest) -> JoinSessionResponse:
#         """
#         Allows a user to join a telemedicine session.
#         If no Chime meeting exists for the session, it creates one.
#         Generates an attendee token for the user.
#         """
#         session = self.get_session(session_id)
#         if not session:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemedicine session not found.")

#         # Basic authorization check: ensure the joining user is the patient or doctor for the session
#         # In a real app, this would be integrated with a robust auth system
#         if join_request.user_type == UserType.PATIENT and join_request.user_id != session.patient_id:
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to join this session as patient.")
#         if join_request.user_type == UserType.DOCTOR and join_request.user_id != session.doctor_id:
#             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to join this session as doctor.")

#         meeting_id = session.meeting_id
#         meeting_info = None

#         # If meeting_id doesn't exist, create a new Chime meeting
#         if not meeting_id:
#             try:
#                 # ExternalMeetingId helps link Chime meeting to our internal session_id
#                 create_meeting_response = self.chime_meetings.create_meeting(
#                     ClientRequestToken=str(uuid.uuid4()), # Unique token for idempotency
#                     ExternalMeetingId=session_id,
#                     MediaRegion=AWS_REGION, # Use the same region for Chime as the service
#                     Tags=[
#                         {'Key': 'NINCSessionId', 'Value': session_id},
#                         {'Key': 'PatientId', 'Value': session.patient_id},
#                         {'Key': 'DoctorId', 'Value': session.doctor_id}
#                     ]
#                 )
#                 meeting = create_meeting_response['Meeting']
#                 meeting_id = meeting['MeetingId']
#                 meeting_info = ChimeMeetingInfo(
#                     meeting_id=meeting['MeetingId'],
#                     external_meeting_id=meeting['ExternalMeetingId'],
#                     media_region=meeting['MediaRegion'],
#                     media_placement=meeting['MediaPlacement']
#                 )

#                 # Update session in DynamoDB with Chime meeting details
#                 self.dynamodb.update_item(
#                     TableName=self.sessions_table_name,
#                     Key={'session_id': {'S': session_id}},
#                     UpdateExpression="SET meeting_id = :mid, meeting_region = :mregion, #st = :status, actual_start_time = :ast, updated_at = :ua",
#                     ExpressionAttributeNames={'#st': 'status'},
#                     ExpressionAttributeValues={
#                         ':mid': {'S': meeting_id},
#                         ':mregion': {'S': AWS_REGION},
#                         ':status': {'S': SessionStatus.IN_PROGRESS.value},
#                         ':ast': {'S': datetime.now().isoformat()},
#                         ':ua': {'S': datetime.now().isoformat()}
#                     },
#                     ReturnValues="UPDATED_NEW"
#                 )
#                 logger.info(f"Created new Chime meeting {meeting_id} for session {session_id}.")

#             except Exception as e:
#                 logger.error(f"Error creating Chime meeting for session {session_id}: {e}")
#                 raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create Chime meeting.")
#         else:
#             # If meeting_id exists, fetch existing meeting info
#             try:
#                 get_meeting_response = self.chime_meetings.get_meeting(MeetingId=meeting_id)
#                 meeting = get_meeting_response['Meeting']
#                 meeting_info = ChimeMeetingInfo(
#                     meeting_id=meeting['MeetingId'],
#                     external_meeting_id=meeting['ExternalMeetingId'],
#                     media_region=meeting['MediaRegion'],
#                     media_placement=meeting['MediaPlacement']
#                 )
#                 # Ensure status is 'in_progress'
#                 if session.status == SessionStatus.SCHEDULED:
#                      self.dynamodb.update_item(
#                         TableName=self.sessions_table_name,
#                         Key={'session_id': {'S': session_id}},
#                         UpdateExpression="SET #st = :status, actual_start_time = :ast, updated_at = :ua",
#                         ExpressionAttributeNames={'#st': 'status'},
#                         ExpressionAttributeValues={
#                             ':status': {'S': SessionStatus.IN_PROGRESS.value},
#                             ':ast': {'S': datetime.now().isoformat()},
#                             ':ua': {'S': datetime.now().isoformat()}
#                         },
#                         ReturnValues="UPDATED_NEW"
#                     )
#                 logger.info(f"Retrieved existing Chime meeting {meeting_id} for session {session_id}.")

#             except self.chime_meetings.exceptions.NotFoundException:
#                 logger.error(f"Chime meeting {meeting_id} not found for session {session_id}. It might have been ended or deleted.")
#                 # Clear meeting_id in DynamoDB if it's no longer valid
#                 self.dynamodb.update_item(
#                     TableName=self.sessions_table_name,
#                     Key={'session_id': {'S': session_id}},
#                     UpdateExpression="REMOVE meeting_id, meeting_region SET #st = :status, updated_at = :ua",
#                     ExpressionAttributeNames={'#st': 'status'},
#                     ExpressionAttributeValues={
#                         ':status': {'S': SessionStatus.ENDED.value}, # Set to ended if meeting not found
#                         ':ua': {'S': datetime.now().isoformat()}
#                     },
#                     ReturnValues="UPDATED_NEW"
#                 )
#                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated Chime meeting not found or has ended.")
#             except Exception as e:
#                 logger.error(f"Error fetching Chime meeting {meeting_id}: {e}")
#                 raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve Chime meeting details.")


#         # Create Chime attendee for the user
#         try:
#             create_attendee_response = self.chime_meetings.create_attendee(
#                 MeetingId=meeting_id,
#                 ExternalUserId=f"{join_request.user_type.value}-{join_request.user_id}", # Unique ID for Chime
#                 Tags=[
#                     {'Key': 'UserId', 'Value': join_request.user_id},
#                     {'Key': 'UserType', 'Value': join_request.user_type.value},
#                     {'Key': 'SessionId', 'Value': session_id}
#                 ]
#             )
#             attendee = create_attendee_response['Attendee']
#             attendee_info = ChimeAttendeeInfo(
#                 attendee_id=attendee['AttendeeId'],
#                 external_user_id=attendee['ExternalUserId'],
#                 join_token=attendee['JoinToken']
#             )
#             logger.info(f"Created Chime attendee {attendee['AttendeeId']} for user {join_request.user_id} in meeting {meeting_id}.")

#             return JoinSessionResponse(
#                 session_id=session_id,
#                 meeting_info=meeting_info,
#                 attendee_info=attendee_info
#             )
#         except Exception as e:
#             logger.error(f"Error creating Chime attendee for session {session_id} and user {join_request.user_id}: {e}")
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create Chime attendee.")

#     def end_session(self, session_id: str) -> TelemedicineSessionResponse:
#         """
#         Ends a telemedicine session. Deletes the associated Chime meeting.
#         """
#         session = self.get_session(session_id)
#         if not session:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemedicine session not found.")
#         if session.status == SessionStatus.ENDED:
#             return session # Already ended

#         if session.meeting_id:
#             try:
#                 self.chime_meetings.delete_meeting(MeetingId=session.meeting_id)
#                 logger.info(f"Deleted Chime meeting {session.meeting_id} for session {session_id}.")
#             except self.chime_meetings.exceptions.NotFoundException:
#                 logger.warning(f"Chime meeting {session.meeting_id} for session {session_id} already gone.")
#             except Exception as e:
#                 logger.error(f"Error deleting Chime meeting {session.meeting_id} for session {session_id}: {e}")
#                 # Log error, but proceed to update DynamoDB as session is conceptually ended

#         # Update session status in DynamoDB
#         current_time = datetime.now().isoformat()
#         try:
#             response = self.dynamodb.update_item(
#                 TableName=self.sessions_table_name,
#                 Key={'session_id': {'S': session_id}},
#                 UpdateExpression="SET #st = :status, actual_end_time = :aet, is_recording_active = :ira, updated_at = :ua REMOVE meeting_id, meeting_region",
#                 ExpressionAttributeNames={'#st': 'status'},
#                 ExpressionAttributeValues={
#                     ':status': {'S': SessionStatus.ENDED.value},
#                     ':aet': {'S': current_time},
#                     ':ira': {'BOOL': False}, # Ensure recording is marked inactive
#                     ':ua': {'S': current_time}
#                 },
#                 ReturnValues="ALL_NEW"
#             )
#             updated_item = response.get('Attributes')
#             return self._dynamodb_item_to_session_response(updated_item)
#         except Exception as e:
#             logger.error(f"Error updating session {session_id} status to ENDED in DynamoDB: {e}")
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to end telemedicine session: {e}")


#     def start_recording(self, session_id: str) -> TelemedicineSessionResponse:
#         """
#         Starts recording for a given telemedicine session.
#         """
#         session = self.get_session(session_id)
#         if not session:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemedicine session not found.")
#         if session.status != SessionStatus.IN_PROGRESS or not session.meeting_id:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is not in progress or no active meeting to record.")
#         if session.is_recording_active:
#             return session # Already recording

#         # Construct S3 key for recording
#         recording_s3_key_prefix = f"sessions/{session_id}/"
#         # Chime SDK automatically appends a timestamp and file extension (e.g., .mp4, .aac)
#         # We'll just store the prefix here, and can list S3 objects later if needed.

#         try:
#             self.chime_meetings.start_meeting_transcription(
#                 MeetingId=session.meeting_id,
#                 ContentIdentificationType='ParticipantIdentification', # For HIPAA/GDPR, consider this or None
#                 ContentRedactionType='PII', # For HIPAA/GDPR, consider this or None
#                 RecordingConfiguration={
#                     'State': 'Active',
#                     'Destination': {
#                         'Type': 'S3Bucket',
#                         'S3Bucket': self.recording_bucket,
#                         'S3Prefix': recording_s3_key_prefix
#                     }
#                 }
#             )
#             # Update DynamoDB to reflect recording status
#             current_time = datetime.now().isoformat()
#             response = self.dynamodb.update_item(
#                 TableName=self.sessions_table_name,
#                 Key={'session_id': {'S': session_id}},
#                 UpdateExpression="SET is_recording_active = :ira, recording_s3_key = :rsk, updated_at = :ua",
#                 ExpressionAttributeValues={
#                     ':ira': {'BOOL': True},
#                     ':rsk': {'S': recording_s3_key_prefix},
#                     ':ua': {'S': current_time}
#                 },
#                 ReturnValues="ALL_NEW"
#             )
#             updated_item = response.get('Attributes')
#             logger.info(f"Recording started for session {session_id}. S3 Prefix: {recording_s3_key_prefix}")
#             return self._dynamodb_item_to_session_response(updated_item)
#         except Exception as e:
#             logger.error(f"Error starting recording for session {session_id}: {e}")
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to start recording: {e}")

#     def stop_recording(self, session_id: str) -> TelemedicineSessionResponse:
#         """
#         Stops recording for a given telemedicine session.
#         """
#         session = self.get_session(session_id)
#         if not session:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemedicine session not found.")
#         if not session.is_recording_active or not session.meeting_id:
#             return session # Not actively recording

#         try:
#             self.chime_meetings.stop_meeting_transcription(MeetingId=session.meeting_id)
#             # Update DynamoDB to reflect recording status
#             current_time = datetime.now().isoformat()
#             response = self.dynamodb.update_item(
#                 TableName=self.sessions_table_name,
#                 Key={'session_id': {'S': session_id}},
#                 UpdateExpression="SET is_recording_active = :ira, updated_at = :ua",
#                 ExpressionAttributeValues={
#                     ':ira': {'BOOL': False},
#                     ':ua': {'S': current_time}
#                 },
#                 ReturnValues="ALL_NEW"
#             )
#             updated_item = response.get('Attributes')
#             logger.info(f"Recording stopped for session {session_id}.")
#             return self._dynamodb_item_to_session_response(updated_item)
#         except Exception as e:
#             logger.error(f"Error stopping recording for session {session_id}: {e}")
#             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to stop recording: {e}")
# Use code with caution
# The TelemedicineService class encapsulates the core logic for managing telemedicine sessions.

# The __init__ method initializes the DynamoDB and Chime SDK Meetings clients and stores the table and bucket names.
# _dynamodb_item_to_session_response: A helper method to convert the data format returned by DynamoDB into the TelemedicineSessionResponse Pydantic model. This handles data type conversions and checks for missing keys.
# create_session: Creates a new session record in DynamoDB with a unique session ID, scheduled times, patient and doctor IDs, and initial status. It uses a conditional write to ensure the session ID doesn't already exist.
# get_session: Retrieves a single session from DynamoDB based on its session_id.
# get_sessions_by_patient: Queries DynamoDB to find all sessions associated with a specific patient_id. This requires a Global Secondary Index (GSI) on the patient_id attribute in the DynamoDB table.
# get_sessions_by_doctor: Similar to the patient function, this queries DynamoDB for sessions associated with a specific doctor_id, requiring a GSI on doctor_id.
# join_session: This is a key function that allows a user to join a session. It first retrieves the session details. If no Chime meeting is currently associated with the session, it creates a new one using the Chime SDK Meetings API, updates the session record in DynamoDB with the meeting details, and sets the session status to in_progress. If a meeting already exists, it retrieves its details. It then creates a Chime attendee for the joining user and returns the necessary meeting and attendee information to the client (frontend application). It includes basic authorization checks to ensure the joining user is either the patient or doctor for the session.
# end_session: Ends a telemedicine session by deleting the associated Chime meeting and updating the session status in DynamoDB to ended. It also records the actual end time.
# start_recording: Initiates recording for an active telemedicine session using the Chime SDK Meetings API. It specifies the S3 bucket and a prefix for storing the recording and updates the session record in DynamoDB to mark recording as active.
# stop_recording: Stops the recording for an active session using the Chime SDK Meetings API and updates the session record in DynamoDB to mark recording as inactive.
# 6. FastAPI Application Setup
# # --- FastAPI Application Setup ---

# app = FastAPI(
#     title="NINC Telemedicine Microservice",
#     description="API for managing secure video consultations.",
#     version="1.0.0"
# )

# # Initialize service instance
# telemedicine_service = TelemedicineService()
# Use code with caution
# This section initializes the FastAPI application instance.

# FastAPI() creates the application, providing a title, description, and version, which are used to generate the automatic API documentation (Swagger UI).
# telemedicine_service = TelemedicineService() creates an instance of the TelemedicineService class, making it available for use by the API endpoints.
# 7. API Endpoints
# # --- API Endpoints ---

# @app.post("/telemedicine/sessions", response_model=TelemedicineSessionResponse, status_code=status.HTTP_201_CREATED)
# async def create_new_telemedicine_session(session_data: TelemedicineSessionCreate):
#     """
#     Schedules a new telemedicine session. Does not start the video call.
#     """
#     return telemedicine_service.create_session(session_data)

# @app.get("/telemedicine/sessions/{session_id}", response_model=TelemedicineSessionResponse)
# async def get_single_telemedicine_session(session_id: str):
#     """
#     Retrieves details of a single telemedicine session.
#     """
#     session = telemedicine_service.get_session(session_id)
#     if not session:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Telemedicine session not found")
#     return session

# @app.post("/telemedicine/sessions/{session_id}/join", response_model=JoinSessionResponse)
# async def join_telemedicine_session(session_id: str, join_request: JoinSessionRequest):
#     """
#     Allows a user (patient or doctor) to join a telemedicine session.
#     Creates an AWS Chime SDK meeting if one doesn't exist and provides attendee details.
#     """
#     return telemedicine_service.join_session(session_id, join_request)

# @app.put("/telemedicine/sessions/{session_id}/end", response_model=TelemedicineSessionResponse)
# async def end_telemedicine_session(session_id: str):
#     """
#     Ends a telemedicine session and deletes the associated AWS Chime SDK meeting.
#     """
#     return telemedicine_service.end_session(session_id)

# @app.put("/telemedicine/sessions/{session_id}/start_recording", response_model=TelemedicineSessionResponse)
# async def start_telemedicine_recording(session_id: str):
#     """
