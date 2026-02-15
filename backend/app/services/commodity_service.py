"""
Commodity Service for CRUD operations on commodities.
"""
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commodity import Commodity
from app.schemas import (
    CommodityCreate,
    CommodityUpdate,
    CommodityResponse,
    CommodityListResponse,
)


class CommodityService:
    """Service class for commodity operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, commodity_id: int) -> Optional[Commodity]:
        """Get a commodity by ID."""
        result = await self.db.execute(
            select(Commodity).where(Commodity.id == commodity_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Commodity]:
        """Get a commodity by name."""
        result = await self.db.execute(
            select(Commodity).where(Commodity.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = True,
    ) -> Tuple[List[Commodity], int]:
        """
        Get paginated list of commodities with optional filters.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            category: Filter by category
            search: Search term for name/description
            is_active: Filter by active status
        
        Returns:
            Tuple of (list of commodities, total count)
        """
        query = select(Commodity)
        count_query = select(func.count(Commodity.id))
        
        # Apply filters
        if is_active is not None:
            query = query.where(Commodity.is_active == is_active)
            count_query = count_query.where(Commodity.is_active == is_active)
        
        if category:
            query = query.where(Commodity.category == category)
            count_query = count_query.where(Commodity.category == category)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Commodity.name.ilike(search_pattern),
                    Commodity.description.ilike(search_pattern),
                )
            )
            count_query = count_query.where(
                or_(
                    Commodity.name.ilike(search_pattern),
                    Commodity.description.ilike(search_pattern),
                )
            )
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Commodity.name)
        
        result = await self.db.execute(query)
        commodities = result.scalars().all()
        
        return list(commodities), total
    
    async def get_categories(self) -> List[str]:
        """Get list of unique commodity categories."""
        result = await self.db.execute(
            select(Commodity.category)
            .distinct()
            .where(Commodity.is_active == True)
            .order_by(Commodity.category)
        )
        return [row[0] for row in result.all()]
    
    async def create(self, commodity_data: CommodityCreate) -> Commodity:
        """Create a new commodity."""
        commodity = Commodity(
            name=commodity_data.name,
            category=commodity_data.category,
            unit=commodity_data.unit,
            description=commodity_data.description,
        )
        self.db.add(commodity)
        await self.db.commit()
        await self.db.refresh(commodity)
        return commodity
    
    async def update(
        self,
        commodity_id: int,
        commodity_data: CommodityUpdate,
    ) -> Optional[Commodity]:
        """Update an existing commodity."""
        commodity = await self.get_by_id(commodity_id)
        if not commodity:
            return None
        
        update_data = commodity_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(commodity, field, value)
        
        commodity.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(commodity)
        return commodity
    
    async def delete(self, commodity_id: int) -> bool:
        """Delete a commodity (soft delete by setting is_active=False)."""
        commodity = await self.get_by_id(commodity_id)
        if not commodity:
            return False
        
        commodity.is_active = False
        commodity.updated_at = datetime.utcnow()
        await self.db.commit()
        return True
    
    async def hard_delete(self, commodity_id: int) -> bool:
        """Permanently delete a commodity."""
        commodity = await self.get_by_id(commodity_id)
        if not commodity:
            return False
        
        await self.db.delete(commodity)
        await self.db.commit()
        return True
    
    async def bulk_create(
        self,
        commodities: List[CommodityCreate],
    ) -> List[Commodity]:
        """Bulk create commodities."""
        commodity_objects = [
            Commodity(
                name=c.name,
                category=c.category,
                unit=c.unit,
                description=c.description,
            )
            for c in commodities
        ]
        self.db.add_all(commodity_objects)
        await self.db.commit()
        
        for obj in commodity_objects:
            await self.db.refresh(obj)
        
        return commodity_objects
    
    @staticmethod
    def to_response(commodity: Commodity) -> CommodityResponse:
        """Convert Commodity model to response schema."""
        return CommodityResponse.model_validate(commodity)
    
    @staticmethod
    def to_list_response(
        commodities: List[Commodity],
        total: int,
        page: int,
        page_size: int,
    ) -> CommodityListResponse:
        """Convert list of commodities to paginated response."""
        total_pages = (total + page_size - 1) // page_size
        return CommodityListResponse(
            items=[CommodityService.to_response(c) for c in commodities],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
