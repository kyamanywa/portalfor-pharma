import time
from django.contrib import auth
from django.contrib.auth import logout
from django.utils.deprecation import MiddlewareMixin
from workflow.models_admin_settings import get_session_setting

class SessionTimeoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip for non-authenticated users
        if not request.user.is_authenticated:
            return None
            
        # Skip for AJAX requests
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return None
        
        # Get current time and last activity time
        current_time = time.time()
        last_activity = request.session.get('last_activity')

        # Use the centralized session management setting when available
        session_timeout_hours = get_session_setting('session_timeout_hours', 12)
        try:
            session_timeout = int(float(session_timeout_hours) * 3600)
        except (TypeError, ValueError):
            session_timeout = 43200

        # Keep the browser session expiry aligned with the enforced timeout
        request.session.set_expiry(session_timeout)
        
        # Update last activity time
        request.session['last_activity'] = current_time
        
        # If no last activity or session expired, ignore
        if not last_activity:
            return None
            
        # Check if session has expired
        if current_time - last_activity > session_timeout:
            # Logout user and display message
            auth.logout(request)
            # Let the logout view handle the redirect
            
        return None
