from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import json
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class ServiceType(str, Enum):
    MAKEUP = "makeup"
    PHOTOGRAPHY = "photography"
    VIDEO = "video"
    COMBO = "combo"
    EDITING = "editing"
    GRAPHIC_DESIGN = "graphic_design"
    MEMORY_STORAGE = "memory_storage"

class BookingStatus(str, Enum):
    PENDING_PAYMENT = "pending_payment"
    PAYMENT_SUBMITTED = "payment_submitted"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class SessionLocation(str, Enum):
    INDOOR = "indoor"
    OUTDOOR = "outdoor"

# Models
class Service(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: ServiceType
    location: Optional[SessionLocation] = None
    description: str
    base_price: float
    deposit_percentage: float  # 25% for indoor, 60% for outdoor
    duration_hours: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    service_id: str
    customer_email: str
    customer_phone: str
    customer_name: str
    booking_date: datetime
    booking_time: str
    status: BookingStatus = BookingStatus.PENDING_PAYMENT
    payment_amount: Optional[float] = None
    payment_method: str = "cashapp"
    payment_reference: Optional[str] = None
    admin_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Admin(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password_hash: str  # In real app, use proper hashing
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PricingConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    service_type: str
    service_name: str
    price: float
    description: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Input Models
class BookingCreate(BaseModel):
    service_id: str
    customer_email: str
    customer_phone: str
    customer_name: str
    booking_date: str  # YYYY-MM-DD format
    booking_time: str  # HH:MM format

class PaymentSubmission(BaseModel):
    booking_id: str
    payment_amount: float
    payment_reference: str

class AdminLogin(BaseModel):
    username: str
    password: str

class ServiceCreate(BaseModel):
    name: str
    type: ServiceType
    location: Optional[SessionLocation] = None
    description: str
    base_price: float
    deposit_percentage: float
    duration_hours: float

# Initialize default services
async def initialize_default_services():
    existing_services = await db.services.count_documents({})
    if existing_services == 0:
        default_services = [
            # Makeup Services
            {
                "name": "Natural Glow Glam",
                "type": "makeup",
                "description": "Perfect for everyday elegance with subtle enhancement. Includes skin prep, natural foundation, soft eyeshadow, mascara, and nude lip color.",
                "base_price": 75.0,
                "deposit_percentage": 25.0,
                "duration_hours": 1
            },
            {
                "name": "Soft Glow Glam",
                "type": "makeup",
                "description": "Ideal for special occasions with enhanced beauty. Includes contouring, highlighting, defined eyes, and glamorous finish.",
                "base_price": 95.0,
                "deposit_percentage": 25.0,
                "duration_hours": 1.5
            },
            {
                "name": "Full Glow Glam",
                "type": "makeup",
                "description": "Complete transformation for red carpet events. Premium makeup with airbrush foundation, dramatic eyes, contouring, and luxury finish.",
                "base_price": 150.0,
                "deposit_percentage": 25.0,
                "duration_hours": 2
            },
            # Photography Services
            {
                "name": "Standard Indoor Session",
                "type": "photography",
                "location": "indoor",
                "description": "Professional studio session with basic lighting setup, 1 hour session, 10 edited photos.",
                "base_price": 180.0,
                "deposit_percentage": 25.0,
                "duration_hours": 1
            },
            {
                "name": "Deluxe Indoor Session",
                "type": "photography",
                "location": "indoor",
                "description": "Premium studio session with advanced lighting, props, 2 hours, 20 edited photos, and styling consultation.",
                "base_price": 280.0,
                "deposit_percentage": 25.0,
                "duration_hours": 2
            },
            {
                "name": "Newborn/Infant Session",
                "type": "photography",
                "location": "indoor",
                "description": "Specialized newborn photography with safety first approach. Up to 3 clothing changes, 5 edited photos, $15 per additional edit.",
                "base_price": 230.0,
                "deposit_percentage": 25.0,
                "duration_hours": 2
            },
            {
                "name": "Outdoor Photography",
                "type": "photography",
                "location": "outdoor",
                "description": "On-location outdoor session at scenic locations. Natural lighting, candid and posed shots, 15 edited photos.",
                "base_price": 320.0,
                "deposit_percentage": 60.0,
                "duration_hours": 2
            },
            # Video Services
            {
                "name": "Indoor Video Session",
                "type": "video",
                "location": "indoor",
                "description": "Professional studio video production with lighting setup, 2-hour session, basic editing included.",
                "base_price": 350.0,
                "deposit_percentage": 25.0,
                "duration_hours": 2
            },
            {
                "name": "Outdoor Video Session",
                "type": "video",
                "location": "outdoor",
                "description": "On-location video production for events, documentaries, or promotional content. Professional equipment and editing.",
                "base_price": 500.0,
                "deposit_percentage": 60.0,
                "duration_hours": 3
            }
        ]
        
        for service_data in default_services:
            service = Service(**service_data)
            await db.services.insert_one(service.dict())

# Initialize default admin
async def initialize_default_admin():
    existing_admin = await db.admins.count_documents({})
    if existing_admin == 0:
        default_admin = Admin(username="admin", password_hash="admin123")  # Use proper hashing in production
        await db.admins.insert_one(default_admin.dict())

# Routes
@api_router.get("/")
async def root():
    return {"message": "Welcome to Alostudio API"}

@api_router.get("/services", response_model=List[Service])
async def get_services():
    services = await db.services.find({"is_active": True}).to_list(1000)
    return [Service(**service) for service in services]

@api_router.get("/services/{service_type}")
async def get_services_by_type(service_type: ServiceType):
    services = await db.services.find({"type": service_type, "is_active": True}).to_list(1000)
    return [Service(**service) for service in services]

@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking_data: BookingCreate):
    # Check if service exists
    service = await db.services.find_one({"id": booking_data.service_id})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Check availability (simplified - check if time slot is taken)
    booking_datetime = datetime.strptime(f"{booking_data.booking_date} {booking_data.booking_time}", "%Y-%m-%d %H:%M")
    existing_booking = await db.bookings.find_one({
        "booking_date": booking_datetime,
        "status": {"$in": ["confirmed", "payment_submitted"]}
    })
    
    if existing_booking:
        raise HTTPException(status_code=400, detail="Time slot not available")
    
    booking = Booking(
        service_id=booking_data.service_id,
        customer_email=booking_data.customer_email,
        customer_phone=booking_data.customer_phone,
        customer_name=booking_data.customer_name,
        booking_date=booking_datetime,
        booking_time=booking_data.booking_time
    )
    
    await db.bookings.insert_one(booking.dict())
    return booking

@api_router.post("/bookings/{booking_id}/payment")
async def submit_payment(booking_id: str, payment_data: PaymentSubmission):
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Update booking with payment info
    await db.bookings.update_one(
        {"id": booking_id},
        {
            "$set": {
                "status": "payment_submitted",
                "payment_amount": payment_data.payment_amount,
                "payment_reference": payment_data.payment_reference,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"message": "Payment submitted for admin review"}

@api_router.get("/bookings/customer/{email}")
async def get_customer_bookings(email: str):
    bookings = await db.bookings.find({"customer_email": email}).to_list(1000)
    # Convert MongoDB documents to proper format
    result = []
    for booking in bookings:
        if '_id' in booking:
            del booking['_id']  # Remove MongoDB ObjectId
        result.append(booking)
    return result

# Admin Routes
@api_router.post("/admin/login")
async def admin_login(login_data: AdminLogin):
    admin = await db.admins.find_one({"username": login_data.username, "password_hash": login_data.password})
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"message": "Login successful", "admin_id": admin["id"]}

@api_router.get("/admin/bookings")
async def get_all_bookings():
    bookings = await db.bookings.find().sort("created_at", -1).to_list(1000)
    return bookings

@api_router.put("/admin/bookings/{booking_id}/approve")
async def approve_booking(booking_id: str):
    result = await db.bookings.update_one(
        {"id": booking_id},
        {
            "$set": {
                "status": "confirmed",
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return {"message": "Booking approved"}

@api_router.put("/admin/bookings/{booking_id}/complete")
async def complete_booking(booking_id: str):
    result = await db.bookings.update_one(
        {"id": booking_id},
        {
            "$set": {
                "status": "completed",
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return {"message": "Booking marked as completed"}

@api_router.put("/admin/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: str):
    result = await db.bookings.update_one(
        {"id": booking_id},
        {
            "$set": {
                "status": "cancelled",
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return {"message": "Booking cancelled"}

@api_router.get("/admin/services", response_model=List[Service])
async def admin_get_all_services():
    services = await db.services.find().to_list(1000)
    return [Service(**service) for service in services]

@api_router.post("/admin/services", response_model=Service)
async def admin_create_service(service_data: ServiceCreate):
    service = Service(**service_data.dict())
    await db.services.insert_one(service.dict())
    return service

@api_router.put("/admin/services/{service_id}/price")
async def update_service_price(service_id: str, price: float):
    result = await db.services.update_one(
        {"id": service_id},
        {"$set": {"base_price": price}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return {"message": "Service price updated"}

# Check availability
@api_router.get("/availability/{date}")
async def check_availability(date: str):
    """Check available time slots for a specific date"""
    try:
        check_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Get all bookings for that date
    start_of_day = check_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    
    booked_slots = await db.bookings.find({
        "booking_date": {
            "$gte": start_of_day,
            "$lt": end_of_day
        },
        "status": {"$in": ["confirmed", "payment_submitted"]}
    }).to_list(1000)
    
    booked_times = [booking["booking_time"] for booking in booked_slots]
    
    # Generate available time slots (9 AM to 6 PM)
    available_slots = []
    for hour in range(9, 18):  # 9 AM to 5 PM
        for minute in [0, 30]:  # 30-minute intervals
            time_str = f"{hour:02d}:{minute:02d}"
            if time_str not in booked_times:
                available_slots.append(time_str)
    
    return {"available_slots": available_slots}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await initialize_default_services()
    await initialize_default_admin()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()