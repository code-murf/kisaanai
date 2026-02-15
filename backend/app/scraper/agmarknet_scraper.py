"""
AGMARKNET scraper for agricultural commodity price data.

Scrapes price data from the official AGMARKNET portal (https://agmarknet.gov.in)
and related government data sources.
"""
import asyncio
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import logging

import aiohttp
from bs4 import BeautifulSoup
import pandas as pd

from app.config import settings


logger = logging.getLogger(__name__)


@dataclass
class ScrapedPrice:
    """Scraped price data point."""
    commodity_name: str
    mandi_name: str
    mandi_state: str
    mandi_district: str
    price_date: date
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    modal_price: Optional[float] = None
    arrival_qty: Optional[float] = None
    unit: str = "Quintal"
    source: str = "AGMARKNET"


@dataclass
class ScraperConfig:
    """Configuration for the scraper."""
    base_url: str = "https://agmarknet.gov.in"
    api_url: str = "https://agmarknet.gov.in/SearchCmmMkt"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 2.0
    rate_limit_delay: float = 1.0
    concurrent_requests: int = 5
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


@dataclass
class ScraperResult:
    """Result of a scraping operation."""
    success: bool
    prices: List[ScrapedPrice] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    total_records: int = 0
    scraped_at: datetime = field(default_factory=datetime.utcnow)


