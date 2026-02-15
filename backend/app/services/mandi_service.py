"""
Mandi Service for CRUD operations and geospatial queries on mandis.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.models.mandi import Mandi
from app.schemas import (
    MandiCreate,
    MandiUpdate,
    MandiResponse,
    MandiListResponse,
    NearbyMandiResponse,
)


class MandiService:
    """Service class for mandi operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, mandi_id: int) -> Optional[Mandi]:
        """Get a mandi by ID."""
        result = await self.db.execute(
            select(Mandi).where(Mandi.id == mandi_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name_and_district(
        self,
        name: str,
        district: str,
    ) -> Optional[Mandi]:
        """Get a mandi by name and district."""
        result = await self.db.execute(
            select(Mandi).where(
                and_(
                    Mandi.name == name,
                    Mandi.district == district,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_list(
        self,
        page: int = 1,
        page_size: int = 20,
        state: Optional[str] = None,
        district: Optional[str] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = True,
    ) -> Tuple[List[Mandi], int]:
        """
        Get paginated list of mandis with optional filters.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            state: Filter by state
            district: Filter by district
            search: Search term for name/district
            is_active: Filter by active status
        
        Returns:
            Tuple of (list of mandis, total count)
        """
        query = select(Mandi)
        count_query = select(func.count(Mandi.id))
        
        # Apply filters
        if is_active is not None:
            query = query.where(Mandi.is_active == is_active)
            count_query = count_query.where(Mandi.is_active == is_active)
        
        if state:
            query = query.where(Mandi.state == state)
            count_query = count_query.where(Mandi.state == state)
        
        if district:
            query = query.where(Mandi.district == district)
            count_query = count_query.where(Mandi.district == district)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Mandi.name.ilike(search_pattern),
                    Mandi.district.ilike(search_pattern),
                    Mandi.state.ilike(search_pattern),
                )
            )
            count_query = count_query.where(
                or_(
                    Mandi.name.ilike(search_pattern),
                    Mandi.district.ilike(search_pattern),
                    Mandi.state.ilike(search_pattern),
                )
            )
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Mandi.name)
        
        result = await self.db.execute(query)
        mandis = result.scalars().all()
        
        return list(mandis), total
    
    async def get_states(self) -> List[str]:
        """Get list of unique states."""
        result = await self.db.execute(
            select(Mandi.state)
            .distinct()
            .where(Mandi.is_active == True)
            .order_by(Mandi.state)
        )
        return [row[0] for row in result.all()]
    
    async def get_districts_by_state(self, state: str) -> List[str]:
        """Get list of districts for a state."""
        result = await self.db.execute(
            select(Mandi.district)
            .distinct()
            .where(and_(Mandi.state == state, Mandi.is_active == True))
            .order_by(Mandi.district)
        )
        return [row[0] for row in result.all()]
    
    async def get_nearby(
        self,
        latitude: Decimal,
        longitude: Decimal,
        radius_km: int = 50,
        limit: int = 10,
    ) -> List[Tuple[Mandi, float]]:
        """
        Get mandis within a radius using PostGIS geospatial queries.
        
        Args:
            latitude: User's latitude
            longitude: User's longitude
            radius_km: Search radius in kilometers
            limit: Maximum number of results
        
        Returns:
            List of tuples (mandi, distance_km)
        """
        # Use raw SQL for PostGIS distance calculation
        # ST_MakePoint creates a point, ST_Distance calculates distance in meters
        # We convert to km by dividing by 1000
        query = text("""
            SELECT 
                id, name, state, district, latitude, longitude, 
                market_type, pincode, contact_phone, is_active,
                created_at, updated_at,
                ST_Distance(
                    location,
                    ST_MakePoint(:longitude, :latitude)::geography
                ) / 1000.0 as distance_km
            FROM mandis
            WHERE is_active = true
            AND ST_DWithin(
                location,
                ST_MakePoint(:longitude, :latitude)::geography,
                :radius_meters
            )
            ORDER BY distance_km
            LIMIT :limit
        """)
        
        result = await self.db.execute(
            query,
            {
                "latitude": float(latitude),
                "longitude": float(longitude),
                "radius_meters": radius_km * 1000,
                "limit": limit,
            }
        )
        
        mandis_with_distance = []
        for row in result:
            mandi = Mandi(
                id=row.id,
                name=row.name,
                state=row.state,
                district=row.district,
                latitude=row.latitude,
                longitude=row.longitude,
                market_type=row.market_type,
                pincode=row.pincode,
                contact_phone=row.contact_phone,
                is_active=row.is_active,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            mandis_with_distance.append((mandi, row.distance_km))
        
        return mandis_with_distance
    
    async def get_nearby_python(
        self,
        latitude: Decimal,
        longitude: Decimal,
        radius_km: int = 50,
        limit: int = 10,
    ) -> List[Tuple[Mandi, float]]:
        """
        Get mandis within a radius using Python Haversine calculation.
        Fallback method if PostGIS is not available.
        
        Args:
            latitude: User's latitude
            longitude: User's longitude
            radius_km: Search radius in kilometers
            limit: Maximum number of results
        
        Returns:
            List of tuples (mandi, distance_km)
        """
        result = await self.db.execute(
            select(Mandi).where(Mandi.is_active == True)
        )
        all_mandis = result.scalars().all()
        
        # Calculate distances
        mandis_with_distance = []
        for mandi in all_mandis:
            distance = Mandi.calculate_distance(
                float(latitude),
                float(longitude),
                float(mandi.latitude),
                float(mandi.longitude),
            )
            if distance <= radius_km:
                mandis_with_distance.append((mandi, distance))
        
        # Sort by distance and limit
        mandis_with_distance.sort(key=lambda x: x[1])
        return mandis_with_distance[:limit]
    
    async def create(self, mandi_data: MandiCreate) -> Mandi:
        """Create a new mandi."""
        mandi = Mandi(
            name=mandi_data.name,
            state=mandi_data.state,
            district=mandi_data.district,
            latitude=mandi_data.latitude,
            longitude=mandi_data.longitude,
            market_type=mandi_data.market_type,
            pincode=mandi_data.pincode,
            contact_phone=mandi_data.contact_phone,
        )
        
        # Set location using PostGIS
        # This requires raw SQL to set the geography column
        self.db.add(mandi)
        await self.db.flush()
        
        # Update location with PostGIS function
        await self.db.execute(
            text("""
                UPDATE mandis 
                SET location = ST_MakePoint(:longitude, :latitude)::geography
                WHERE id = :id
            """),
            {
                "latitude": float(mandi_data.latitude),
                "longitude": float(mandi_data.longitude),
                "id": mandi.id,
            }
        )
        
        await self.db.commit()
        await self.db.refresh(mandi)
        return mandi
    
    async def update(
        self,
        mandi_id: int,
        mandi_data: MandiUpdate,
    ) -> Optional[Mandi]:
        """Update an existing mandi."""
        mandi = await self.get_by_id(mandi_id)
        if not mandi:
            return None
        
        update_data = mandi_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(mandi, field, value)
        
        # Update location if coordinates changed
        if 'latitude' in update_data or 'longitude' in update_data:
            lat = update_data.get('latitude', mandi.latitude)
            lon = update_data.get('longitude', mandi.longitude)
            await self.db.execute(
                text("""
                    UPDATE mandis 
                    SET location = ST_MakePoint(:longitude, :latitude)::geography
                    WHERE id = :id
                """),
                {
                    "latitude": float(lat),
                    "longitude": float(lon),
                    "id": mandi.id,
                }
            )
        
        mandi.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(mandi)
        return mandi
    
    async def delete(self, mandi_id: int) -> bool:
        """Delete a mandi (soft delete by setting is_active=False)."""
        mandi = await self.get_by_id(mandi_id)
        if not mandi:
            return False
        
        mandi.is_active = False
        mandi.updated_at = datetime.utcnow()
        await self.db.commit()
        return True
    
    async def bulk_create(
        self,
        mandis: List[MandiCreate],
    ) -> List[Mandi]:
        """Bulk create mandis."""
        created_mandis = []
        
        for mandi_data in mandis:
            mandi = await self.create(mandi_data)
            created_mandis.append(mandi)
        
        return created_mandis
    
    @staticmethod
    def to_response(mandi: Mandi) -> MandiResponse:
        """Convert Mandi model to response schema."""
        return MandiResponse.model_validate(mandi)
    
    @staticmethod
    def to_list_response(
        mandis: List[Mandi],
        total: int,
        page: int,
        page_size: int,
    ) -> MandiListResponse:
        """Convert list of mandis to paginated response."""
        total_pages = (total + page_size - 1) // page_size
        return MandiListResponse(
            items=[MandiService.to_response(m) for m in mandis],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    @staticmethod
    def to_nearby_response(
        mandi: Mandi,
        distance_km: float,
    ) -> NearbyMandiResponse:
        """Convert Mandi with distance to nearby response schema."""
        return NearbyMandiResponse(
            id=mandi.id,
            name=mandi.name,
            state=mandi.state,
            district=mandi.district,
            latitude=float(mandi.latitude),
            longitude=float(mandi.longitude),
            distance_km=round(distance_km, 2),
        )
