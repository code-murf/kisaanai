"""
Commodity API endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.commodity_service import CommodityService
from app.schemas import (
    CommodityCreate,
    CommodityUpdate,
    CommodityResponse,
    CommodityListResponse,
    SuccessResponse,
    ErrorDetail,
)

router = APIRouter(prefix="/commodities", tags=["Commodities"])


@router.get(
    "",
    response_model=CommodityListResponse,
    summary="List commodities",
    description="Get paginated list of commodities with optional filters.",
)
async def list_commodities(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search term"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of commodities."""
    commodity_service = CommodityService(db)
    commodities, total = await commodity_service.get_list(
        page=page,
        page_size=page_size,
        category=category,
        search=search,
        is_active=is_active,
    )
    return CommodityService.to_list_response(
        commodities, total, page, page_size
    )


@router.get(
    "/categories",
    response_model=List[str],
    summary="Get commodity categories",
    description="Get list of all unique commodity categories.",
)
async def get_categories(
    db: AsyncSession = Depends(get_db),
):
    """Get all commodity categories."""
    commodity_service = CommodityService(db)
    return await commodity_service.get_categories()


@router.get(
    "/{commodity_id}",
    response_model=CommodityResponse,
    summary="Get commodity by ID",
    description="Get detailed information about a specific commodity.",
    responses={
        404: {"model": ErrorDetail, "description": "Commodity not found"},
    },
)
async def get_commodity(
    commodity_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a commodity by ID."""
    commodity_service = CommodityService(db)
    commodity = await commodity_service.get_by_id(commodity_id)
    
    if not commodity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commodity not found",
        )
    
    return CommodityService.to_response(commodity)


@router.post(
    "",
    response_model=CommodityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create commodity",
    description="Create a new commodity.",
    responses={
        201: {"description": "Commodity created successfully"},
        400: {"model": ErrorDetail, "description": "Commodity with this name already exists"},
    },
)
async def create_commodity(
    commodity_data: CommodityCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new commodity."""
    commodity_service = CommodityService(db)
    
    try:
        commodity = await commodity_service.create(commodity_data)
        return CommodityService.to_response(commodity)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/bulk",
    response_model=List[CommodityResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create commodities",
    description="Create multiple commodities at once.",
)
async def bulk_create_commodities(
    commodities: List[CommodityCreate],
    db: AsyncSession = Depends(get_db),
):
    """Bulk create commodities."""
    commodity_service = CommodityService(db)
    created = await commodity_service.bulk_create(commodities)
    return [CommodityService.to_response(c) for c in created]


@router.patch(
    "/{commodity_id}",
    response_model=CommodityResponse,
    summary="Update commodity",
    description="Update an existing commodity.",
    responses={
        200: {"description": "Commodity updated successfully"},
        404: {"model": ErrorDetail, "description": "Commodity not found"},
    },
)
async def update_commodity(
    commodity_id: int,
    commodity_data: CommodityUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a commodity."""
    commodity_service = CommodityService(db)
    
    try:
        commodity = await commodity_service.update(commodity_id, commodity_data)
        
        if not commodity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Commodity not found",
            )
        
        return CommodityService.to_response(commodity)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{commodity_id}",
    response_model=SuccessResponse,
    summary="Delete commodity",
    description="Soft delete a commodity (sets is_active=False).",
    responses={
        200: {"description": "Commodity deleted successfully"},
        404: {"model": ErrorDetail, "description": "Commodity not found"},
    },
)
async def delete_commodity(
    commodity_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a commodity (soft delete)."""
    commodity_service = CommodityService(db)
    success = await commodity_service.delete(commodity_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Commodity not found",
        )
    
    return SuccessResponse(message="Commodity deleted successfully")
