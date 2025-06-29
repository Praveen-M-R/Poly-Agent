from django.db import models
from django.conf import settings
import uuid

class HealthCheck(models.Model):
    """Model for storing health check configurations"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True, help_text="URL to be monitored (optional)")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Check interval
    interval_days = models.PositiveIntegerField(default=0)
    interval_hours = models.PositiveIntegerField(default=0)
    interval_minutes = models.PositiveIntegerField(default=5)  # Default 5 minutes
    
    # Grace period before marking as failed
    grace_days = models.PositiveIntegerField(default=0)
    grace_hours = models.PositiveIntegerField(default=0)
    grace_minutes = models.PositiveIntegerField(default=5)  # Default 5 minutes
    
    # Unique URL for ping endpoint
    ping_url = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Notification settings
    notify_email = models.EmailField(blank=True, null=True)
    notify_webhook = models.URLField(blank=True, null=True)
    
    # Status tracking
    last_ping = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_up = models.BooleanField(default=False)

    # Response time tracking
    response_time_threshold = models.PositiveIntegerField(
        default=1000,
        help_text="Maximum acceptable response time in milliseconds"
    )
    avg_response_time = models.FloatField(
        default=0,
        help_text="Average response time in milliseconds"
    )
    max_response_time = models.FloatField(
        default=0,
        help_text="Maximum response time in milliseconds"
    )
    min_response_time = models.FloatField(
        default=0,
        help_text="Minimum response time in milliseconds"
    )
    total_pings = models.PositiveIntegerField(
        default=0,
        help_text="Total number of successful pings"
    )

    def __str__(self):
        return self.name

    def update_response_time_stats(self, response_time):
        """Update response time statistics for the health check"""
        self.total_pings += 1
        
        # Update average response time
        self.avg_response_time = (
            (self.avg_response_time * (self.total_pings - 1) + response_time) 
            / self.total_pings
        )
        
        # Update min and max response times
        if self.total_pings == 1:
            self.min_response_time = response_time
            self.max_response_time = response_time
        else:
            self.min_response_time = min(self.min_response_time, response_time)
            self.max_response_time = max(self.max_response_time, response_time)
        
        self.save()


class HealthCheckLog(models.Model):
    """Model for storing health check ping logs"""
    health_check = models.ForeignKey(HealthCheck, on_delete=models.CASCADE, related_name="logs")
    status = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Response time in milliseconds
    response_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Response time in milliseconds"
    )
    
    # Additional ping data (JSON)
    additional_data = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.health_check.name} - {self.timestamp} - {self.status}"


class FailedHealthCheck(models.Model):
    """Model for tracking failed health checks and notifications"""
    health_check = models.ForeignKey(HealthCheck, on_delete=models.CASCADE, related_name="failures")
    failed_at = models.DateTimeField(auto_now_add=True)
    notification_sent = models.BooleanField(default=False)
    notification_time = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Failed: {self.health_check.name} at {self.failed_at}"