class AgmarknetScraper:
    """
    Scraper for AGMARKNET agricultural price data.
    
    Uses the AGMARKNET portal's data API to fetch commodity prices
    from various mandis across India.
    """
    
    # Commodity category mapping
    COMMODITY_CATEGORIES = {
        "Cereals": ["Paddy", "Wheat", "Maize", "Bajra", "Jowar", "Ragi"],
        "Pulses": ["Gram", "Tur", "Moong", "Urad", "Lentil", "Arhar"],
        "Vegetables": ["Onion", "Potato", "Tomato", "Brinjal", "Cabbage", "Cauliflower"],
        "Fruits": ["Banana", "Mango", "Apple", "Orange", "Grapes", "Guava"],
        "Spices": ["Turmeric", "Chilli", "Coriander", "Cumin", "Garlic", "Ginger"],
        "Oilseeds": ["Groundnut", "Mustard", "Soyabean", "Sunflower", "Sesamum"],
        "Others": ["Cotton", "Jute", "Sugarcane", "Tea", "Coffee"],
    }
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(self.config.concurrent_requests)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def initialize(self):
        """Initialize the scraper session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": self.config.user_agent,
                    "Accept": "application/json, text/html, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                }
            )
    
    async def close(self):
        """Close the scraper session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def scrape_prices(
        self,
        state: Optional[str] = None,
        commodity: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> ScraperResult:
        """
        Scrape price data from AGMARKNET.
        
        Args:
            state: Filter by state name
            commodity: Filter by commodity name
            date_from: Start date for price data
            date_to: End date for price data
        
        Returns:
            ScraperResult with scraped prices
        """
        await self.initialize()
        
        result = ScraperResult(success=False)
        
        try:
            # Set default date range
            if not date_to:
                date_to = date.today()
            if not date_from:
                date_from = date_to - timedelta(days=7)
            
            # Get prices for the specified parameters
            prices = await self._fetch_prices(
                state=state,
                commodity=commodity,
                date_from=date_from,
                date_to=date_to,
            )
            
            result.prices = prices
            result.total_records = len(prices)
            result.success = True
            logger.info(f"Scraped {len(prices)} price records")
            
        except Exception as e:
            result.errors.append(str(e))
            logger.error(f"Scraping failed: {e}")
        
        return result
    
    async def _fetch_prices(
        self,
        state: Optional[str],
        commodity: Optional[str],
        date_from: date,
        date_to: date,
    ) -> List[ScrapedPrice]:
        """Fetch prices from AGMARKNET API."""
        prices = []
        
        # Build request parameters
        params = {
            "Dt": date_to.strftime("%d-%b-%Y"),
            "Commodity": commodity or "",
            "State": state or "",
        }
        
        try:
            async with self._semaphore:
                await asyncio.sleep(self.config.rate_limit_delay)
                
                # Try the API endpoint first
                data = await self._fetch_api_data(params)
                
                if data:
                    prices = self._parse_api_response(data)
                else:
                    # Fallback to HTML scraping
                    prices = await self._scrape_html_pages(
                        state=state,
                        commodity=commodity,
                        date_from=date_from,
                        date_to=date_to,
                    )
        
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
        
        return prices
    
    async def _fetch_api_data(self, params: Dict[str, str]) -> Optional[List[Dict]]:
        """Fetch data from AGMARKNET API."""
        url = f"{self.config.api_url}/GetData"
        
        for attempt in range(self.config.max_retries):
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        content_type = response.headers.get("Content-Type", "")
                        if "json" in content_type:
                            return await response.json()
                        else:
                            text = await response.text()
                            return self._parse_json_from_html(text)
            except aiohttp.ClientError as e:
                logger.warning(f"API request failed (attempt {attempt + 1}): {e}")
                await asyncio.sleep(self.config.retry_delay)
        
        return None
    
    def _parse_json_from_html(self, html: str) -> Optional[List[Dict]]:
        """Parse JSON data embedded in HTML response."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Look for JSON in script tags or data attributes
            scripts = soup.find_all("script")
            for script in scripts:
                if script.string and "var data" in script.string:
                    # Extract JSON from JavaScript variable
                    match = re.search(r"var\s+data\s*=\s*(\[.*?\]);", script.string, re.DOTALL)
                    if match:
                        return json.loads(match.group(1))
            
            # Look for table data
            table = soup.find("table", {"id": "ContentPlaceHolder1_GridView1"})
            if table:
                return self._parse_table_to_json(table)
                
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
        
        return None
    
    def _parse_table_to_json(self, table) -> List[Dict]:
        """Parse HTML table to JSON data."""
        data = []
        headers = []
        
        # Get headers
        header_row = table.find("tr")
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]
        
        # Get data rows
        for row in table.find_all("tr")[1:]:  # Skip header
            cells = row.find_all("td")
            if cells:
                row_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        row_data[headers[i]] = cell.get_text(strip=True)
                if row_data:
                    data.append(row_data)
        
        return data
    
    def _parse_api_response(self, data: List[Dict]) -> List[ScrapedPrice]:
        """Parse API response into ScrapedPrice objects."""
        prices = []
        
        for item in data:
            try:
                price = ScrapedPrice(
                    commodity_name=item.get("Commodity", "").strip(),
                    mandi_name=item.get("Market", "").strip(),
                    mandi_state=item.get("State", "").strip(),
                    mandi_district=item.get("District", "").strip(),
                    price_date=self._parse_date(item.get("Arrival_Date", "")),
                    min_price=self._parse_float(item.get("Min_x0020_Price")),
                    max_price=self._parse_float(item.get("Max_x0020_Price")),
                    modal_price=self._parse_float(item.get("Modal_x0020_Price")),
                    arrival_qty=self._parse_float(item.get("Arrival")),
                    unit="Quintal",
                    source="AGMARKNET",
                )
                
                if price.modal_price and price.modal_price > 0:
                    prices.append(price)
                    
            except Exception as e:
                logger.warning(f"Error parsing price item: {e}")
                continue
        
        return prices
    
    async def _scrape_html_pages(
        self,
        state: Optional[str],
        commodity: Optional[str],
        date_from: date,
        date_to: date,
    ) -> List[ScrapedPrice]:
        """Scrape prices from HTML pages as fallback."""
        prices = []
        
        # Construct search URL
        search_url = f"{self.config.base_url}/SearchCmmMkt"
        
        params = {
            "Commodity": commodity or "All",
            "State": state or "All",
            "Date": date_to.strftime("%d-%b-%Y"),
        }
        
        try:
            async with self.session.get(search_url, params=params) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # Find the price table
                    table = soup.find("table", {"class": "table"})
                    if not table:
                        table = soup.find("table", {"id": re.compile("GridView")})
                    
                    if table:
                        prices = self._extract_prices_from_table(table)
        
        except Exception as e:
            logger.error(f"HTML scraping failed: {e}")
        
        return prices
    
    def _extract_prices_from_table(self, table) -> List[ScrapedPrice]:
        """Extract price data from HTML table."""
        prices = []
        rows = table.find_all("tr")
        
        for row in rows[1:]:  # Skip header
            cells = row.find_all("td")
            if len(cells) >= 8:
                try:
                    price = ScrapedPrice(
                        commodity_name=cells[0].get_text(strip=True),
                        mandi_name=cells[1].get_text(strip=True),
                        mandi_state=cells[2].get_text(strip=True),
                        mandi_district=cells[3].get_text(strip=True),
                        price_date=self._parse_date(cells[4].get_text(strip=True)),
                        arrival_qty=self._parse_float(cells[5].get_text(strip=True)),
                        min_price=self._parse_float(cells[6].get_text(strip=True)),
                        max_price=self._parse_float(cells[7].get_text(strip=True)),
                        modal_price=self._parse_float(cells[8].get_text(strip=True)) if len(cells) > 8 else None,
                        unit="Quintal",
                        source="AGMARKNET",
                    )
                    
                    if price.modal_price and price.modal_price > 0:
                        prices.append(price)
                        
                except Exception as e:
                    logger.warning(f"Error extracting row: {e}")
                    continue
        
        return prices
    
    @staticmethod
    def _parse_date(date_str: str) -> Optional[date]:
        """Parse date from various formats."""
        if not date_str:
            return None
        
        formats = [
            "%d-%b-%Y",
            "%d-%B-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d %b %Y",
            "%d %B %Y",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def _parse_float(value: Any) -> Optional[float]:
        """Parse float from various formats."""
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove commas, spaces, and currency symbols
            cleaned = re.sub(r"[^\d.]", "", value.strip())
            if cleaned:
                try:
                    return float(cleaned)
                except ValueError:
                    pass
        
        return None
    
    async def scrape_commodities_list(self) -> List[Dict[str, str]]:
        """Scrape the list of available commodities."""
        commodities = []
        
        # Use predefined list for reliability
        for category, items in self.COMMODITY_CATEGORIES.items():
            for item in items:
                commodities.append({
                    "name": item,
                    "category": category,
                    "source": "AGMARKNET",
                })
        
        return commodities
    
    async def scrape_states_list(self) -> List[Dict[str, str]]:
        """Scrape the list of available states."""
        states = [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
            "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh",
            "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
            "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha",
            "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
            "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
            "Delhi", "Jammu and Kashmir", "Ladakh",
        ]
        
        return [{"name": state, "source": "AGMARKNET"} for state in states]
    
    def to_dataframe(self, prices: List[ScrapedPrice]) -> pd.DataFrame:
        """Convert scraped prices to pandas DataFrame."""
        if not prices:
            return pd.DataFrame()
        
        data = [
            {
                "commodity_name": p.commodity_name,
                "mandi_name": p.mandi_name,
                "mandi_state": p.mandi_state,
                "mandi_district": p.mandi_district,
                "price_date": p.price_date,
                "min_price": p.min_price,
                "max_price": p.max_price,
                "modal_price": p.modal_price,
                "arrival_qty": p.arrival_qty,
                "unit": p.unit,
                "source": p.source,
            }
            for p in prices
        ]
        
        df = pd.DataFrame(data)
        df["price_date"] = pd.to_datetime(df["price_date"])
        
        return df
    
    async def save_to_csv(
        self,
        prices: List[ScrapedPrice],
        output_path: Path,
    ) -> Path:
        """Save scraped prices to CSV file."""
        df = self.to_dataframe(prices)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(prices)} records to {output_path}")
        return output_path
    
    async def save_to_json(
        self,
        prices: List[ScrapedPrice],
        output_path: Path,
    ) -> Path:
        """Save scraped prices to JSON file."""
        data = [
            {
                "commodity_name": p.commodity_name,
                "mandi_name": p.mandi_name,
                "mandi_state": p.mandi_state,
                "mandi_district": p.mandi_district,
                "price_date": p.price_date.isoformat() if p.price_date else None,
                "min_price": p.min_price,
                "max_price": p.max_price,
                "modal_price": p.modal_price,
                "arrival_qty": p.arrival_qty,
                "unit": p.unit,
                "source": p.source,
            }
            for p in prices
        ]
        
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved {len(prices)} records to {output_path}")
        return output_path


async def run_scraper(
    state: Optional[str] = None,
    commodity: Optional[str] = None,
    output_dir: Optional[Path] = None,
) -> ScraperResult:
    """
    Run the AGMARKNET scraper.
    
    Convenience function to run the scraper with default settings.
    """
    config = ScraperConfig()
    
    async with AgmarknetScraper(config) as scraper:
        result = await scraper.scrape_prices(
            state=state,
            commodity=commodity,
        )
        
        if result.success and result.prices and output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            await scraper.save_to_csv(
                result.prices,
                output_dir / f"prices_{timestamp}.csv",
            )
            await scraper.save_to_json(
                result.prices,
                output_dir / f"prices_{timestamp}.json",
            )
        
        return result


if __name__ == "__main__":
    # Example usage
    asyncio.run(run_scraper(
        state="Maharashtra",
        commodity="Onion",
        output_dir=Path("data/raw"),
    ))
