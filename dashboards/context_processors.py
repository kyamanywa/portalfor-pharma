"""
Context processor to make admin-configured settings available in all templates
"""
from workflow.models import (
    get_dashboard_setting, get_alert_setting, get_session_setting, get_production_limit
)

def admin_settings_context(request):
    """
    Context processor to provide commonly used admin settings to all templates
    """
    try:
        return {
            'dashboard_settings': {
                'auto_refresh': get_dashboard_setting('dashboard_auto_refresh', True),
                'refresh_interval': get_dashboard_setting('dashboard_refresh_interval', 30) * 1000,  # Convert to milliseconds
                'admin_refresh_interval': get_dashboard_setting('admin_dashboard_refresh_interval', 60) * 1000,
                'phase_countdown_interval': get_dashboard_setting('phase_countdown_refresh_interval', 1) * 1000,
                'show_phase_timers': get_dashboard_setting('show_phase_timers', True),
                'enable_real_time_updates': get_dashboard_setting('enable_real_time_updates', True),
                'show_advanced_filters': get_dashboard_setting('show_advanced_filters', False),
                'default_page_size': get_dashboard_setting('default_page_size', 20),
                'mobile_responsive_breakpoint': get_dashboard_setting('mobile_responsive_breakpoint', 768),
                'mobile_hide_sidebar': get_dashboard_setting('mobile_hide_sidebar', True),
            },
            'alert_settings': {
                'show_overrun_notifications': get_alert_setting('show_overrun_notifications', True),
                'auto_dismiss_seconds': get_alert_setting('notification_auto_dismiss_seconds', 5) * 1000,
                'max_notifications_display': get_alert_setting('max_notifications_display', 10),
                'sound_enabled': get_alert_setting('notification_sound_enabled', False),
            },
            'session_settings': {
                'timeout_hours': get_session_setting('session_timeout_hours', 8),
                'warning_minutes': get_session_setting('session_warning_minutes', 15),
                'extend_on_activity': get_session_setting('session_extend_on_activity', True),
            },
            'production_limits': {
                'max_concurrent_batches': get_production_limit('max_concurrent_batches', 10),
                'max_page_size': get_production_limit('api_max_page_size', 100),
                'max_file_upload_size_mb': get_production_limit('max_file_upload_size_mb', 50),
            }
        }
    except Exception as e:
        # Fallback to defaults if database is not available
        return {
            'dashboard_settings': {
                'auto_refresh': True,
                'refresh_interval': 30000,
                'admin_refresh_interval': 60000,
                'phase_countdown_interval': 1000,
                'show_phase_timers': True,
                'enable_real_time_updates': True,
                'show_advanced_filters': False,
                'default_page_size': 20,
                'mobile_responsive_breakpoint': 768,
                'mobile_hide_sidebar': True,
            },
            'alert_settings': {
                'show_overrun_notifications': True,
                'auto_dismiss_seconds': 5000,
                'max_notifications_display': 10,
                'sound_enabled': False,
            },
            'session_settings': {
                'timeout_hours': 8,
                'warning_minutes': 15,
                'extend_on_activity': True,
            },
            'production_limits': {
                'max_concurrent_batches': 10,
                'max_page_size': 100,
                'max_file_upload_size_mb': 50,
            }
        }