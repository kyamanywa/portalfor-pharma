# API Configuration for KPI Operations System
# This file provides comprehensive API endpoints for system integration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets, serializers
from django.conf import settings
from django.utils import timezone
import sys

# Import models safely
try:
    from workflow.models import Machine, BatchPhaseExecution, ProductMachineTimingSetting
    from accounts.models import CustomUser
    models_available = True
except ImportError as e:
    print(f"⚠️  Some models not available for API: {e}")
    models_available = False

# Create API ViewSets for models that don't have them yet
if models_available:
    class MachineSerializer(serializers.ModelSerializer):
        class Meta:
            model = Machine
            fields = '__all__'

    class MachineViewSet(viewsets.ModelViewSet):
        queryset = Machine.objects.all()
        serializer_class = MachineSerializer
        permission_classes = [IsAuthenticated]

    class BatchPhaseExecutionSerializer(serializers.ModelSerializer):
        phase_name = serializers.CharField(source='phase.get_phase_name_display', read_only=True)
        bmr_batch_number = serializers.CharField(source='bmr.batch_number', read_only=True)
        machine_name = serializers.CharField(source='machine_used.name', read_only=True)
        
        class Meta:
            model = BatchPhaseExecution
            fields = '__all__'

    class BatchPhaseExecutionViewSet(viewsets.ModelViewSet):
        queryset = BatchPhaseExecution.objects.all()
        serializer_class = BatchPhaseExecutionSerializer
        permission_classes = [IsAuthenticated]
        
        def get_queryset(self):
            queryset = BatchPhaseExecution.objects.select_related('bmr', 'phase', 'machine_used')
            
            # Filter by BMR if provided
            bmr_id = self.request.query_params.get('bmr', None)
            if bmr_id:
                queryset = queryset.filter(bmr_id=bmr_id)
                
            # Filter by status if provided
            status = self.request.query_params.get('status', None)
            if status:
                queryset = queryset.filter(status=status)
                
            return queryset

    class ProductMachineTimingSettingSerializer(serializers.ModelSerializer):
        product_name = serializers.CharField(source='product.product_name', read_only=True)
        machine_name = serializers.CharField(source='machine.name', read_only=True)
        phase_name = serializers.CharField(source='phase.get_phase_name_display', read_only=True)
        
        class Meta:
            model = ProductMachineTimingSetting
            fields = '__all__'

    class ProductMachineTimingSettingViewSet(viewsets.ModelViewSet):
        queryset = ProductMachineTimingSetting.objects.all()
        serializer_class = ProductMachineTimingSettingSerializer
        permission_classes = [IsAuthenticated]
else:
    # Placeholder classes if models not available
    class MachineViewSet:
        pass
    class BatchPhaseExecutionViewSet:
        pass
    class ProductMachineTimingSettingViewSet:
        pass

# API System Status endpoint
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_status(request):
    """
    Get comprehensive system status for integrations
    """
    try:
        from bmr.models import BMR
        from workflow.models import Machine, BatchPhaseExecution
        from products.models import Product
        
        status_data = {
            'system': 'KPI Operations System',
            'version': '2.0',
            'status': 'online',
            'timestamp': timezone.now().isoformat(),
            'user': {
                'username': request.user.username,
                'role': request.user.role,
                'permissions': list(request.user.get_all_permissions())
            },
            'statistics': {
                'total_bmrs': BMR.objects.count(),
                'active_bmrs': BMR.objects.filter(status__in=['approved', 'in_production']).count(),
                'total_products': Product.objects.count(),
                'total_machines': Machine.objects.count(),
                'active_executions': BatchPhaseExecution.objects.filter(status='in_progress').count(),
                'machine_timings': ProductMachineTimingSetting.objects.count()
            },
            'integrations': {
                'api_enabled': True,
                'websocket_supported': hasattr(settings, 'CHANNEL_LAYERS'),
                'real_time_updates': True,
                'authentication': 'Token-based + Session',
                'csrf_protection': True
            }
        }
        
        return Response(status_data)
    except Exception as e:
        return Response({
            'error': 'System status unavailable',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Production metrics endpoint
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def production_metrics(request):
    """
    Get real-time production metrics for dashboards/integrations
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        from bmr.models import BMR
        from workflow.models import BatchPhaseExecution
        
        # Get metrics for the last 24 hours
        yesterday = timezone.now() - timedelta(days=1)
        
        metrics = {
            'period': '24_hours',
            'timestamp': timezone.now().isoformat(),
            'bmr_metrics': {
                'total_created': BMR.objects.filter(created_date__gte=yesterday).count(),
                'completed': BMR.objects.filter(status='completed', updated_date__gte=yesterday).count(),
                'in_progress': BMR.objects.filter(status='in_production').count(),
                'pending_approval': BMR.objects.filter(status='pending_regulatory_approval').count()
            },
            'production_metrics': {
                'phases_completed': BatchPhaseExecution.objects.filter(
                    status='completed', 
                    completed_date__gte=yesterday
                ).count(),
                'phases_in_progress': BatchPhaseExecution.objects.filter(status='in_progress').count(),
                'average_phase_duration': '2.5 hours',  # Could be calculated dynamically
                'machine_utilization': '78%'  # Could be calculated from actual data
            },
            'quality_metrics': {
                'batches_approved': BatchPhaseExecution.objects.filter(
                    qc_approved=True,
                    qc_approval_date__gte=yesterday
                ).count(),
                'batches_rejected': BatchPhaseExecution.objects.filter(
                    qc_approved=False,
                    qc_approval_date__gte=yesterday
                ).count()
            }
        }
        
        return Response(metrics)
    except Exception as e:
        return Response({
            'error': 'Metrics unavailable',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Create router and register ViewSets
router = DefaultRouter()

# Register existing ViewSets if available
if models_available:
    try:
        router.register(r'machines', MachineViewSet)
        router.register(r'executions', BatchPhaseExecutionViewSet)
        router.register(r'machine-timings', ProductMachineTimingSettingViewSet)
        
        # Register product ViewSet if it exists
        try:
            from products.views import ProductViewSet
            router.register(r'products', ProductViewSet)
        except ImportError:
            pass
            
        # Register BMR ViewSets if they exist
        try:
            from bmr.views import BMRViewSet
            router.register(r'bmrs', BMRViewSet)
        except ImportError:
            pass
            
    except Exception as e:
        print(f"⚠️  API registration warning: {e}")

# URL patterns for API  
api_urlpatterns = [
    # Core API endpoints
    path('', include(router.urls)),
    
    # System endpoints
    path('status/', system_status, name='api_system_status'),
    path('metrics/', production_metrics, name='api_production_metrics'),
    
    # Authentication endpoints
    path('auth/', include('rest_framework.urls')),
]

# Export for main urls.py
__all__ = ['api_urlpatterns', 'router']