from rest_framework import serializers
from .models import HealthCheck, HealthCheckLog, FailedHealthCheck


class HealthCheckLogSerializer(serializers.ModelSerializer):
    """Serializer for HealthCheckLog instances"""
    class Meta:
        model = HealthCheckLog
        fields = ['id', 'status', 'timestamp', 'response_time', 'additional_data']


class FailedHealthCheckSerializer(serializers.ModelSerializer):
    """Serializer for FailedHealthCheck instances"""
    class Meta:
        model = FailedHealthCheck
        fields = ['id', 'failed_at', 'notification_sent', 'notification_time']


class HealthCheckSerializer(serializers.ModelSerializer):
    """Serializer for HealthCheck instances"""
    class Meta:
        model = HealthCheck
        fields = [
            'id', 'name', 'description', 'url', 'created_at', 
            'interval_days', 'interval_hours', 'interval_minutes',
            'grace_days', 'grace_hours', 'grace_minutes',
            'ping_url', 'notify_email', 'notify_webhook',
            'last_ping', 'is_active', 'is_up',
            'response_time_threshold', 'avg_response_time',
            'max_response_time', 'min_response_time', 'total_pings'
        ]
        read_only_fields = ['id', 'created_at', 'ping_url', 'last_ping', 
                            'avg_response_time', 'max_response_time', 
                            'min_response_time', 'total_pings']


class HealthCheckDetailSerializer(HealthCheckSerializer):
    """
    Detailed serializer for HealthCheck instances 
    including recent logs and failures
    """
    recent_logs = serializers.SerializerMethodField()
    recent_failures = serializers.SerializerMethodField()
    
    class Meta(HealthCheckSerializer.Meta):
        fields = HealthCheckSerializer.Meta.fields + ['recent_logs', 'recent_failures']
    
    def get_recent_logs(self, obj):
        # Get the 10 most recent logs
        recent_logs = obj.logs.all()[:10]
        return HealthCheckLogSerializer(recent_logs, many=True).data
    
    def get_recent_failures(self, obj):
        # Get the 5 most recent failures
        recent_failures = obj.failures.all()[:5]
        return FailedHealthCheckSerializer(recent_failures, many=True).data


class HealthCheckCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating HealthCheck instances"""
    class Meta:
        model = HealthCheck
        fields = [
            'name', 'description', 'url',
            'interval_days', 'interval_hours', 'interval_minutes',
            'grace_days', 'grace_hours', 'grace_minutes',
            'notify_email', 'notify_webhook', 'response_time_threshold',
            'is_active'
        ]
        
    def validate(self, data):
        """Validate that at least one time interval is set"""
        interval_days = data.get('interval_days', 0)
        interval_hours = data.get('interval_hours', 0)
        interval_minutes = data.get('interval_minutes', 0)
        
        if interval_days == 0 and interval_hours == 0 and interval_minutes == 0:
            raise serializers.ValidationError(
                "At least one time interval (days, hours, or minutes) must be greater than 0"
            )
        
        return data 