from django.contrib import admin
from .models import HealthCheck, HealthCheckLog, FailedHealthCheck

class HealthCheckLogInline(admin.TabularInline):
    model = HealthCheckLog
    extra = 0
    readonly_fields = ('timestamp', 'status', 'response_time')
    can_delete = False
    max_num = 10
    
    def has_add_permission(self, request, obj=None):
        return False

class FailedHealthCheckInline(admin.TabularInline):
    model = FailedHealthCheck
    extra = 0
    readonly_fields = ('failed_at', 'notification_sent', 'notification_time')
    can_delete = False
    max_num = 5
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(HealthCheck)
class HealthCheckAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'is_active', 'is_up', 'last_ping', 'total_pings', 'avg_response_time')
    list_filter = ('is_active', 'is_up', 'created_by')
    search_fields = ('name', 'description')
    readonly_fields = ('ping_url', 'last_ping', 'avg_response_time', 'min_response_time', 'max_response_time', 'total_pings')
    inlines = [HealthCheckLogInline, FailedHealthCheckInline]

@admin.register(HealthCheckLog)
class HealthCheckLogAdmin(admin.ModelAdmin):
    list_display = ('health_check', 'timestamp', 'status', 'response_time')
    list_filter = ('status', 'timestamp')
    search_fields = ('health_check__name',)
    readonly_fields = ('timestamp',)

@admin.register(FailedHealthCheck)
class FailedHealthCheckAdmin(admin.ModelAdmin):
    list_display = ('health_check', 'failed_at', 'notification_sent', 'notification_time')
    list_filter = ('notification_sent', 'failed_at')
    search_fields = ('health_check__name',)
    readonly_fields = ('failed_at',)
