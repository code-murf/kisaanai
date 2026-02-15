"""
Mandi API endpoints.
"""
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.mandi_service import MandiService
from app.schemas import (
    MandiCreate,
    MandiUpdate,
    MandiResponse,
    MandiListResponse,
    NearbyMandiResponse,
    NearbyMandiRequest,
    SuccessResponse,
    ErrorDetail,
)

router = APIRouter(prefix="/mandis", tags=["Mandis"])


@router.get(
    "",
    response_model=MandiListResponse,
    summary="List mandis",
    description="Get paginated list of mandis with optional filters.",
)
async def list_mandis(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    state: Optional[str] = Query(None, description="Filter by state"),
    district: Optional[str] = Query(None, description="Filter by district"),
    search: Optional[str] = Query(None, description="Search term"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of mandis."""
    mandi_service = MandiService(db)
    mandis, total = await mandi_service.get_list(
        page=page,
        page_size=page_size,
        state=state,
        district=district,
        search=search,
        is_active=is_active,
    )
    return MandiService.to_list_response(
        mandis, total, page, page_size
    )


@router.get(
    "/states",
    response_model=List[str],
    summary="Get states",
    description="Get list of all unique states.",
)
async def get_states(
    db: AsyncSession = Depends(get_db),
):
    """Get all states."""
    mandi_service = MandiService(db)
    return await mandi_service.get_states()


@router.get(
    "/states/{state}/districts",
    response_model=List[str],
    summary="Get districts by state",
    description="Get list of districts for a specific state.",
)
async def get_districts_by_state(
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Get districts by state."""
    mandi_service = MandiService(db)
    return await mandi_service.get_districts_by_state(state)


@router.post(
    "/nearby",
    response_model=List[NearbyMandiResponse],
    summary="Find nearby mandis",
    description="Find mandis within a specified radius of given coordinates.",
)
async def find_nearby_mandis(
    request: NearbyMandiRequest,
    use_postgis: bool = Query(True, description="Use PostGIS for geospatial queries"),
    db: AsyncSession = Depends(get_db),
):
    """Find nearby mandis using geospatial queries."""
    mandi_service = MandiService(db)
    
    if use_postgis:
        mandis_with_distance = await mandi_service.get_nearby(
            latitude=request.latitude,
            longitude=request.longitude,
            radius_km=request.radius_km,
            limit=request.limit,
        )
    else:
        mandis_with_distance = await mandi_service.get_nearby_python(
            latitude=request.latitude,
            longitude=request.longitude,
            radius_km=request.radius_km,
            limit=request.limit,
        )
    
    return [
        MandiService.to_nearby_response(mandi, distance)
        for mandi, distance in mandis_with_distance
    ]


@router.get(
    "/{mandi_id}",
    response_model=MandiResponse,
    summary="Get mandi by ID",
    description="Get detailed information about a specific mandi.",
    responses={
        404: {"model": ErrorDetail, "description": "Mandi not found"},
    },
)
async def get_mandi(
    mandi_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a mandi by ID."""
    mandi_service = MandiService(db)
    mandi = await mandi_service.get_by_id(mandi_id)
    
    if not mandi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mandi not found",
        )
    
    return MandiService.to_response(mandi)


@router.post(
    "",
    response_model=MandiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create mandi",
    description="Create a new mandi.",
    responses={
        201: {"description": "Mandi created successfully"},
        400: {"model": ErrorDetail, "description": "Mandi already exists"},
    },
)
async def create_mandi(
    mandi_data: MandiCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new mandi."""
    mandi_service = MandiService(db)
    
    try:
        mandi = await mandi_service.create(mandi_data)
        return MandiService.to_response(mandi)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/bulk",
    response_model=List[MandiResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create mandis",
    description="Create multiple mandis at once.",
)
async def bulk_create_mandis(
    mandis: List[MandiCreate],
    db: AsyncSession = Depends(get_db),
):
    """Bulk create mandis."""
    mandi_service = MandiService(db)
    created = await mandi_service.bulk_create(mandis)
    return [MandiService.to_response(m) for m in created]


@router.patch(
    "/{mandi_id}",
    response_model=MandiResponse,
    summary="Update mandi",
    description="Update an existing mandi.",
    responses={
        200: {"description": "Mandi updated successfully"},
        404: {"model": ErrorDetail, "description": "Mandi not found"},
    },
)
async def update_mandi(
    mandi_id: int,
    mandi_data: MandiUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a mandi."""
    mandi_service = MandiService(db)
    
    try:
        mandi = await mandi_service.update(mandi_id, mandi_data)
        
        if not mandi:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mandi not found",
            )
        
        return MandiService.to_response(mandi)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{mandi_id}",
    response_model=SuccessResponse,
    summary="Delete mandi",
    description="Soft delete a mandi (sets is_active=False).",
    responses={
        200: {"description": "Mandi deleted successfully"},
        404: {"model": ErrorDetail, "description": "Mandi not found"},
    },
)
async def delete_mandi(
    mandi_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a mandi (soft delete)."""
    mandi_service = MandiService(db)
    success = await mandi_service.delete(mandi_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mandi not found",
        )
    
    return SuccessResponse(message="Mandi deleted successfully")
