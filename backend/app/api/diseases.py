"""
Disease Detection API Router with S3 and CloudWatch integration.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime
import time
import logging
from typing import Optional

from app.services.disease_service import DiseaseService
from app.services.s3_service import s3_service
from app.services.cloudwatch_service import cloudwatch_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diseases", tags=["diseases"])

class DiseaseResponse(BaseModel):
    disease_name: str
    confidence: float
    treatment: str
    severity: str
    image_url: Optional[str] = None
    s3_key: Optional[str] = None
    storage_mode: Optional[str] = None
    timestamp: Optional[str] = None

@router.post("/diagnose", response_model=DiseaseResponse)
async def diagnose_plant(request: Request, file: UploadFile = File(...)):
    """
    Diagnose plant disease from an uploaded image.
    Uploads image to S3 and records CloudWatch metrics.
    """
    start_time = time.time()
    service = DiseaseService()
    upload_result = {'success': False, 'error': None, 'url': None, 'key': None, 'storage': None}
    
    try:
        contents = await file.read()
        
        # Upload to S3
        upload_result = await s3_service.upload_image(
            contents,
            file.filename,
            file.content_type or 'image/jpeg'
        )

        if upload_result.get('error'):
            logger.warning(
                "Primary storage upload failed, using %s fallback: %s",
                upload_result.get('storage') or 'no',
                upload_result.get('error'),
            )
            await cloudwatch_service.put_metric(
                'StorageWarnings', 1,
                dimensions=[
                    {'Name': 'WarningType', 'Value': 'S3UploadFailed'},
                    {'Name': 'Endpoint', 'Value': 'diseases'}
                ]
            )
        
        # ML inference
        prediction = await service.predict(contents, file.filename)
        
        # Record metrics
        latency = (time.time() - start_time) * 1000
        await cloudwatch_service.put_metrics_batch([
            {'name': 'DiseaseAPILatency', 'value': latency, 'unit': 'Milliseconds'},
            {'name': 'DiseaseAPIRequests', 'value': 1}
        ])
        
        logger.info(
            "Disease diagnosis completed in %.2fms, storage_key=%s",
            latency,
            upload_result.get('key') if upload_result.get('success') else 'unavailable',
        )

        image_url = upload_result.get('url') if upload_result.get('success') else None
        if image_url and image_url.startswith("/"):
            image_url = f"{str(request.base_url).rstrip('/')}{image_url}"
        
        return DiseaseResponse(
            disease_name=prediction.disease_name,
            confidence=prediction.confidence,
            treatment=prediction.treatment,
            severity=prediction.severity,
            image_url=image_url,
            s3_key=upload_result.get('key') if upload_result.get('success') else None,
            storage_mode=upload_result.get('storage') if upload_result.get('success') else None,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except RuntimeError as e:
        await cloudwatch_service.put_metric(
            'APIErrors', 1,
            dimensions=[
                {'Name': 'ErrorType', 'Value': 'RuntimeError'},
                {'Name': 'Endpoint', 'Value': 'diseases'}
            ]
        )
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Disease diagnosis failed")
        await cloudwatch_service.put_metric(
            'APIErrors', 1,
            dimensions=[
                {'Name': 'ErrorType', 'Value': type(e).__name__},
                {'Name': 'Endpoint', 'Value': 'diseases'}
            ]
        )
        raise HTTPException(status_code=500, detail=str(e))
