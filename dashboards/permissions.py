from django.shortcuts import redirect
from django.contrib import messages
from .models import DashboardPermission

def check_dashboard_permission(user, dashboard_name):
    """
    Check if a user has permission to access a specific dashboard
    
    Args:
        user: User object
        dashboard_name: Name of the dashboard to check (matches DashboardPermission.name)
    
    Returns:
        bool: True if user has access, False otherwise
    """
    try:
        permission = DashboardPermission.objects.get(name=dashboard_name, is_active=True)
        return permission.user_has_access(user)
    except DashboardPermission.DoesNotExist:
        # If no permission rule exists, fall back to basic is_staff check
        return user.is_staff

def require_dashboard_permission(dashboard_name, redirect_url='dashboards:dashboard_home'):
    """
    Decorator to require dashboard permission for a view
    
    Args:
        dashboard_name: Name of the dashboard permission to check
        redirect_url: URL to redirect to if access denied
    
    Returns:
        Decorator function
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please log in to access this page.')
                return redirect('accounts:login')  # Fixed: Use regular login, not admin login
            
            if not check_dashboard_permission(request.user, dashboard_name):
                messages.error(request, 'Access denied. You do not have permission to access this dashboard.')
                return redirect(redirect_url)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def get_user_accessible_dashboards(user):
    """
    Get list of dashboards a user can access
    
    Args:
        user: User object
    
    Returns:
        list: List of dashboard names the user can access
    """
    accessible_dashboards = []
    
    for permission in DashboardPermission.objects.filter(is_active=True):
        if permission.user_has_access(user):
            accessible_dashboards.append(permission.name)
    
    return accessible_dashboards