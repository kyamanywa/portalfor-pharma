from django import template
from dashboards.permissions import check_dashboard_permission, get_user_accessible_dashboards

register = template.Library()

@register.simple_tag
def has_dashboard_permission(user, dashboard_name):
    """
    Template tag to check if user has permission to access a dashboard
    
    Usage: {% has_dashboard_permission user 'admin_dashboard' as can_access %}
    """
    return check_dashboard_permission(user, dashboard_name)

@register.simple_tag
def user_dashboards(user):
    """
    Template tag to get list of accessible dashboards for a user
    
    Usage: {% user_dashboards user as accessible_dashboards %}
    """
    return get_user_accessible_dashboards(user)

@register.inclusion_tag('dashboards/dashboard_card.html')
def dashboard_card(user, dashboard_name, title, description, icon, url, color='primary'):
    """
    Template tag to render a dashboard card with permission check
    
    Usage: {% dashboard_card user 'admin_dashboard' 'Admin Dashboard' 'System overview' 'fas fa-chart-line' 'dashboards:admin_dashboard' 'info' %}
    """
    has_permission = check_dashboard_permission(user, dashboard_name)
    
    return {
        'has_permission': has_permission,
        'title': title,
        'description': description,
        'icon': icon,
        'url': url,
        'color': color
    }