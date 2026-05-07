"""
Django Channels Routing for WebSocket connections
Handles real-time notifications across the system
"""

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from django.urls import path
from workflow.consumers import NotificationConsumer

# Initialize Django ASGI application early
django_asgi_app = get_asgi_application()

# WebSocket URL patterns
websocket_urlpatterns = [
    path('ws/notifications/', NotificationConsumer.as_asgi()),
    path('ws/dashboard/<int:user_id>/', NotificationConsumer.as_asgi()),
]

# Main ASGI application
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})