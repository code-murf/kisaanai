"""
Disease Detection API Router with S3 and CloudWatch integration.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from datetime import datetime
import time
import logging

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
    image_url: str = None
    s3_key: str = None
    timestamp: str = None

@router.post("/diagnose", response_model=DiseaseResponse)
async def diagnose_plant(file: UploadFile = File(...)):
    """
    Diagnose plant disease from an uploaded image.
    Uploads image to S3 and records CloudWatch metrics.
    """
    start_time = time.time()
    service = DiseaseService()
    
    try:
        contents = await file.read()
        
        # Upload to S3
        s3_result = await s3_service.upload_image(
            contents,
            file.filename,
            file.content_type or 'image/jpeg'
        )
        
        if not s3_result['success']:
            logger.error(f"S3 upload failed: {s3_result.get('error')}")
            await cloudwatch_service.put_metric(
                'APIErrors', 1,
                dimensions=[
                    {'Name': 'ErrorType', 'Value': 'S3UploadFailed'},
                    {'Name': 'Endpoint', 'Value': 'diseases'}
                ]
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload image to storage: {s3_result.get('error')}"
            )
        
        # ML inference
        prediction = await service.predict(contents, file.filename)
        
        # Record metrics
        latency = (time.time() - start_time) * 1000
        await cloudwatch_service.put_metrics_batch([
            {'name': 'DiseaseAPILatency', 'value': latency, 'unit': 'Milliseconds'},
            {'name': 'DiseaseAPIRequests', 'value': 1}
        ])
        
        logger.info(f"Disease diagnosis completed in {latency:.2f}ms, S3 key: {s3_result['key']}")
        
        return DiseaseResponse(
            disease_name=prediction.disease_name,
            confidence=prediction.confidence,
            treatment=prediction.treatment,
            severity=prediction.severity,
            image_url=s3_result.get('url'),
            s3_key=s3_result.get('key'),
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
