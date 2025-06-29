from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'checks', views.HealthCheckViewSet, basename='healthcheck')

urlpatterns = [
    # API endpoints using viewsets
    path('api/', include(router.urls)),
    
    # Public ping endpoint (no authentication required)
    path('ping/<uuid:ping_uuid>/', views.ping_health_check, name='ping'),
    
    # Additional API endpoints
    path('api/reports/', views.reports, name='reports'),
    path('api/export/', views.export_data, name='export'),
] 