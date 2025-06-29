from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
import logging
import requests
from datetime import timedelta

from Poly_Agent.celery import app

from .models import HealthCheck, HealthCheckLog, FailedHealthCheck

logger = logging.getLogger(__name__)


@app.task
def check_health_checks():
    """
    Task to check for health checks that have not been pinged
    within their expected interval + grace period
    """
    logger.info("Running health check monitoring task")
    now = timezone.now()
    
    # Get all active health checks
    active_checks = HealthCheck.objects.filter(is_active=True)
    
    for check in active_checks:
        # Calculate the expected ping interval and grace period
        interval = timedelta(
            days=check.interval_days,
            hours=check.interval_hours,
            minutes=check.interval_minutes
        )
        
        grace_period = timedelta(
            days=check.grace_days,
            hours=check.grace_hours,
            minutes=check.grace_minutes
        )
        
        # Skip checks that have never been pinged
        if not check.last_ping:
            continue
        
        # Calculate when the check is considered failed
        failure_time = check.last_ping + interval + grace_period
        
        # Check if the health check has failed
        if now > failure_time:
            # The check has failed, mark it as down
            with transaction.atomic():
                # Only proceed if the check is currently up
                # to avoid duplicate notifications
                if check.is_up:
                    check.is_up = False
                    check.save()
                    
                    # Create a failed check log
                    HealthCheckLog.objects.create(
                        health_check=check,
                        status=False
                    )
                    
                    # Create a failed health check entry
                    failed_check = FailedHealthCheck.objects.create(
                        health_check=check,
                        failed_at=now
                    )
                    
                    # Schedule notification task
                    send_failure_notification.delay(failed_check.id)
                    
                    logger.info(f"Health check '{check.name}' marked as down")


@app.task
def send_failure_notification(failed_check_id):
    """
    Task to send notification for a failed health check
    """
    try:
        failed_check = FailedHealthCheck.objects.get(id=failed_check_id)
        check = failed_check.health_check
        
        # Skip if already notified
        if failed_check.notification_sent:
            return
        
        # Send email notification if configured
        if check.notify_email:
            subject = f"Health Check Failed: {check.name}"
            message = (
                f"Your health check '{check.name}' has failed.\n\n"
                f"Last successful ping: {check.last_ping}\n"
                f"Failed at: {failed_check.failed_at}\n\n"
                f"Please check your application or service."
            )
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [check.notify_email]
            
            try:
                send_mail(subject, message, from_email, recipient_list)
                logger.info(f"Sent email notification for '{check.name}' to {check.notify_email}")
            except Exception as e:
                logger.error(f"Failed to send email notification for '{check.name}': {str(e)}")
        
        # Send webhook notification if configured
        if check.notify_webhook:
            try:
                payload = {
                    'check_name': check.name,
                    'check_id': check.id,
                    'status': 'down',
                    'last_ping': check.last_ping.isoformat() if check.last_ping else None,
                    'failed_at': failed_check.failed_at.isoformat(),
                }
                
                response = requests.post(
                    check.notify_webhook,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code < 200 or response.status_code >= 300:
                    logger.error(f"Webhook returned error status {response.status_code}: {response.text}")
                else:
                    logger.info(f"Sent webhook notification for '{check.name}' to {check.notify_webhook}")
            except Exception as e:
                logger.error(f"Failed to send webhook notification for '{check.name}': {str(e)}")
        
        # Mark as notified
        failed_check.notification_sent = True
        failed_check.notification_time = timezone.now()
        failed_check.save()
    
    except FailedHealthCheck.DoesNotExist:
        logger.error(f"Failed check with ID {failed_check_id} not found")
    except Exception as e:
        logger.error(f"Error sending notification for failed check {failed_check_id}: {str(e)}")


@app.task
def cleanup_old_logs(days=30):
    """
    Task to remove logs older than the specified number of days
    """
    cutoff_date = timezone.now() - timedelta(days=days)
    
    # Delete old logs
    old_logs = HealthCheckLog.objects.filter(timestamp__lt=cutoff_date)
    count = old_logs.count()
    old_logs.delete()
    
    logger.info(f"Cleaned up {count} health check logs older than {days} days") 