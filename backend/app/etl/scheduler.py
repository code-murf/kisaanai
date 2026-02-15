"""
APScheduler-based orchestration pipeline for data ingestion and processing.

This module defines scheduled jobs for:
- Scheduled price data scraping
- Data validation and cleaning
- Database synchronization
- Model retraining triggers
"""
import asyncio
import logging
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
from functools import wraps

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

from app.config import settings
from app.scraper.agmarknet_scraper import (
    AgmarknetScraper,
    ScraperConfig,
    ScrapedPrice,
    ScraperResult,
)


logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


def async_task(func):
    """Decorator to handle async tasks with proper error logging."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Task {func.__name__} failed: {e}", exc_info=True)
            raise
    return wrapper


# ============================================================================
# TASKS
# ============================================================================

@async_task
async def scrape_prices_task(
    state: Optional[str] = None,
    commodity: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> ScraperResult:
    """
    Task to scrape price data from AGMARKNET.
    
    Args:
        state: Filter by state
        commodity: Filter by commodity
        date_from: Start date
        date_to: End date
    
    Returns:
        ScraperResult with scraped prices
    """
    logger.info(f"Starting price scraping for state={state}, commodity={commodity}")
    
    config = ScraperConfig()
    
    async with AgmarknetScraper(config) as scraper:
        result = await scraper.scrape_prices(
            state=state,
            commodity=commodity,
            date_from=date_from,
            date_to=date_to,
        )
    
    if result.success:
        logger.info(f"Scraped {result.total_records} price records")
    else:
        logger.error(f"Scraping failed: {result.errors}")
    
    return result


def validate_prices_task(prices: List[ScrapedPrice]) -> List[ScrapedPrice]:
    """
    Task to validate scraped price data.
    
    Args:
        prices: List of scraped prices
    
    Returns:
        List of validated prices
    """
    logger.info(f"Validating {len(prices)} price records")
    
    validated = []
    invalid_count = 0
    
    for price in prices:
        # Basic validation rules
        if not price.commodity:
            invalid_count += 1
            continue
        
        if price.min_price < 0 or price.max_price < 0:
            invalid_count += 1
            continue
        
        if price.min_price > price.max_price:
            # Swap if min > max
            price.min_price, price.max_price = price.max_price, price.min_price
        
        # Ensure modal price is within range
        if price.modal_price < price.min_price:
            price.modal_price = price.min_price
        elif price.modal_price > price.max_price:
            price.modal_price = price.max_price
        
        validated.append(price)
    
    logger.info(f"Validated {len(validated)} records, rejected {invalid_count}")
    return validated


@async_task
async def sync_to_database_task(prices: List[ScrapedPrice]) -> Dict[str, Any]:
    """
    Task to sync validated prices to database.
    
    Args:
        prices: List of validated prices
    
    Returns:
        Sync result with statistics
    """
    from app.database import get_async_session
    from app.services.price_service import PriceService
    
    logger.info(f"Syncing {len(prices)} prices to database")
    
    async with get_async_session() as session:
        price_service = PriceService(session)
        
        created = 0
        updated = 0
        errors = 0
        
        for price in prices:
            try:
                # Check if price record exists
                existing = await price_service.get_price_by_date_mandi_commodity(
                    date=price.date,
                    mandi_id=price.mandi_id,
                    commodity_id=price.commodity_id,
                )
                
                if existing:
                    await price_service.update_price(
                        price_id=existing.id,
                        price_data={
                            "min_price": price.min_price,
                            "max_price": price.max_price,
                            "modal_price": price.modal_price,
                            "arrivals": price.arrivals,
                        }
                    )
                    updated += 1
                else:
                    await price_service.create_price(
                        price_data={
                            "commodity_id": price.commodity_id,
                            "mandi_id": price.mandi_id,
                            "date": price.date,
                            "min_price": price.min_price,
                            "max_price": price.max_price,
                            "modal_price": price.modal_price,
                            "arrivals": price.arrivals,
                        }
                    )
                    created += 1
            except Exception as e:
                logger.error(f"Error syncing price: {e}")
                errors += 1
        
        result = {
            "created": created,
            "updated": updated,
            "errors": errors,
            "total": len(prices),
        }
        
        logger.info(f"Sync complete: {result}")
        return result


@async_task
async def trigger_model_retraining_task(commodity_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Task to trigger model retraining.
    
    Args:
        commodity_id: Optional commodity ID to retrain specific model
    
    Returns:
        Retraining result
    """
    from app.ml.xgboost_forecast import XGBoostForecaster
    from app.ml.feature_engineering import FeatureEngineer
    
    logger.info(f"Triggering model retraining for commodity_id={commodity_id}")
    
    try:
        feature_engineer = FeatureEngineer()
        forecaster = XGBoostForecaster()
        
        # Prepare features
        features = await feature_engineer.prepare_training_data(commodity_id)
        
        # Train model
        metrics = forecaster.train(features)
        
        # Save model
        forecaster.save_model()
        
        result = {
            "success": True,
            "commodity_id": commodity_id,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        logger.info(f"Model retraining complete: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Model retraining failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


# ============================================================================
# FLOWS (Combined Tasks)
# ============================================================================

@async_task
async def daily_price_ingestion_flow(
    state: Optional[str] = None,
    commodity: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Complete flow for daily price data ingestion.
    
    1. Scrape prices
    2. Validate data
    3. Sync to database
    4. Trigger retraining if needed
    
    Args:
        state: Filter by state
        commodity: Filter by commodity
    
    Returns:
        Flow execution result
    """
    logger.info("Starting daily price ingestion flow")
    
    # Step 1: Scrape
    scrape_result = await scrape_prices_task(
        state=state,
        commodity=commodity,
        date_from=date.today(),
        date_to=date.today(),
    )
    
    if not scrape_result.success:
        return {
            "success": False,
            "error": "Scraping failed",
            "details": scrape_result.errors,
        }
    
    # Step 2: Validate
    validated_prices = validate_prices_task(scrape_result.prices)
    
    # Step 3: Sync to database
    sync_result = await sync_to_database_task(validated_prices)
    
    # Step 4: Trigger retraining (async, non-blocking)
    # Only retrain if we have significant new data
    if sync_result.get("created", 0) > 100:
        scheduler.add_job(
            trigger_model_retraining_task,
            kwargs={"commodity_id": None},
            id="model_retraining",
            replace_existing=True,
        )
    
    return {
        "success": True,
        "scraped": scrape_result.total_records,
        "validated": len(validated_prices),
        "synced": sync_result,
    }


@async_task
async def weekly_full_sync_flow() -> Dict[str, Any]:
    """
    Weekly flow for full data synchronization.
    
    Returns:
        Flow execution result
    """
    logger.info("Starting weekly full sync flow")
    
    # Scrape last 7 days
    date_from = date.today() - timedelta(days=7)
    
    scrape_result = await scrape_prices_task(
        date_from=date_from,
        date_to=date.today(),
    )
    
    if not scrape_result.success:
        return {
            "success": False,
            "error": "Scraping failed",
        }
    
    validated_prices = validate_prices_task(scrape_result.prices)
    sync_result = await sync_to_database_task(validated_prices)
    
    # Always retrain on weekly sync
    await trigger_model_retraining_task()
    
    return {
        "success": True,
        "synced": sync_result,
    }


# ============================================================================
# SCHEDULER SETUP
# ============================================================================

def setup_scheduler() -> AsyncIOScheduler:
    """
    Set up and configure the APScheduler.
    
    Returns:
        Configured scheduler instance
    """
    global scheduler
    
    jobstores = {
        "default": MemoryJobStore(),
    }
    
    executors = {
        "default": ThreadPoolExecutor(20),
    }
    
    job_defaults = {
        "coalesce": True,
        "max_instances": 3,
        "misfire_grace_time": 3600,  # 1 hour
    }
    
    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone="Asia/Kolkata",
    )
    
    # Add scheduled jobs
    
    # Daily price ingestion at 6 AM IST
    scheduler.add_job(
        daily_price_ingestion_flow,
        trigger=CronTrigger(hour=6, minute=0),
        id="daily_price_ingestion",
        name="Daily Price Ingestion",
        replace_existing=True,
    )
    
    # Weekly full sync on Sunday at 2 AM IST
    scheduler.add_job(
        weekly_full_sync_flow,
        trigger=CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="weekly_full_sync",
        name="Weekly Full Sync",
        replace_existing=True,
    )
    
    # Hourly price updates during market hours (9 AM - 5 PM IST)
    scheduler.add_job(
        daily_price_ingestion_flow,
        trigger=CronTrigger(hour="9-17", minute=30),
        id="hourly_price_update",
        name="Hourly Price Update",
        replace_existing=True,
    )
    
    logger.info("Scheduler configured with jobs:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name}: {job.trigger}")
    
    return scheduler


def start_scheduler():
    """Start the scheduler."""
    global scheduler
    
    if scheduler is None:
        scheduler = setup_scheduler()
    
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    global scheduler
    
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler shutdown complete")


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """Get the current scheduler instance."""
    return scheduler


# ============================================================================
# MANUAL TRIGGERS
# ============================================================================

async def run_price_ingestion_now(
    state: Optional[str] = None,
    commodity: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Manually trigger price ingestion flow.
    
    Args:
        state: Filter by state
        commodity: Filter by commodity
    
    Returns:
        Flow execution result
    """
    return await daily_price_ingestion_flow(state=state, commodity=commodity)


async def run_model_retraining_now(
    commodity_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Manually trigger model retraining.
    
    Args:
        commodity_id: Optional commodity ID
    
    Returns:
        Retraining result
    """
    return await trigger_model_retraining_task(commodity_id=commodity_id)
