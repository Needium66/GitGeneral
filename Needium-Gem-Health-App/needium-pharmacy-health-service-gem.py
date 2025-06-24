##################################################################
#Develop Python code for the NINC Pharmacy microservice. 
#This Canvas provides the architecture for managing prescriptions, ordering them, and tracking their status
#Leveraging AWS DynamoDB for data persistence and AWS SQS for asynchronous communication with external pharmacy systems
#######################################################################################################################
#The Code:
#######################################################################################################################

# pharmacy_service.py

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import boto3
import os
import uuid
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
PRESCRIPTIONS_TABLE_NAME = os.getenv("PRESCRIPTIONS_TABLE_NAME", "NINCPrescriptions")
PHARMACY_ORDERS_TABLE_NAME = os.getenv("PHARMACY_ORDERS_TABLE_NAME", "NINCPharmacyOrders")

# SQS Queue for sending orders to external pharmacy systems
SQS_PHARMACY_ORDER_QUEUE_URL = os.getenv("SQS_PHARMACY_ORDER_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456789012/NINCPharmacyOrderQueue")
# SNS Topic for notifications (e.g., prescription ready, shipped)
SNS_PHARMACY_NOTIFICATIONS_TOPIC_ARN = os.getenv("SNS_PHARMACY_NOTIFICATIONS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:NINCPharmacyNotifications")

# --- Enums ---
class PrescriptionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY_FOR_PICKUP = "ready_for_pickup"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"

class DeliveryMethod(str, Enum):
    PICKUP = "pickup"
    DELIVERY = "delivery"

# --- Pydantic Models for Data Validation and Serialization ---

class PrescriptionDrug(BaseModel):
    """
    Represents a single drug within a prescription.
    """
    drug_name: str
    dosage: str
    quantity: str
    instructions: str
    refills_remaining: int = Field(ge=0)

class PrescriptionCreate(BaseModel):
    """
    Model for creating a new prescription. This would typically be
    created by a doctor or integrated from an EHR system.
    """
    patient_id: str
    doctor_id: str
    prescription_date: datetime
    expiry_date: datetime
    drugs: List[PrescriptionDrug]
    notes: Optional[str] = None

class PrescriptionResponse(PrescriptionCreate):
    """
    Model for returning prescription details, including its ID.
    """
    prescription_id: str
    status: PrescriptionStatus = PrescriptionStatus.ACTIVE
    created_at: datetime
    updated_at: datetime

class PharmacyOrderCreate(BaseModel):
    """
    Model for a patient placing an order for a prescription.
    """
    patient_id: str
    prescription_id: str
    pharmacy_id: str = Field(..., description="ID of the pharmacy chosen by the patient.")
    delivery_method: DeliveryMethod
    delivery_address: Optional[Dict[str, str]] = None # Required if delivery_method is DELIVERY
    # Could include payment_transaction_id if payment is pre-authorized/linked

class PharmacyOrderResponse(PharmacyOrderCreate):
    """
    Model for returning pharmacy order details.
    """
    order_id: str
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime
    updated_at: datetime
    # Add tracking information later

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

def get_sqs_client():
    """
    Initializes and returns an SQS client.
    """
    try:
        return boto3.client('sqs', region_name=AWS_REGION)
    except Exception as e:
        logger.error(f"Error initializing SQS client: {e}")
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

