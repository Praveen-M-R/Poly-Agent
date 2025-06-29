from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Min, Max
from django.db import transaction
from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import HealthCheck, HealthCheckLog, FailedHealthCheck
from .serializers import (
    HealthCheckSerializer, 
    HealthCheckDetailSerializer, 
    HealthCheckCreateSerializer,
    HealthCheckLogSerializer,
    FailedHealthCheckSerializer
)

import time
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class HealthCheckViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling CRUD operations on HealthCheck model
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return HealthChecks for the current user only"""
        return HealthCheck.objects.filter(created_by=self.request.user)
    
    def get_serializer_class(self):
        """Return different serializers based on the action"""
        if self.action == 'create':
            return HealthCheckCreateSerializer
        elif self.action == 'retrieve':
            return HealthCheckDetailSerializer
        return HealthCheckSerializer
    
    def perform_create(self, serializer):
        """When creating a health check, set the created_by field to the current user"""
        serializer.save(created_by=self.request.user)
        
        # Invalidate user stats cache
        cache_key = f'health_check_summary_{self.request.user.id}'
        cache.delete(cache_key)
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get logs for a specific health check"""
        health_check = self.get_object()
        logs = health_check.logs.all()[:50]  # Limit to 50 most recent logs
        serializer = HealthCheckLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def failures(self, request, pk=None):
        """Get failure records for a specific health check"""
        health_check = self.get_object()
        failures = health_check.failures.all()[:20]  # Limit to 20 most recent failures
        serializer = FailedHealthCheckSerializer(failures, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary statistics for the user's health checks"""
        # Use caching for performance
        cache_key = f'health_check_summary_{request.user.id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # Get counts
        total_checks = HealthCheck.objects.filter(created_by=request.user).count()
        active_checks = HealthCheck.objects.filter(created_by=request.user, is_active=True).count()
        up_checks = HealthCheck.objects.filter(created_by=request.user, is_up=True, is_active=True).count()
        down_checks = HealthCheck.objects.filter(created_by=request.user, is_up=False, is_active=True).count()
        
        # Get most recent failures
        recent_failures = FailedHealthCheck.objects.filter(
            health_check__created_by=request.user
        ).order_by('-failed_at')[:5]
        
        # Aggregate response time data
        response_time_stats = HealthCheck.objects.filter(
            created_by=request.user,
            total_pings__gt=0
        ).aggregate(
            avg_response=Avg('avg_response_time'),
            max_response=Max('max_response_time'),
            min_response=Min('min_response_time')
        )
        
        summary_data = {
            'total_checks': total_checks,
            'active_checks': active_checks,
            'up_checks': up_checks,
            'down_checks': down_checks,
            'health_percentage': (up_checks / active_checks * 100) if active_checks > 0 else 0,
            'recent_failures': FailedHealthCheckSerializer(recent_failures, many=True).data,
            'response_time_stats': response_time_stats
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, summary_data, 300)
        
        return Response(summary_data)


@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def ping_health_check(request, ping_uuid):
    """
    Public API endpoint for receiving pings for health checks
    Can be pinged via GET or POST
    """
    try:
        start_time = time.time()
        
        # Find the health check with this UUID
        health_check = get_object_or_404(HealthCheck, ping_url=ping_uuid)
        
        # Calculate response time in milliseconds
        response_time = (time.time() - start_time) * 1000
        
        # Get any additional data from the request
        additional_data = None
        if request.method == 'POST':
            try:
                additional_data = request.data
            except:
                pass
        
        # Update the health check status
        with transaction.atomic():
            # Update last ping time
            health_check.last_ping = timezone.now()
            health_check.is_up = True
            health_check.save()
            
            # Create a log entry
            log = HealthCheckLog.objects.create(
                health_check=health_check,
                status=True,
                response_time=response_time,
                additional_data=additional_data
            )
            
            # Update response time stats
            health_check.update_response_time_stats(response_time)
            
            # Check if this was a previously failed check
            # If so, mark it as recovered
            FailedHealthCheck.objects.filter(
                health_check=health_check,
                notification_sent=False
            ).delete()
            
        return Response({
            'status': 'success',
            'message': f'Health check {health_check.name} pinged successfully',
            'response_time_ms': response_time
        })
    
    except Exception as e:
        logger.error(f"Error processing health check ping: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Failed to process health check ping'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reports(request):
    """
    Generate reports and analytics for health checks
    """
    # Get time period from query params (default to last 7 days)
    days = int(request.query_params.get('days', 7))
    since = timezone.now() - timedelta(days=days)
    
    # Get check_id from query params (optional)
    check_id = request.query_params.get('check_id', None)
    
    # Get user's health checks
    health_checks = HealthCheck.objects.filter(created_by=request.user)
    
    # Filter by check_id if provided
    if check_id and check_id.isdigit():
        health_checks = health_checks.filter(id=int(check_id))
    
    # Aggregate all-time stats
    active_checks_count = health_checks.filter(is_active=True).count()
    up_checks_count = health_checks.filter(is_active=True, is_up=True).count()
    
    uptime_percentage = 0
    if active_checks_count > 0:
        uptime_percentage = (up_checks_count / active_checks_count) * 100
    
    # Get recent logs for the specified period
    recent_logs = HealthCheckLog.objects.filter(
        health_check__in=health_checks,
        timestamp__gte=since
    ).order_by('timestamp')
    
    # Get response time data for charts
    response_time_data = []
    for log in recent_logs.filter(response_time__isnull=False)[:100]:  # Limit to 100 points
        response_time_data.append({
            'name': log.timestamp.strftime('%Y-%m-%d %H:%M'),
            'value': log.response_time
        })
    
    # Calculate response time stats
    response_time_stats = recent_logs.filter(response_time__isnull=False).aggregate(
        avg_response=Avg('response_time'),
        max_response=Max('response_time'),
        min_response=Min('response_time')
    )
    
    # Count downtime incidents
    downtime_incidents = 0
    for check in health_checks:
        # Count transitions from up to down
        check_logs = recent_logs.filter(health_check=check).order_by('timestamp')
        if check_logs.count() > 1:
            prev_status = None
            for log in check_logs:
                if prev_status is True and log.status is False:
                    downtime_incidents += 1
                prev_status = log.status
    
    # Prepare data in the format expected by the frontend
    return Response({
        'uptime_percentage': uptime_percentage,
        'response_time_data': response_time_data,
        'response_time_stats': response_time_stats,
        'downtime_incidents': downtime_incidents,
        'total_checks': health_checks.count(),
        'active_checks': active_checks_count,
        'up_checks': up_checks_count,
        'down_checks': active_checks_count - up_checks_count,
        'period_days': days,
        'anomalies': []  # No anomaly detection implemented yet
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_data(request):
    """
    Export health check data as JSON
    """
    # Get the user's health checks
    health_checks = HealthCheck.objects.filter(created_by=request.user)
    
    # Get from/to date filters
    from_date_str = request.query_params.get('from')
    to_date_str = request.query_params.get('to')
    
    try:
        if from_date_str:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        else:
            from_date = (timezone.now() - timedelta(days=30)).date()
        
        if to_date_str:
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        else:
            to_date = timezone.now().date()
    except ValueError:
        return Response({
            'error': 'Invalid date format. Use YYYY-MM-DD'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Add time to make the dates inclusive
    from_datetime = datetime.combine(from_date, datetime.min.time())
    to_datetime = datetime.combine(to_date, datetime.max.time())
    
    # Prepare export data
    export_data = {
        'health_checks': [],
        'export_date': timezone.now().isoformat(),
        'user': request.user.username,
        'period': {
            'from': from_datetime.isoformat(),
            'to': to_datetime.isoformat()
        }
    }
    
    # Add data for each health check
    for check in health_checks:
        check_data = HealthCheckSerializer(check).data
        
        # Get logs for the period
        logs = check.logs.filter(
            timestamp__gte=from_datetime,
            timestamp__lte=to_datetime
        )
        
        check_data['logs'] = HealthCheckLogSerializer(logs, many=True).data
        export_data['health_checks'].append(check_data)
    
    return Response(export_data)


@login_required
def create_health_check(request):
    """Handles health check creation with transaction support"""
    if request.method == "POST":
        try:
            with transaction.atomic():
                # Extract data from request.POST
                name = request.POST.get('name')
                description = request.POST.get('description', '')
                url = request.POST.get('url', '')
                
                # Interval settings
                interval_days = int(request.POST.get('interval_days', 0))
                interval_hours = int(request.POST.get('interval_hours', 0))
                interval_minutes = int(request.POST.get('interval_minutes', 5))
                
                # Grace period settings
                grace_days = int(request.POST.get('grace_days', 0))
                grace_hours = int(request.POST.get('grace_hours', 0))
                grace_minutes = int(request.POST.get('grace_minutes', 5))
                
                # Notification settings
                notify_email = request.POST.get('notify_email', '')
                notify_webhook = request.POST.get('notify_webhook', '')
                response_time_threshold = int(request.POST.get('response_time_threshold', 1000))
                
                # Create the health check object
                health_check = HealthCheck.objects.create(
                    name=name,
                    description=description,
                    url=url,
                    created_by=request.user,
                    interval_days=interval_days,
                    interval_hours=interval_hours,
                    interval_minutes=interval_minutes,
                    grace_days=grace_days,
                    grace_hours=grace_hours,
                    grace_minutes=grace_minutes,
                    notify_email=notify_email,
                    notify_webhook=notify_webhook,
                    response_time_threshold=response_time_threshold
                )
                
                # Invalidate user stats cache
                cache_key = f'health_check_summary_{request.user.id}'
                cache.delete(cache_key)
                
                messages.success(request, 'Health check created successfully!')
                return redirect("healthcheck-list")  # Redirect to the health checks list
        except Exception as e:
            logger.error(f"Error creating health check: {str(e)}")
            messages.error(request, f'An error occurred while creating the health check: {str(e)}')
    
    # For GET requests or if the POST was unsuccessful, show the form
    return render(request, "health_check/create_health_check.html")


@login_required
def health_checks_list(request):
    """Displays health checks for the logged in user"""
    try:
        health_checks = HealthCheck.objects.filter(created_by=request.user).order_by('-created_at')
        return render(request, "health_check/health_checks_list.html", {
            "health_checks": health_checks
        })
    except Exception as e:
        logger.error(f"Error loading health checks list: {str(e)}")
        messages.error(request, f'An error occurred while loading health checks: {str(e)}')
        return redirect('dashboard')  # Redirect to the main dashboard
