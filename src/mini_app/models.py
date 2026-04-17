from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from enum import Enum


class VersionEnum(str, Enum):
    LITE = "lite"
    BOOKING = "booking"


class UserData(BaseModel):
    """User data from Telegram WebApp"""
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: bool = False


class UserProfileResponse(BaseModel):
    """User profile for mini app"""
    user_id: int
    username: Optional[str] = None
    first_name: str
    phone: Optional[str] = None
    preferred_version: VersionEnum = VersionEnum.LITE


class ServiceData(BaseModel):
    """Service information"""
    id: str
    name: str
    description: str
    emoji: Optional[str] = None


class TimeSlot(BaseModel):
    """Available time slot"""
    time: str  # HH:MM format
    available: bool


class QuoteRequest(BaseModel):
    """Quote request from mini app"""
    service_id: str
    date: str  # YYYY-MM-DD format
    time: Optional[str] = None  # HH:MM format


class QuoteResponse(BaseModel):
    """Quote response"""
    service_id: str
    service_name: str
    date: str
    time: Optional[str] = None
    price_min: float
    price_max: float
    currency: str = "AED"


class OrderSubmission(BaseModel):
    """Order submission from mini app"""
    service_id: str
    service_name: str
    date: str  # YYYY-MM-DD
    time: Optional[str] = None  # HH:MM
    proposed_price: Optional[float] = None
    quantity: int = 1
    notes: Optional[str] = None
    version: VersionEnum


class OrderResponse(BaseModel):
    """Order response"""
    order_id: Optional[str] = None
    status: str
    message: str
    data: Optional[Dict] = None


class APIResponse(BaseModel):
    """Generic API response"""
    success: bool
    message: str
    data: Optional[Dict] = None
    errors: Optional[List[str]] = None


class ListVersionsResponse(BaseModel):
    """Available versions response"""
    versions: List[Dict] = Field(default_factory=list)
    default_version: VersionEnum = VersionEnum.LITE
