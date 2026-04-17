from fastapi import APIRouter, Depends, HTTPException
from typing import List
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.mini_app.models import (
    UserData, UserProfileResponse, ServiceData,
    QuoteRequest, QuoteResponse, OrderSubmission,
    OrderResponse, APIResponse, ListVersionsResponse,
    VersionEnum
)
from src.mini_app.api.dependencies import get_user_from_init_data, get_current_user
from src.config import SERVICES, SUBSCRIPTION_PLANS, MINI_APP_VERSIONS, DATABASE_PATH
from src.database.db_manager import DatabaseManager

router = APIRouter(prefix="/api/v1", tags=["mini_app"])
db = DatabaseManager(DATABASE_PATH)


@router.get("/user", response_model=UserProfileResponse)
async def get_user_profile(user: UserData = Depends(get_user_from_init_data)):
    """Get user profile data"""
    db_user = db.get_user(user.id)

    return UserProfileResponse(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        phone=db_user.get('phone_number') if db_user else None,
        preferred_version=VersionEnum.LITE
    )


@router.get("/services", response_model=List[ServiceData])
async def get_services(user_id: int = Depends(get_current_user)):
    """Get all available services"""
    services = []

    for service_id, service_info in SERVICES.items():
        services.append(
            ServiceData(
                id=service_id,
                name=service_info['name'],
                description=service_info['description']
            )
        )

    return services


@router.post("/quote", response_model=QuoteResponse)
async def get_quote(
    request: QuoteRequest,
    user_id: int = Depends(get_current_user)
):
    """Get quote for a service"""

    if request.service_id not in SERVICES:
        raise HTTPException(status_code=400, detail="Invalid service")

    service = SERVICES[request.service_id]

    # Get price range - using average subscription prices as base
    price_min = 180
    price_max = 350

    return QuoteResponse(
        service_id=request.service_id,
        service_name=service['name'],
        date=request.date,
        time=request.time,
        price_min=price_min,
        price_max=price_max,
        currency="AED"
    )


@router.post("/submit-order", response_model=OrderResponse)
async def submit_order(
    order: OrderSubmission,
    user_id: int = Depends(get_current_user)
):
    """Submit a new order from mini app"""

    if order.service_id not in SERVICES:
        raise HTTPException(status_code=400, detail="Invalid service")

    try:
        # Create order in database
        order_id = db.create_order(
            user_id=user_id,
            service_type=order.service_id,
            hours=1,  # Default 1 hour
            estimated_price=order.proposed_price or 250,
            scheduled_date=order.date
        )

        # If there's a proposed price, create a deal
        if order.proposed_price:
            deal_id = db.create_deal(
                order_id=order_id,
                proposed_price=order.proposed_price,
                proposed_by='user',
                message=order.notes or ''
            )

        return OrderResponse(
            order_id=str(order_id),
            status="created",
            message="Order created successfully. Admin will review your proposal.",
            data={"order_id": order_id}
        )

    except Exception as e:
        return OrderResponse(
            status="error",
            message=f"Failed to create order: {str(e)}"
        )


@router.get("/versions", response_model=ListVersionsResponse)
async def get_available_versions(user_id: int = Depends(get_current_user)):
    """Get available mini app versions"""

    versions = []
    for version_key, version_info in MINI_APP_VERSIONS.items():
        versions.append({
            'id': version_key,
            'name': version_info['name'],
            'features': version_info['features']
        })

    return ListVersionsResponse(
        versions=versions,
        default_version=VersionEnum.LITE
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}
