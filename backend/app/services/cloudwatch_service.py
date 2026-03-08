"""
Amazon CloudWatch Service for KisaanAI.

Handles application monitoring, logging, and metrics.
"""
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
import logging
from datetime import datetime
from typing import Optional, Dict, List
from app.config import settings

logger = logging.getLogger(__name__)


class CloudWatchService:
    """
    Amazon CloudWatch service for monitoring and logging.
    
    Usage:
        cw = CloudWatchService()
        await cw.put_metric('APIRequests', 1)
        await cw.log_event('application', 'User logged in')
    """
    
    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: Optional[str] = None,
        namespace: str = 'KisaanAI'
    ):
        self.aws_access_key_id = aws_access_key_id or settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = aws_secret_access_key or settings.AWS_SECRET_ACCESS_KEY
        self.aws_region = aws_region or settings.AWS_REGION
        self.namespace = namespace
        self._client = None
        self._logs_client = None
        # Keep CloudWatch calls non-blocking in constrained/offline environments.
        self._boto_config = Config(
            connect_timeout=0.2,
            read_timeout=0.2,
            retries={"max_attempts": 0},
        )
    
    @property
    def client(self):
        """Lazy-initialize CloudWatch client."""
        if self._client is None:
            self._client = boto3.client(
                'cloudwatch',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region,
                config=self._boto_config,
            )
        return self._client
    
    @property
    def logs_client(self):
        """Lazy-initialize CloudWatch Logs client."""
        if self._logs_client is None:
            self._logs_client = boto3.client(
                'logs',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region,
                config=self._boto_config,
            )
        return self._logs_client
    
    def is_configured(self) -> bool:
        """Check if AWS credentials are available."""
        return bool(self.aws_access_key_id and self.aws_secret_access_key)
    
    async def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = 'Count',
        dimensions: Optional[List[Dict]] = None
    ) -> bool:
        """
        Put custom metric to CloudWatch.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit (Count, Seconds, Bytes, etc.)
            dimensions: Optional dimensions for the metric
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            logger.warning("AWS credentials not configured for CloudWatch")
            return False
        
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.now()
            }
            
            if dimensions:
                metric_data['Dimensions'] = dimensions
            
            self.client.put_metric_data(
                Namespace=self.namespace,
                MetricData=[metric_data]
            )
            
            logger.debug(f"Put CloudWatch metric: {metric_name}={value}")
            return True
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"CloudWatch put_metric error: {e}")
            return False
    
    async def put_metrics_batch(self, metrics: List[Dict]) -> bool:
        """
        Put multiple metrics in a single request.
        
        Args:
            metrics: List of metric dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            logger.warning("AWS credentials not configured for CloudWatch")
            return False
        
        try:
            metric_data = []
            for metric in metrics:
                data = {
                    'MetricName': metric['name'],
                    'Value': metric['value'],
                    'Unit': metric.get('unit', 'Count'),
                    'Timestamp': datetime.now()
                }
                if 'dimensions' in metric:
                    data['Dimensions'] = metric['dimensions']
                metric_data.append(data)
            
            self.client.put_metric_data(
                Namespace=self.namespace,
                MetricData=metric_data
            )
            
            logger.debug(f"Put {len(metrics)} CloudWatch metrics")
            return True
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"CloudWatch put_metrics_batch error: {e}")
            return False
    
    async def log_event(
        self,
        log_group: str,
        log_stream: str,
        message: str
    ) -> bool:
        """
        Log event to CloudWatch Logs.
        
        Args:
            log_group: Log group name
            log_stream: Log stream name
            message: Log message
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured():
            logger.warning("AWS credentials not configured for CloudWatch Logs")
            return False
        
        try:
            # Ensure log group exists
            try:
                self.logs_client.create_log_group(logGroupName=log_group)
            except self.logs_client.exceptions.ResourceAlreadyExistsException:
                pass
            
            # Ensure log stream exists
            try:
                self.logs_client.create_log_stream(
                    logGroupName=log_group,
                    logStreamName=log_stream
                )
            except self.logs_client.exceptions.ResourceAlreadyExistsException:
                pass
            
            # Put log event
            self.logs_client.put_log_events(
                logGroupName=log_group,
                logStreamName=log_stream,
                logEvents=[
                    {
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'message': message
                    }
                ]
            )
            
            logger.debug(f"Logged to CloudWatch: {log_group}/{log_stream}")
            return True
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"CloudWatch log_event error: {e}")
            return False
    
    async def get_metric_statistics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        period: int = 300,
        statistics: List[str] = None
    ) -> Optional[Dict]:
        """
        Get metric statistics from CloudWatch.
        
        Args:
            metric_name: Name of the metric
            start_time: Start time for statistics
            end_time: End time for statistics
            period: Period in seconds
            statistics: List of statistics (Average, Sum, etc.)
            
        Returns:
            Metric statistics or None
        """
        if not self.is_configured():
            logger.warning("AWS credentials not configured for CloudWatch")
            return None
        
        if statistics is None:
            statistics = ['Sum', 'Average']
        
        try:
            response = self.client.get_metric_statistics(
                Namespace=self.namespace,
                MetricName=metric_name,
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=statistics
            )
            
            return response.get('Datapoints', [])
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"CloudWatch get_metric_statistics error: {e}")
            return None


# Singleton instance
cloudwatch_service = CloudWatchService()


# Convenience functions for common metrics
async def track_api_request(endpoint: str, status_code: int):
    """Track API request metric."""
    await cloudwatch_service.put_metrics_batch([
        {
            'name': 'APIRequests',
            'value': 1,
            'dimensions': [
                {'Name': 'Endpoint', 'Value': endpoint},
                {'Name': 'StatusCode', 'Value': str(status_code)}
            ]
        }
    ])


async def track_voice_query(language: str, success: bool):
    """Track voice query metric."""
    await cloudwatch_service.put_metrics_batch([
        {
            'name': 'VoiceQueries',
            'value': 1,
            'dimensions': [
                {'Name': 'Language', 'Value': language},
                {'Name': 'Success', 'Value': str(success)}
            ]
        }
    ])


async def track_disease_detection(success: bool, processing_time: float):
    """Track disease detection metric."""
    await cloudwatch_service.put_metrics_batch([
        {
            'name': 'DiseaseDetections',
            'value': 1,
            'dimensions': [{'Name': 'Success', 'Value': str(success)}]
        },
        {
            'name': 'DiseaseDetectionTime',
            'value': processing_time,
            'unit': 'Seconds'
        }
    ])