class PharmacyService:
    """
    Handles operations related to prescriptions and pharmacy orders.
    Uses DynamoDB for storage, SQS for asynchronous order processing, and SNS for notifications.
    """
    def __init__(self):
        self.dynamodb = get_dynamodb_client()
        self.sqs = get_sqs_client()
        self.sns = get_sns_client()
        self.prescriptions_table = PRESCRIPTIONS_TABLE_NAME
        self.orders_table = PHARMACY_ORDERS_TABLE_NAME
        self.sqs_queue_url = SQS_PHARMACY_ORDER_QUEUE_URL
        self.sns_topic_arn = SNS_PHARMACY_NOTIFICATIONS_TOPIC_ARN

    def _dynamodb_item_to_prescription_response(self, item: Dict[str, Any]) -> PrescriptionResponse:
        """
        Converts a DynamoDB item dictionary to a PrescriptionResponse Pydantic model.
        """
        try:
            return PrescriptionResponse(
                prescription_id=item['prescription_id']['S'],
                patient_id=item['patient_id']['S'],
                doctor_id=item['doctor_id']['S'],
                prescription_date=datetime.fromisoformat(item['prescription_date']['S']),
                expiry_date=datetime.fromisoformat(item['expiry_date']['S']),
                drugs=json.loads(item['drugs']['S']), # Stored as JSON string
                notes=item.get('notes', {}).get('S'),
                status=PrescriptionStatus(item['status']['S']),
                created_at=datetime.fromisoformat(item['created_at']['S']),
                updated_at=datetime.fromisoformat(item['updated_at']['S'])
            )
        except KeyError as e:
            logger.error(f"Missing key in DynamoDB item for Prescription: {e}. Item: {item}")
            raise ValueError(f"Invalid DynamoDB item format for Prescription: {e}")
        except Exception as e:
            logger.error(f"Error converting DynamoDB item to PrescriptionResponse: {e}. Item: {item}")
            raise

    def _dynamodb_item_to_pharmacy_order_response(self, item: Dict[str, Any]) -> PharmacyOrderResponse:
        """
        Converts a DynamoDB item dictionary to a PharmacyOrderResponse Pydantic model.
        """
        try:
            return PharmacyOrderResponse(
                order_id=item['order_id']['S'],
                patient_id=item['patient_id']['S'],
                prescription_id=item['prescription_id']['S'],
                pharmacy_id=item['pharmacy_id']['S'],
                delivery_method=DeliveryMethod(item['delivery_method']['S']),
                delivery_address=json.loads(item['delivery_address']['S']) if 'delivery_address' in item else None,
                status=OrderStatus(item['status']['S']),
                created_at=datetime.fromisoformat(item['created_at']['S']),
                updated_at=datetime.fromisoformat(item['updated_at']['S'])
            )
        except KeyError as e:
            logger.error(f"Missing key in DynamoDB item for PharmacyOrder: {e}. Item: {item}")
            raise ValueError(f"Invalid DynamoDB item format for PharmacyOrder: {e}")
        except Exception as e:
            logger.error(f"Error converting DynamoDB item to PharmacyOrderResponse: {e}. Item: {item}")
            raise

    def create_prescription(self, prescription_data: PrescriptionCreate) -> PrescriptionResponse:
        """
        Creates a new prescription record in DynamoDB.
        """
        prescription_id = str(uuid.uuid4())
        current_time = datetime.now()

        item = {
            'prescription_id': {'S': prescription_id},
            'patient_id': {'S': prescription_data.patient_id},
            'doctor_id': {'S': prescription_data.doctor_id},
            'prescription_date': {'S': prescription_data.prescription_date.isoformat()},
            'expiry_date': {'S': prescription_data.expiry_date.isoformat()},
            'drugs': {'S': json.dumps([d.dict() for d in prescription_data.drugs])}, # Store list of drugs as JSON string
            'notes': {'S': prescription_data.notes} if prescription_data.notes else {'NULL': True},
            'status': {'S': PrescriptionStatus.ACTIVE.value},
            'created_at': {'S': current_time.isoformat()},
            'updated_at': {'S': current_time.isoformat()}
        }

        try:
            self.dynamodb.put_item(
                TableName=self.prescriptions_table,
                Item=item,
                ConditionExpression="attribute_not_exists(prescription_id)"
            )
            created_prescription = self._dynamodb_item_to_prescription_response(item)
            logger.info(f"Prescription {prescription_id} created for patient {prescription_data.patient_id}.")
            return created_prescription
        except self.dynamodb.exceptions.ConditionalCheckFailedException:
            logger.error(f"Prescription ID {prescription_id} already exists.")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Prescription ID conflict.")
        except Exception as e:
            logger.error(f"Error creating prescription: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create prescription: {e}")

    def get_prescription(self, prescription_id: str) -> Optional[PrescriptionResponse]:
        """
        Retrieves a single prescription by its ID.
        """
        try:
            response = self.dynamodb.get_item(
                TableName=self.prescriptions_table,
                Key={'prescription_id': {'S': prescription_id}}
            )
            item = response.get('Item')
            if item:
                return self._dynamodb_item_to_prescription_response(item)
            return None
        except Exception as e:
            logger.error(f"Error getting prescription {prescription_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve prescription: {e}")

    def get_prescriptions_by_patient(self, patient_id: str) -> List[PrescriptionResponse]:
        """
        Retrieves all prescriptions for a given patient. Requires a GSI on patient_id.
        """
        try:
            response = self.dynamodb.query(
                TableName=self.prescriptions_table,
                IndexName='patient_id-index', # Ensure this GSI exists
                KeyConditionExpression='patient_id = :patient_id',
                ExpressionAttributeValues={':patient_id': {'S': patient_id}}
            )
            prescriptions = [self._dynamodb_item_to_prescription_response(item) for item in response.get('Items', [])]
            logger.info(f"Retrieved {len(prescriptions)} prescriptions for patient {patient_id}.")
            return prescriptions
        except Exception as e:
            logger.error(f"Error getting prescriptions for patient {patient_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve patient prescriptions: {e}")

    def place_pharmacy_order(self, order_data: PharmacyOrderCreate) -> PharmacyOrderResponse:
        """
        Places a new pharmacy order. Records the order and sends a message to SQS
        for asynchronous processing by a pharmacy integration service.
        """
        order_id = str(uuid.uuid4())
        current_time = datetime.now()

        # Validate prescription existence and status before ordering
        prescription = self.get_prescription(order_data.prescription_id)
        if not prescription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found.")
        if prescription.status != PrescriptionStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Prescription is not active and cannot be ordered.")
        # Further checks: is the prescription expired? Are there refills remaining?

        item = {
            'order_id': {'S': order_id},
            'patient_id': {'S': order_data.patient_id},
            'prescription_id': {'S': order_data.prescription_id},
            'pharmacy_id': {'S': order_data.pharmacy_id},
            'delivery_method': {'S': order_data.delivery_method.value},
            'status': {'S': OrderStatus.PENDING.value},
            'created_at': {'S': current_time.isoformat()},
            'updated_at': {'S': current_time.isoformat()}
        }
        if order_data.delivery_method == DeliveryMethod.DELIVERY and order_data.delivery_address:
            item['delivery_address'] = {'S': json.dumps(order_data.delivery_address)}
        elif order_data.delivery_method == DeliveryMethod.DELIVERY and not order_data.delivery_address:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Delivery address is required for delivery method.")


        try:
            self.dynamodb.put_item(
                TableName=self.orders_table,
                Item=item,
                ConditionExpression="attribute_not_exists(order_id)"
            )
            created_order = self._dynamodb_item_to_pharmacy_order_response(item)
            logger.info(f"Pharmacy order {order_id} placed for patient {order_data.patient_id}.")

            # Send order to SQS queue for asynchronous processing by an external system/worker
            sqs_message = {
                "order_id": order_id,
                "prescription_id": order_data.prescription_id,
                "patient_id": order_data.patient_id,
                "pharmacy_id": order_data.pharmacy_id,
                "delivery_method": order_data.delivery_method.value,
                "delivery_address": order_data.delivery_address,
                "timestamp": current_time.isoformat()
                # You might include full prescription details if the receiving system needs it directly
            }
            self.sqs.send_message(
                QueueUrl=self.sqs_queue_url,
                MessageBody=json.dumps(sqs_message)
            )
            logger.info(f"Order {order_id} sent to SQS queue.")

            # Send initial notification to patient (e.g., "Order received")
            self._send_pharmacy_notification(
                order_data.patient_id,
                f"Your pharmacy order {order_id} for prescription {order_data.prescription_id} has been received and is pending processing."
            )
            return created_order
        except HTTPException:
            raise # Re-raise if it's already an HTTPException
        except self.dynamodb.exceptions.ConditionalCheckFailedException:
            logger.error(f"Order ID {order_id} already exists.")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order ID conflict.")
        except Exception as e:
            logger.error(f"Error placing pharmacy order: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to place pharmacy order: {e}")

    def get_pharmacy_order(self, order_id: str) -> Optional[PharmacyOrderResponse]:
        """
        Retrieves a single pharmacy order by its ID.
        """
        try:
            response = self.dynamodb.get_item(
                TableName=self.orders_table,
                Key={'order_id': {'S': order_id}}
            )
            item = response.get('Item')
            if item:
                return self._dynamodb_item_to_pharmacy_order_response(item)
            return None
        except Exception as e:
            logger.error(f"Error getting pharmacy order {order_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve pharmacy order: {e}")

    def get_pharmacy_orders_by_patient(self, patient_id: str) -> List[PharmacyOrderResponse]:
        """
        Retrieves all pharmacy orders for a given patient. Requires a GSI on patient_id.
        """
        try:
            response = self.dynamodb.query(
                TableName=self.orders_table,
                IndexName='patient_id-index', # Ensure this GSI exists
                KeyConditionExpression='patient_id = :patient_id',
                ExpressionAttributeValues={':patient_id': {'S': patient_id}}
            )
            orders = [self._dynamodb_item_to_pharmacy_order_response(item) for item in response.get('Items', [])]
            logger.info(f"Retrieved {len(orders)} pharmacy orders for patient {patient_id}.")
            return orders
        except Exception as e:
            logger.error(f"Error getting pharmacy orders for patient {patient_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve patient pharmacy orders: {e}")

    def update_pharmacy_order_status(self, order_id: str, new_status: OrderStatus) -> PharmacyOrderResponse:
        """
        Updates the status of a pharmacy order. This would typically be called by a worker
        processing the SQS queue or a webhook from a pharmacy partner.
        """
        current_time = datetime.now().isoformat()
        try:
            response = self.dynamodb.update_item(
                TableName=self.orders_table,
                Key={'order_id': {'S': order_id}},
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
                logger.warning(f"Order {order_id} not found for status update.")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pharmacy order not found.")

            updated_order = self._dynamodb_item_to_pharmacy_order_response(updated_item)
            logger.info(f"Order {order_id} status updated to {new_status.value}.")

            # Send notification about status change
            self._send_pharmacy_notification(
                updated_order.patient_id,
                f"Your pharmacy order {order_id} is now {new_status.value}."
            )
            return updated_order
        except HTTPException:
            raise # Re-raise if it's already an HTTPException
        except Exception as e:
            logger.error(f"Error updating status for order {order_id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update pharmacy order status: {e}")

    def _send_pharmacy_notification(self, patient_id: str, message: str):
        """
        Sends an SNS notification for a pharmacy-related event.
        In a real application, you'd fetch the patient's preferred contact (email/phone)
        from the Patient Management Service and send targeted notifications.
        For simplicity, this sends to a generic SNS topic.
        """
        notification_payload = {
            "patient_id": patient_id,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        try:
            self.sns.publish(
                TopicArn=self.sns_topic_arn,
                Message=json.dumps(notification_payload),
                Subject="NINC Pharmacy Notification"
            )
            logger.info(f"Notification sent for patient {patient_id}: {message}")
        except Exception as e:
            logger.error(f"Failed to send SNS notification for patient {patient_id}: {e}")
            # Do not re-raise, as notification failure shouldn't block main operation


# --- FastAPI Application Setup ---

app = FastAPI(
    title="NINC Pharmacy Microservice",
    description="API for managing prescriptions and pharmacy orders.",
    version="1.0.0"
)

# Initialize service instances
pharmacy_service = PharmacyService()

# --- API Endpoints ---

@app.post("/prescriptions", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_new_prescription(prescription_data: PrescriptionCreate):
    """
    Creates a new prescription record. (Typically called by doctor/EHR integration).
    """
    return pharmacy_service.create_prescription(prescription_data)

@app.get("/prescriptions/{prescription_id}", response_model=PrescriptionResponse)
async def get_single_prescription(prescription_id: str):
    """
    Retrieves a single prescription by its ID.
    """
    prescription = pharmacy_service.get_prescription(prescription_id)
    if not prescription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prescription not found")
    return prescription

@app.get("/prescriptions/patient/{patient_id}", response_model=List[PrescriptionResponse])
async def get_patient_prescriptions(patient_id: str):
    """
    Retrieves all prescriptions for a specific patient.
    """
    return pharmacy_service.get_prescriptions_by_patient(patient_id)

@app.post("/orders", response_model=PharmacyOrderResponse, status_code=status.HTTP_201_CREATED)
async def place_new_pharmacy_order(order_data: PharmacyOrderCreate):
    """
    Places a new order for a prescription with a chosen pharmacy.
    """
    return pharmacy_service.place_pharmacy_order(order_data)

@app.get("/orders/{order_id}", response_model=PharmacyOrderResponse)
async def get_single_pharmacy_order(order_id: str):
    """
    Retrieves a single pharmacy order by its ID.
    """
    order = pharmacy_service.get_pharmacy_order(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pharmacy order not found")
    return order

@app.get("/orders/patient/{patient_id}", response_model=List[PharmacyOrderResponse])
async def get_patient_pharmacy_orders(patient_id: str):
    """
    Retrieves all pharmacy orders for a specific patient.
    """
    return pharmacy_service.get_pharmacy_orders_by_patient(patient_id)

@app.put("/orders/{order_id}/status", response_model=PharmacyOrderResponse)
async def update_pharmacy_order_status(order_id: str, new_status: OrderStatus):
    """
    Updates the status of an existing pharmacy order.
    (Typically called by pharmacy integration webhook or internal worker).
    """
    return pharmacy_service.update_pharmacy_order_status(order_id, new_status)

# --- Example AWS Resource Setup Commands ---
# You would run these AWS CLI commands or use CloudFormation/Terraform to set up your AWS resources.

"""
# 1. Create DynamoDB Table for Prescriptions
aws dynamodb create-table \
    --table-name NINCPrescriptions \
    --attribute-definitions \
        AttributeName=prescription_id,AttributeType=S \
        AttributeName=patient_id,AttributeType=S \
    --key-schema \
        AttributeName=prescription_id,KeyType=HASH \
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
            }
        ]'

# 2. Create DynamoDB Table for Pharmacy Orders
aws dynamodb create-table \
    --table-name NINCPharmacyOrders \
    --attribute-definitions \
        AttributeName=order_id,AttributeType=S \
        AttributeName=patient_id,AttributeType=S \
    --key-schema \
        AttributeName=order_id,KeyType=HASH \
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
            }
        ]'

# 3. Create SQS Queue for Pharmacy Orders
aws sqs create-queue --queue-name NINCPharmacyOrderQueue

# 4. Create SNS Topic for Pharmacy Notifications
aws sns create-topic --name NINCPharmacyNotifications

# 5. Ensure IAM Role for your FastAPI application has:
#    - DynamoDB permissions: dynamodb:GetItem, dynamodb:PutItem, dynamodb:Query
#    - SQS permissions: sqs:SendMessage
#    - SNS permissions: sns:Publish
"""

# To run this FastAPI application locally:
# 1. Install dependencies: pip install fastapi uvicorn "python-dotenv[extra]" boto3 pydantic
# 2. Create a .env file with your AWS credentials/endpoints and SQS/SNS ARNs/URLs:
#    AWS_REGION=us-east-1
#    PRESCRIPTIONS_TABLE_NAME=NINCPrescriptions
#    PHARMACY_ORDERS_TABLE_NAME=NINCPharmacyOrders
#    SQS_PHARMACY_ORDER_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/NINCPharmacyOrderQueue # Replace with your actual queue URL
#    SNS_PHARMACY_NOTIFICATIONS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:NINCPharmacyNotifications # Replace with your actual topic ARN
# 3. Ensure your AWS CLI is configured with credentials that have access to DynamoDB, SQS, and SNS.
# 4. Run the application: uvicorn pharmacy_service:app --reload --port 8004
# 5. Access the API documentation at http://127.0.0.1:8004/docs


###############################################################################################
#Code Description
###############################################################################################

# This Python code defines a microservice using the FastAPI framework to manage prescriptions and pharmacy orders. 
# It integrates with Amazon Web Services (AWS) services like DynamoDB (for data storage), SQS (for asynchronous messaging), and SNS (for notifications).

# Imports and Setup
# from fastapi import FastAPI, HTTPException, status
# from pydantic import BaseModel, Field
# import boto3
# import os
# import uuid
# import json
# import logging
# from datetime import datetime
# from typing import Optional, List, Dict, Any, Union
# from enum import Enum

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
# Use code with caution
# This section imports necessary libraries:

# FastAPI, HTTPException, and status: For building the web API.
# BaseModel and Field from pydantic: For data validation and serialization.
# boto3: The AWS SDK for Python, used to interact with AWS services.
# os: For accessing environment variables.
# uuid: For generating unique identifiers.
# json: For handling JSON data.
# logging: For logging information and errors.
# datetime: For working with dates and times.
# typing: For type hints, improving code readability and maintainability.
# enum: For defining enumerated types.
# Logging is configured to output informational messages to the console.

# Configuration
# # --- Configuration ---
# AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
# PRESCRIPTIONS_TABLE_NAME = os.getenv("PRESCRIPTIONS_TABLE_NAME", "NINCPrescriptions")
# PHARMACY_ORDERS_TABLE_NAME = os.getenv("PHARMACY_ORDERS_TABLE_NAME", "NINCPharmacyOrders")

# # SQS Queue for sending orders to external pharmacy systems
# SQS_PHARMACY_ORDER_QUEUE_URL = os.getenv("SQS_PHARMACY_ORDER_QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/123456789012/NINCPharmacyOrderQueue")
# # SNS Topic for notifications (e.g., prescription ready, shipped)
# SNS_PHARMACY_NOTIFICATIONS_TOPIC_ARN = os.getenv("SNS_PHARMACY_NOTIFICATIONS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:NINCPharmacyNotifications")
# Use code with caution
# This part sets up configuration variables, primarily using environment variables to make the application configurable without changing the code. Default values are provided if environment variables are not set. These variables specify:

# AWS_REGION: The AWS region to use.
# PRESCRIPTIONS_TABLE_NAME: The name of the DynamoDB table for prescriptions.
# PHARMACY_ORDERS_TABLE_NAME: The name of the DynamoDB table for pharmacy orders.
# SQS_PHARMACY_ORDER_QUEUE_URL: The URL of the SQS queue for sending pharmacy orders.
# SNS_PHARMACY_NOTIFICATIONS_TOPIC_ARN: The ARN of the SNS topic for notifications.
# Enums
# # --- Enums ---
# class PrescriptionStatus(str, Enum):
#     ACTIVE = "active"
#     EXPIRED = "expired"
#     FULFILLED = "fulfilled"
#     CANCELLED = "cancelled"

# class OrderStatus(str, Enum):
#     PENDING = "pending"
#     PROCESSING = "processing"
#     READY_FOR_PICKUP = "ready_for_pickup"
#     SHIPPED = "shipped"
#     DELIVERED = "delivered"
#     CANCELLED = "cancelled"
#     FAILED = "failed"

# class DeliveryMethod(str, Enum):
#     PICKUP = "pickup"
#     DELIVERY = "delivery"
# Use code with caution
# This section defines enumerated types (Enum) to represent the possible statuses for prescriptions and orders, and the possible delivery methods. Using enums helps ensure data consistency and makes the code more readable.

# Pydantic Models
# # --- Pydantic Models for Data Validation and Serialization ---

# class PrescriptionDrug(BaseModel):
#     """
#     Represents a single drug within a prescription.
#     """
#     drug_name: str
#     dosage: str
#     quantity: str
#     instructions: str
#     refills_remaining: int = Field(ge=0)

# class PrescriptionCreate(BaseModel):
#     """
#     Model for creating a new prescription. This would typically be
#     created by a doctor or integrated from an EHR system.
#     """
#     patient_id: str
#     doctor_id: str
#     prescription_date: datetime
#     expiry_date: datetime
#     drugs: List[PrescriptionDrug]
#     notes: Optional[str] = None

# class PrescriptionResponse(PrescriptionCreate):
#     """
#     Model for returning prescription details, including its ID.
#     """
#     prescription_id: str
#     status: PrescriptionStatus = PrescriptionStatus.ACTIVE
#     created_at: datetime
#     updated_at: datetime

# class PharmacyOrderCreate(BaseModel):
#     """
#     Model for a patient placing an order for a prescription.
#     """
#     patient_id: str
#     prescription_id: str
#     pharmacy_id: str = Field(..., description="ID of the pharmacy chosen by the patient.")
#     delivery_method: DeliveryMethod
#     delivery_address: Optional[Dict[str, str]] = None # Required if delivery_method is DELIVERY
#     # Could include payment_transaction_id if payment is pre-authorized/linked

# class PharmacyOrderResponse(PharmacyOrderCreate):
#     """
#     Model for returning pharmacy order details.
#     """
#     order_id: str
#     status: OrderStatus = OrderStatus.PENDING
#     created_at: datetime
#     updated_at: datetime
#     # Add tracking information later
# Use code with caution
# Pydantic models are used for data validation and serialization. These classes define the structure and expected data types for API requests and responses:

# PrescriptionDrug: Represents the details of a single drug in a prescription.
# PrescriptionCreate: Defines the data needed to create a new prescription.
# PrescriptionResponse: Defines the structure of the data returned when retrieving prescription details, including generated fields like prescription_id, status, created_at, and updated_at. It inherits from PrescriptionCreate.
# PharmacyOrderCreate: Defines the data needed for a patient to place a pharmacy order.
# PharmacyOrderResponse: Defines the structure of the data returned when retrieving pharmacy order details, including generated fields like order_id, status, `created_

