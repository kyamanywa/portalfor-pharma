"""
ASGI config for kampala_pharma project with WebSocket support.

It exposes the ASGI callable as a module-level variable named ``application``.
This configuration supports both HTTP and WebSocket connections for real-time features.
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import compatibility shim for Python 3.14+ before Django imports
import pkgutil_compat

from django.core.asgi import get_asgi_application

# Initialize Django ASGI application early to ensure the AppRegistry is populated
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kampala_pharma.settings')
django.setup()

# Import Django ASGI application
django_asgi_app = get_asgi_application()

# Import Channels routing
try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
    from django.urls import path, re_path
    
    # Define WebSocket URL patterns (will be populated when WebSocket views are created)
    websocket_urlpatterns = [
        # Real-time dashboard updates
        re_path(r'ws/dashboard/$', 'dashboards.consumers.DashboardConsumer'),
        # Production status updates  
        re_path(r'ws/production/$', 'workflow.consumers.ProductionConsumer'),
        # BMR status updates
        re_path(r'ws/bmr/(?P<bmr_id>\w+)/$', 'bmr.consumers.BMRConsumer'),
    ]
    
    # Combined ASGI application with both HTTP and WebSocket support
    application = ProtocolTypeRouter({
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    })
    
    print("🔌 WebSocket support enabled")
    
except ImportError:
    # Fallback to HTTP-only if Channels is not available
    application = django_asgi_app
    print("📡 HTTP-only mode (WebSocket support requires 'channels' package)")

print("🚀 KPI Operations ASGI application ready")
