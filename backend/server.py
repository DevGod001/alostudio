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
import base64
import aiofiles

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
    FRAMES = "frames"

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
    features: Optional[List[str]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class ComboService(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    service_ids: List[str]
    description: str
    total_price: float
    discount_percentage: float = 15.0
    final_price: float
    duration_hours: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    service_id: str
    service_type: str
    is_combo: bool = False
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

class UserPhoto(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_email: str
    user_name: str
    booking_id: Optional[str] = None
    file_name: str
    file_data: Optional[str] = None  # Base64 encoded file data
    file_url: str
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    photo_type: str  # "session", "upload", "edited"
    is_edited: bool = False
    is_private: bool = False
    uploaded_by_admin: bool = False

class FrameOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_email: str
    user_name: str
    photo_ids: List[str]  # References to UserPhoto IDs
    frame_size: str  # "5x7", "8x10", "11x14", "16x20"
    frame_style: str  # "modern", "classic", "rustic"
    quantity: int
    total_price: float
    status: BookingStatus = BookingStatus.PENDING_PAYMENT
    payment_amount: Optional[float] = None
    payment_reference: Optional[str] = None
    special_instructions: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AdminSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Earnings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    booking_id: str
    service_type: str
    amount: float
    payment_date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Admin(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password_hash: str  # In real app, use proper hashing
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Settings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    whatsapp_number: str = "+16144055997"
    cashapp_id: str = "$VitiPay"
    business_name: str = "Alostudio"
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

class SettingsUpdate(BaseModel):
    whatsapp_number: str
    cashapp_id: str

class FrameOrderCreate(BaseModel):
    user_email: str
    user_name: str
    photo_ids: List[str]
    frame_size: str
    frame_style: str
    quantity: int
    special_instructions: Optional[str] = None

class PhotoUpload(BaseModel):
    user_email: str
    user_name: str
    file_name: str
    photo_type: str = "upload"

class AdminPhotoUpload(BaseModel):
    user_email: str
    user_name: str
    booking_id: str
    files: List[dict]  # List of {file_name: str, file_data: str (base64)}
    photo_type: str = "session"

# Initialize default services
async def initialize_default_services():
    # Clear existing services first
    await db.services.delete_many({})
    await db.combo_services.delete_many({})
    
    default_services = [
        # Makeup Services
        {
            "name": "Natural Glow Glam",
            "type": "makeup",
            "description": "Perfect for everyday elegance with subtle enhancement. Includes skin prep, natural foundation, soft eyeshadow, mascara, and nude lip color.",
            "base_price": 75.0,
            "deposit_percentage": 25.0,
            "duration_hours": 1.0,
            "features": ["Skin prep", "Natural foundation", "Soft eyeshadow", "Mascara", "Nude lip color"]
        },
        {
            "name": "Soft Glow Glam",
            "type": "makeup",
            "description": "Ideal for special occasions with enhanced beauty. Includes contouring, highlighting, defined eyes, and glamorous finish.",
            "base_price": 95.0,
            "deposit_percentage": 25.0,
            "duration_hours": 1.5,
            "features": ["Contouring", "Highlighting", "Defined eyes", "Glamorous finish", "Professional touch-ups"]
        },
        {
            "name": "Full Glow Glam",
            "type": "makeup",
            "description": "Complete transformation for red carpet events. Premium makeup with airbrush foundation, dramatic eyes, contouring, and luxury finish.",
            "base_price": 150.0,
            "deposit_percentage": 25.0,
            "duration_hours": 2.0,
            "features": ["Airbrush foundation", "Dramatic eyes", "Full contouring", "Luxury finish", "False lashes", "Premium products"]
        },
        # Photography Services
        {
            "name": "Standard Indoor Session",
            "type": "photography",
            "location": "indoor",
            "description": "Professional studio session with basic lighting setup, 1 hour session, 10 edited photos.",
            "base_price": 180.0,
            "deposit_percentage": 25.0,
            "duration_hours": 1.0,
            "features": ["Professional lighting", "1 hour session", "10 edited photos", "Basic retouching", "Digital delivery"]
        },
        {
            "name": "Deluxe Indoor Session",
            "type": "photography",
            "location": "indoor",
            "description": "Premium studio session with advanced lighting, props, 2 hours, 20 edited photos, and styling consultation.",
            "base_price": 280.0,
            "deposit_percentage": 25.0,
            "duration_hours": 2.0,
            "features": ["Advanced lighting", "Props included", "2 hours session", "20 edited photos", "Styling consultation", "Premium retouching"]
        },
        {
            "name": "Newborn/Infant Session",
            "type": "photography",
            "location": "indoor",
            "description": "Specialized newborn photography with safety first approach. Up to 3 clothing changes, 5 edited photos, $15 per additional edit.",
            "base_price": 230.0,
            "deposit_percentage": 25.0,
            "duration_hours": 2.0,
            "features": ["Safety first approach", "Up to 3 clothing changes", "5 edited photos", "Newborn props", "Gentle handling", "Additional edits $15 each"]
        },
        {
            "name": "Outdoor Photography",
            "type": "photography",
            "location": "outdoor",
            "description": "On-location outdoor session at scenic locations. Natural lighting, candid and posed shots, 15 edited photos.",
            "base_price": 320.0,
            "deposit_percentage": 60.0,
            "duration_hours": 2.0,
            "features": ["Scenic locations", "Natural lighting", "Candid & posed shots", "15 edited photos", "Location scouting", "Weather backup plan"]
        },
        # Video Services
        {
            "name": "Indoor Video Session",
            "type": "video",
            "location": "indoor",
            "description": "Professional studio video production with lighting setup, 2-hour session, basic editing included.",
            "base_price": 350.0,
            "deposit_percentage": 25.0,
            "duration_hours": 2.0,
            "features": ["Professional lighting", "2-hour session", "Basic editing", "Multiple angles", "Audio recording", "Digital delivery"]
        },
        {
            "name": "Outdoor Video Session",
            "type": "video",
            "location": "outdoor",
            "description": "On-location video production for events, documentaries, or promotional content. Professional equipment and editing.",
            "base_price": 500.0,
            "deposit_percentage": 60.0,
            "duration_hours": 3.0,
            "features": ["Professional equipment", "3-hour session", "Advanced editing", "Multiple locations", "Drone shots available", "Sound recording"]
        },
        # Additional Services
        {
            "name": "Photo Editing Service",
            "type": "editing",
            "description": "Professional photo editing and retouching. Upload your photos and we'll enhance them with professional editing techniques.",
            "base_price": 25.0,
            "deposit_percentage": 50.0,
            "duration_hours": 0.5,
            "features": ["Color correction", "Retouching", "Background removal", "Creative effects", "High-resolution output", "1-2 day turnaround"]
        },
        {
            "name": "Video Editing Service", 
            "type": "editing",
            "description": "Professional video editing with transitions, effects, color grading, and sound mixing. Perfect for events, vlogs, or promotional content.",
            "base_price": 75.0,
            "deposit_percentage": 50.0,
            "duration_hours": 2.0,
            "features": ["Professional editing", "Transitions & effects", "Color grading", "Sound mixing", "Title graphics", "1-2 week turnaround"]
        },
        {
            "name": "Graphic Design Service",
            "type": "graphic_design",
            "description": "Custom graphic design for logos, flyers, social media posts, invitations, and more. Professional creative solutions.",
            "base_price": 85.0,
            "deposit_percentage": 50.0,
            "duration_hours": 1.5,
            "features": ["Custom designs", "Multiple revisions", "High-resolution files", "Various formats", "Brand consistency", "3-5 day delivery"]
        },
        {
            "name": "Custom Picture Frames",
            "type": "frames",
            "description": "High-quality custom frames for your professional photos. Choose from your existing photo gallery with us or upload new photos to be framed.",
            "base_price": 45.0,
            "deposit_percentage": 50.0,
            "duration_hours": 0.0,
            "features": ["Choose from photo gallery", "Multiple sizes available", "Professional mounting", "High quality materials", "Various frame styles", "Custom sizing options"]
        }
    ]
    
    service_ids = {}
    for service_data in default_services:
        service = Service(**service_data)
        await db.services.insert_one(service.dict())
        service_ids[service.type] = service.id
    
    # Create combo services
    combo_services = [
        {
            "name": "Makeup + Photography Combo",
            "service_ids": [service_ids.get("makeup"), service_ids.get("photography")],
            "description": "Perfect combination of professional makeup and photography session. Get the complete experience with 15% discount.",
            "total_price": 255.0,  # Natural Glow (75) + Standard Photo (180)
            "discount_percentage": 15.0,
            "final_price": 216.75,  # 15% discount
            "duration_hours": 2.0
        },
        {
            "name": "Makeup + Video Combo",
            "service_ids": [service_ids.get("makeup"), service_ids.get("video")], 
            "description": "Professional makeup plus video session combo. Look your best on camera with our expert team and save 15%.",
            "total_price": 425.0,  # Natural Glow (75) + Indoor Video (350)
            "discount_percentage": 15.0,
            "final_price": 361.25,  # 15% discount
            "duration_hours": 3.0
        },
        {
            "name": "Full Glam + Deluxe Photo Combo",
            "service_ids": [service_ids.get("makeup"), service_ids.get("photography")],
            "description": "Ultimate experience with Full Glow Glam makeup and Deluxe Photography session. Perfect for special occasions with 15% savings.",
            "total_price": 430.0,  # Full Glow (150) + Deluxe Photo (280)
            "discount_percentage": 15.0,
            "final_price": 365.50,  # 15% discount
            "duration_hours": 4.0
        }
    ]
    
    for combo_data in combo_services:
        combo = ComboService(**combo_data)
        await db.combo_services.insert_one(combo.dict())

# Initialize default admin
async def initialize_default_admin():
    existing_admin = await db.admins.count_documents({})
    if existing_admin == 0:
        default_admin = Admin(username="admin", password_hash="admin123")
        await db.admins.insert_one(default_admin.dict())

# Initialize default settings
async def initialize_default_settings():
    existing_settings = await db.settings.count_documents({})
    if existing_settings == 0:
        default_settings = Settings()
        await db.settings.insert_one(default_settings.dict())

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

@api_router.get("/combo-services")
async def get_combo_services():
    combos = await db.combo_services.find({"is_active": True}).to_list(1000)
    # Clean up MongoDB ObjectId
    for combo in combos:
        if '_id' in combo:
            del combo['_id']
    return combos

@api_router.get("/settings")
async def get_settings():
    settings = await db.settings.find_one({})
    if settings:
        if '_id' in settings:
            del settings['_id']
    return settings or {"whatsapp_number": "+16144055997", "cashapp_id": "$VitiPay", "business_name": "Alostudio"}

@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking_data: BookingCreate):
    # Check if service exists (regular service)
    service = await db.services.find_one({"id": booking_data.service_id})
    combo_service = None
    is_combo = False
    
    if not service:
        # Check if it's a combo service
        combo_service = await db.combo_services.find_one({"id": booking_data.service_id})
        if combo_service:
            is_combo = True
        else:
            raise HTTPException(status_code=404, detail="Service not found")
    
    # Check availability (simplified - check if time slot is taken)
    booking_datetime = datetime.strptime(f"{booking_data.booking_date} {booking_data.booking_time}", "%Y-%m-%d %H:%M")
    existing_booking = await db.bookings.find_one({
        "booking_date": booking_datetime,
        "status": {"$in": ["confirmed", "payment_submitted"]}
    })
    
    if existing_booking:
        raise HTTPException(status_code=400, detail="Time slot not available")
    
    service_type = combo_service["name"] if is_combo else service["type"]
    
    booking = Booking(
        service_id=booking_data.service_id,
        service_type=service_type,
        is_combo=is_combo,
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

# Admin Routes - moved to session management above
@api_router.get("/admin/bookings")
async def get_all_bookings():
    bookings = await db.bookings.find().sort("created_at", -1).to_list(1000)
    # Convert MongoDB documents to proper format
    result = []
    for booking in bookings:
        if '_id' in booking:
            del booking['_id']  # Remove MongoDB ObjectId
        result.append(booking)
    return result

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
    
    # Add to earnings when booking is approved
    booking = await db.bookings.find_one({"id": booking_id})
    if booking and booking.get("payment_amount"):
        earnings = Earnings(
            booking_id=booking_id,
            service_type=booking["service_type"],
            amount=booking["payment_amount"],
            payment_date=datetime.utcnow()
        )
        await db.earnings.insert_one(earnings.dict())
    
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

# Admin photo upload for completed bookings
@api_router.post("/admin/bookings/{booking_id}/upload-photos")
async def admin_upload_photos(booking_id: str, files: List[UploadFile] = File(...)):
    """Admin uploads photos/videos for a completed booking"""
    # Verify booking exists and is completed
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking["status"] != "completed":
        raise HTTPException(status_code=400, detail="Can only upload photos for completed bookings")
    
    uploaded_photos = []
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("/app/uploads")
    upload_dir.mkdir(exist_ok=True)
    
    for file in files:
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_filename = f"{booking_id}_{str(uuid.uuid4())[:8]}.{file_extension}"
        file_path = upload_dir / unique_filename
        
        try:
            # Read file content
            file_content = await file.read()
            
            # Save file to disk
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Convert to base64 for database storage
            file_data_b64 = base64.b64encode(file_content).decode('utf-8')
            
            # Create photo record
            photo = UserPhoto(
                user_email=booking["customer_email"],
                user_name=booking["customer_name"],
                booking_id=booking_id,
                file_name=file.filename,
                file_data=file_data_b64,
                file_url=f"/uploads/{unique_filename}",
                photo_type="session",
                uploaded_by_admin=True
            )
            
            await db.user_photos.insert_one(photo.dict())
            uploaded_photos.append({
                "id": photo.id,
                "file_name": file.filename,
                "file_url": photo.file_url
            })
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload {file.filename}: {str(e)}")
    
    return {
        "message": f"Successfully uploaded {len(uploaded_photos)} photos",
        "booking_id": booking_id,
        "photos": uploaded_photos
    }

@api_router.post("/admin/bookings/{booking_id}/upload-photos-base64")
async def admin_upload_photos_base64(booking_id: str, upload_data: AdminPhotoUpload):
    """Admin uploads photos/videos using base64 data for a completed booking"""
    # Verify booking exists and is completed
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking["status"] != "completed":
        raise HTTPException(status_code=400, detail="Can only upload photos for completed bookings")
    
    uploaded_photos = []
    
    for file_data in upload_data.files:
        photo = UserPhoto(
            user_email=upload_data.user_email,
            user_name=upload_data.user_name,
            booking_id=booking_id,
            file_name=file_data["file_name"],
            file_data=file_data["file_data"],
            file_url=f"data:image/jpeg;base64,{file_data['file_data']}",
            photo_type=upload_data.photo_type,
            uploaded_by_admin=True
        )
        
        await db.user_photos.insert_one(photo.dict())
        uploaded_photos.append({
            "id": photo.id,
            "file_name": photo.file_name,
            "file_url": photo.file_url
        })
    
    return {
        "message": f"Successfully uploaded {len(uploaded_photos)} photos",
        "booking_id": booking_id,
        "photos": uploaded_photos
    }

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

@api_router.put("/admin/settings")
async def update_settings(settings_data: SettingsUpdate):
    result = await db.settings.update_one(
        {},
        {
            "$set": {
                "whatsapp_number": settings_data.whatsapp_number,
                "cashapp_id": settings_data.cashapp_id,
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    return {"message": "Settings updated successfully"}

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

# User Photo Gallery Routes
@api_router.get("/user/{email}/photos")
async def get_user_photos(email: str):
    """Get all photos for a user"""
    photos = await db.user_photos.find({"user_email": email}).sort("upload_date", -1).to_list(1000)
    # Clean up MongoDB ObjectId
    for photo in photos:
        if '_id' in photo:
            del photo['_id']
    return photos

@api_router.post("/user/photos")
async def upload_user_photo(photo_data: PhotoUpload):
    """Add a photo to user's gallery"""
    photo = UserPhoto(
        **photo_data.dict(),
        file_url=f"/uploads/{photo_data.file_name}"  # In real app, use actual file upload
    )
    await db.user_photos.insert_one(photo.dict())
    return {"message": "Photo uploaded successfully", "photo_id": photo.id}

@api_router.get("/user/{email}/dashboard")
async def get_user_dashboard(email: str):
    """Get comprehensive user dashboard data"""
    # Get user photos
    photos = await db.user_photos.find({"user_email": email}).sort("upload_date", -1).to_list(1000)
    for photo in photos:
        if '_id' in photo:
            del photo['_id']
    
    # Get user bookings
    bookings = await db.bookings.find({"customer_email": email}).sort("created_at", -1).to_list(1000)
    for booking in bookings:
        if '_id' in booking:
            del booking['_id']
    
    # Get frame orders
    frame_orders = await db.frame_orders.find({"user_email": email}).sort("created_at", -1).to_list(1000)
    for order in frame_orders:
        if '_id' in order:
            del order['_id']
    
    return {
        "photos": photos,
        "bookings": bookings,
        "frame_orders": frame_orders,
        "stats": {
            "total_photos": len(photos),
            "total_bookings": len(bookings),
            "pending_orders": len([o for o in frame_orders if o["status"] in ["pending_payment", "payment_submitted"]])
        }
    }

# Frame Order Routes
@api_router.post("/frames/order")
async def create_frame_order(order_data: FrameOrderCreate):
    """Create a new frame order"""
    # Calculate price based on size and quantity
    size_prices = {
        "5x7": 25.0,
        "8x10": 45.0,
        "11x14": 75.0,
        "16x20": 120.0
    }
    
    base_price = size_prices.get(order_data.frame_size, 45.0)
    total_price = base_price * order_data.quantity
    
    frame_order = FrameOrder(
        **order_data.dict(),
        total_price=total_price
    )
    
    await db.frame_orders.insert_one(frame_order.dict())
    return frame_order

@api_router.post("/frames/{order_id}/payment")
async def submit_frame_payment(order_id: str, payment_data: PaymentSubmission):
    """Submit payment for frame order"""
    result = await db.frame_orders.update_one(
        {"id": order_id},
        {
            "$set": {
                "status": "payment_submitted",
                "payment_amount": payment_data.payment_amount,
                "payment_reference": payment_data.payment_reference,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Frame order not found")
    
    return {"message": "Payment submitted for admin review"}

@api_router.get("/admin/frames")
async def get_all_frame_orders():
    """Get all frame orders for admin"""
    orders = await db.frame_orders.find().sort("created_at", -1).to_list(1000)
    for order in orders:
        if '_id' in order:
            del order['_id']
    return orders

@api_router.put("/admin/frames/{order_id}/approve")
async def approve_frame_order(order_id: str):
    """Approve a frame order payment"""
    result = await db.frame_orders.update_one(
        {"id": order_id},
        {
            "$set": {
                "status": "confirmed",
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Frame order not found")
    
    # Add to earnings
    order = await db.frame_orders.find_one({"id": order_id})
    if order and order.get("payment_amount"):
        earnings = Earnings(
            booking_id=order_id,
            service_type="frames",
            amount=order["payment_amount"],
            payment_date=datetime.utcnow()
        )
        await db.earnings.insert_one(earnings.dict())
    
    return {"message": "Frame order approved"}

# Admin Earnings/Wallet Routes
@api_router.get("/admin/earnings")
async def get_admin_earnings():
    """Get admin wallet/earnings summary"""
    # Get all earnings
    earnings = await db.earnings.find().sort("payment_date", -1).to_list(1000)
    for earning in earnings:
        if '_id' in earning:
            del earning['_id']
    
    # Calculate totals
    total_earnings = sum(e["amount"] for e in earnings)
    
    # Group by service type
    service_totals = {}
    for earning in earnings:
        service_type = earning["service_type"]
        service_totals[service_type] = service_totals.get(service_type, 0) + earning["amount"]
    
    # Get recent earnings (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_earnings = [e for e in earnings if e["payment_date"] > thirty_days_ago]
    recent_total = sum(e["amount"] for e in recent_earnings)
    
    return {
        "total_earnings": total_earnings,
        "recent_earnings": recent_total,
        "service_breakdown": service_totals,
        "earnings_history": earnings[:50],  # Last 50 transactions
        "stats": {
            "total_transactions": len(earnings),
            "recent_transactions": len(recent_earnings),
            "average_transaction": total_earnings / len(earnings) if earnings else 0
        }
    }

# Admin Session Management
@api_router.post("/admin/login")
async def admin_login(login_data: AdminLogin):
    admin = await db.admins.find_one({"username": login_data.username, "password_hash": login_data.password})
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session token (1 hour expiry)
    session_token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    session = AdminSession(
        admin_id=admin["id"],
        session_token=session_token,
        expires_at=expires_at
    )
    
    await db.admin_sessions.insert_one(session.dict())
    
    return {
        "message": "Login successful", 
        "admin_id": admin["id"],
        "session_token": session_token,
        "expires_at": expires_at.isoformat()
    }

@api_router.post("/admin/verify-session")
async def verify_admin_session(session_token: str):
    """Verify admin session and extend if valid"""
    session = await db.admin_sessions.find_one({"session_token": session_token})
    
    if not session or datetime.utcnow() > session["expires_at"]:
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Extend session by 1 hour
    new_expires_at = datetime.utcnow() + timedelta(hours=1)
    await db.admin_sessions.update_one(
        {"session_token": session_token},
        {"$set": {"expires_at": new_expires_at}}
    )
    
    return {"message": "Session valid", "expires_at": new_expires_at.isoformat()}

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
    await initialize_default_settings()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()