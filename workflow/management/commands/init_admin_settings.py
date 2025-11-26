"""
Management command to initialize all system admin settings
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from workflow.models_admin_settings import (
    DashboardSettings, SystemAlertSettings, SessionManagementSettings, 
    ProductionLimitsSettings
)

class Command(BaseCommand):
    help = 'Initialize all system admin settings with default values'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing settings with new default values',
        )

    def handle(self, *args, **options):
        """Initialize all system admin settings"""
        
        with transaction.atomic():
            self.initialize_dashboard_settings(options['update_existing'])
            self.initialize_alert_settings(options['update_existing'])
            self.initialize_session_settings(options['update_existing'])
            self.initialize_production_limits(options['update_existing'])
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎯 All system admin settings initialized successfully!\n'
                f'You can now manage these settings through Django Admin:\n'
                f'📋 Dashboard Settings: "Workflow" → "Dashboard Settings"\n'
                f'🚨 Alert Settings: "Workflow" → "System Alert Settings"\n'
                f'🔐 Session Settings: "Workflow" → "Session Management Settings"\n'
                f'⚙️  Production Limits: "Workflow" → "Production Limits Settings"\n'
            )
        )

    def initialize_dashboard_settings(self, update_existing):
        """Initialize dashboard configuration settings"""
        
        settings = [
            # Refresh and Auto-Update Settings
            {
                'setting_name': 'dashboard_auto_refresh',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'refresh_timing',
                'description': 'Enable automatic dashboard refresh',
            },
            {
                'setting_name': 'dashboard_refresh_interval',
                'setting_value': '30',
                'data_type': 'integer',
                'category': 'refresh_timing',
                'description': 'Dashboard auto-refresh interval in seconds',
            },
            {
                'setting_name': 'admin_dashboard_refresh_interval',
                'setting_value': '60',
                'data_type': 'integer',
                'category': 'refresh_timing',
                'description': 'Admin dashboard refresh interval in seconds',
            },
            {
                'setting_name': 'phase_countdown_refresh_interval',
                'setting_value': '1',
                'data_type': 'integer',
                'category': 'refresh_timing',
                'description': 'Phase countdown timer refresh interval in seconds',
            },
            
            # Pagination Settings
            {
                'setting_name': 'default_page_size',
                'setting_value': '20',
                'data_type': 'integer',
                'category': 'pagination',
                'description': 'Default number of items per page in list views',
            },
            {
                'setting_name': 'max_page_size',
                'setting_value': '100',
                'data_type': 'integer',
                'category': 'pagination',
                'description': 'Maximum allowed items per page',
            },
            {
                'setting_name': 'pagination_show_all_threshold',
                'setting_value': '200',
                'data_type': 'integer',
                'category': 'pagination',
                'description': 'Maximum items before forcing pagination',
            },
            
            # UI Preferences
            {
                'setting_name': 'show_advanced_filters',
                'setting_value': 'false',
                'data_type': 'boolean',
                'category': 'dashboard_ui',
                'description': 'Show advanced filtering options by default',
            },
            {
                'setting_name': 'enable_real_time_updates',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'dashboard_ui',
                'description': 'Enable real-time dashboard updates via WebSocket',
            },
            {
                'setting_name': 'show_operator_statistics',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'dashboard_ui',
                'description': 'Show operator performance statistics on dashboards',
            },
            {
                'setting_name': 'show_phase_timers',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'dashboard_ui',
                'description': 'Show countdown timers for active phases',
            },
            
            # Mobile Responsive Settings
            {
                'setting_name': 'mobile_responsive_breakpoint',
                'setting_value': '768',
                'data_type': 'integer',
                'category': 'mobile_responsive',
                'description': 'Screen width breakpoint for mobile layout (pixels)',
            },
            {
                'setting_name': 'mobile_hide_sidebar',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'mobile_responsive',
                'description': 'Hide sidebar on mobile devices by default',
            },
            {
                'setting_name': 'mobile_compact_tables',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'mobile_responsive',
                'description': 'Use compact table layout on mobile devices',
            },
            
            # User Preferences
            {
                'setting_name': 'default_show_metrics_summary',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'user_preferences',
                'description': 'Show metrics summary by default for new users',
            },
            {
                'setting_name': 'default_show_recent_activities',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'user_preferences',
                'description': 'Show recent activities by default for new users',
            },
            {
                'setting_name': 'default_auto_refresh_enabled',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'user_preferences',
                'description': 'Enable auto-refresh by default for new users',
            },
        ]
        
        created_count, updated_count = self._create_or_update_settings(
            DashboardSettings, settings, update_existing
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'📋 Dashboard Settings: {created_count} created, {updated_count} updated'
            )
        )

    def initialize_alert_settings(self, update_existing):
        """Initialize system alert and notification settings"""
        
        settings = [
            # Email Alert Settings
            {
                'setting_name': 'email_alerts_enabled',
                'setting_value': 'false',
                'data_type': 'boolean',
                'category': 'email_alerts',
                'description': 'Enable email notifications for system alerts',
            },
            {
                'setting_name': 'admin_email_list',
                'setting_value': 'admin@kpiops.com, manager@kpiops.com',
                'data_type': 'email_list',
                'category': 'email_alerts',
                'description': 'Comma-separated list of admin emails for critical alerts',
            },
            {
                'setting_name': 'qa_email_list',
                'setting_value': 'qa@kpiops.com',
                'data_type': 'email_list',
                'category': 'email_alerts',
                'description': 'Email addresses for QA-related notifications',
            },
            {
                'setting_name': 'email_alert_cooldown_minutes',
                'setting_value': '30',
                'data_type': 'integer',
                'category': 'email_alerts',
                'description': 'Minimum minutes between duplicate email alerts',
            },
            
            # Dashboard Notification Settings
            {
                'setting_name': 'show_overrun_notifications',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'dashboard_notifications',
                'description': 'Show phase overrun notifications on dashboards',
            },
            {
                'setting_name': 'notification_auto_dismiss_seconds',
                'setting_value': '5',
                'data_type': 'integer',
                'category': 'dashboard_notifications',
                'description': 'Seconds before auto-dismissing success notifications',
            },
            {
                'setting_name': 'max_notifications_display',
                'setting_value': '10',
                'data_type': 'integer',
                'category': 'dashboard_notifications',
                'description': 'Maximum notifications to show in dashboard notification panel',
            },
            {
                'setting_name': 'notification_sound_enabled',
                'setting_value': 'false',
                'data_type': 'boolean',
                'category': 'dashboard_notifications',
                'description': 'Enable sound alerts for critical notifications',
            },
            
            # Phase Overrun Alert Settings
            {
                'setting_name': 'overrun_alert_enabled',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'overrun_alerts',
                'description': 'Enable automatic overrun alert generation',
            },
            {
                'setting_name': 'overrun_check_interval_minutes',
                'setting_value': '5',
                'data_type': 'integer',
                'category': 'overrun_alerts',
                'description': 'Minutes between automatic overrun checks',
            },
            {
                'setting_name': 'overrun_escalation_hours',
                'setting_value': '2',
                'data_type': 'integer',
                'category': 'overrun_alerts',
                'description': 'Hours before escalating unacknowledged overrun alerts',
            },
            
            # Quality Alert Settings
            {
                'setting_name': 'qc_failure_alert_enabled',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'quality_alerts',
                'description': 'Enable alerts for QC failures and rejections',
            },
            {
                'setting_name': 'quality_hold_alert_enabled',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'quality_alerts',
                'description': 'Enable alerts when batches are placed on quality hold',
            },
            
            # System Maintenance Alerts
            {
                'setting_name': 'maintenance_alert_enabled',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'system_maintenance',
                'description': 'Enable system maintenance notifications',
            },
            {
                'setting_name': 'maintenance_advance_notice_hours',
                'setting_value': '24',
                'data_type': 'integer',
                'category': 'system_maintenance',
                'description': 'Hours before maintenance to send advance notice',
            },
        ]
        
        created_count, updated_count = self._create_or_update_settings(
            SystemAlertSettings, settings, update_existing
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🚨 Alert Settings: {created_count} created, {updated_count} updated'
            )
        )

    def initialize_session_settings(self, update_existing):
        """Initialize session management and security settings"""
        
        settings = [
            # Session Timeout Settings
            {
                'setting_name': 'session_timeout_hours',
                'setting_value': '8',
                'data_type': 'integer',
                'category': 'session_timeout',
                'description': 'Hours of inactivity before automatic logout',
                'unit': 'hours',
                'requires_restart': True,
            },
            {
                'setting_name': 'session_warning_minutes',
                'setting_value': '15',
                'data_type': 'integer',
                'category': 'session_timeout',
                'description': 'Minutes before session expires to show warning',
                'unit': 'minutes',
            },
            {
                'setting_name': 'session_extend_on_activity',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'session_timeout',
                'description': 'Automatically extend session on user activity',
            },
            
            # Authentication Settings
            {
                'setting_name': 'max_login_attempts',
                'setting_value': '5',
                'data_type': 'integer',
                'category': 'authentication',
                'description': 'Maximum failed login attempts before account lockout',
                'unit': 'attempts',
                'requires_restart': True,
            },
            {
                'setting_name': 'account_lockout_duration_minutes',
                'setting_value': '30',
                'data_type': 'integer',
                'category': 'authentication',
                'description': 'Minutes to lock account after failed login attempts',
                'unit': 'minutes',
                'requires_restart': True,
            },
            {
                'setting_name': 'force_password_change_days',
                'setting_value': '90',
                'data_type': 'integer',
                'category': 'authentication',
                'description': 'Days before forcing password change (0 = disabled)',
                'unit': 'days',
            },
            
            # Password Policy Settings
            {
                'setting_name': 'password_min_length',
                'setting_value': '8',
                'data_type': 'integer',
                'category': 'password_policy',
                'description': 'Minimum required password length',
                'unit': 'characters',
                'requires_restart': True,
            },
            {
                'setting_name': 'password_require_uppercase',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'password_policy',
                'description': 'Require at least one uppercase letter in passwords',
                'requires_restart': True,
            },
            {
                'setting_name': 'password_require_numbers',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'password_policy',
                'description': 'Require at least one number in passwords',
                'requires_restart': True,
            },
            {
                'setting_name': 'password_require_special_chars',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'password_policy',
                'description': 'Require at least one special character in passwords',
                'requires_restart': True,
            },
            
            # Two-Factor Authentication
            {
                'setting_name': 'two_factor_required_roles',
                'setting_value': 'admin,qa,regulatory',
                'data_type': 'string',
                'category': 'two_factor_auth',
                'description': 'Comma-separated roles that require 2FA (admin,qa,regulatory)',
                'requires_restart': True,
            },
            {
                'setting_name': 'two_factor_grace_period_days',
                'setting_value': '7',
                'data_type': 'integer',
                'category': 'two_factor_auth',
                'description': 'Days users can delay setting up required 2FA',
                'unit': 'days',
            },
            
            # Security Logging
            {
                'setting_name': 'log_failed_logins',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'security_logging',
                'description': 'Log all failed login attempts',
            },
            {
                'setting_name': 'log_permission_denials',
                'setting_value': 'true',
                'data_type': 'boolean',
                'category': 'security_logging',
                'description': 'Log access attempts to restricted resources',
            },
            {
                'setting_name': 'security_log_retention_days',
                'setting_value': '365',
                'data_type': 'integer',
                'category': 'security_logging',
                'description': 'Days to retain security audit logs',
                'unit': 'days',
            },
        ]
        
        created_count, updated_count = self._create_or_update_settings(
            SessionManagementSettings, settings, update_existing
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🔐 Session Settings: {created_count} created, {updated_count} updated'
            )
        )

    def initialize_production_limits(self, update_existing):
        """Initialize production system limits and constraints"""
        
        settings = [
            # Batch Limits
            {
                'setting_name': 'max_concurrent_batches',
                'setting_value': '10',
                'data_type': 'integer',
                'category': 'batch_limits',
                'description': 'Maximum number of batches that can be in production simultaneously',
                'unit': 'batches',
                'min_value': 1,
                'max_value': 50,
            },
            {
                'setting_name': 'max_batch_size',
                'setting_value': '10000',
                'data_type': 'integer',
                'category': 'batch_limits',
                'description': 'Maximum allowed batch size for production',
                'unit': 'units',
                'min_value': 1,
                'max_value': 100000,
            },
            {
                'setting_name': 'min_batch_size',
                'setting_value': '100',
                'data_type': 'integer',
                'category': 'batch_limits',
                'description': 'Minimum allowed batch size for production',
                'unit': 'units',
                'min_value': 1,
                'max_value': 10000,
            },
            
            # Pagination Limits
            {
                'setting_name': 'api_default_page_size',
                'setting_value': '20',
                'data_type': 'integer',
                'category': 'pagination_limits',
                'description': 'Default page size for API responses',
                'unit': 'items',
                'min_value': 5,
                'max_value': 100,
            },
            {
                'setting_name': 'api_max_page_size',
                'setting_value': '100',
                'data_type': 'integer',
                'category': 'pagination_limits',
                'description': 'Maximum allowed page size for API requests',
                'unit': 'items',
                'min_value': 10,
                'max_value': 1000,
            },
            {
                'setting_name': 'dashboard_list_max_items',
                'setting_value': '200',
                'data_type': 'integer',
                'category': 'pagination_limits',
                'description': 'Maximum items to display in dashboard lists',
                'unit': 'items',
                'min_value': 50,
                'max_value': 1000,
            },
            
            # File Upload Limits
            {
                'setting_name': 'max_file_upload_size_mb',
                'setting_value': '50',
                'data_type': 'integer',
                'category': 'file_limits',
                'description': 'Maximum file upload size for attachments and documents',
                'unit': 'MB',
                'min_value': 1,
                'max_value': 500,
            },
            {
                'setting_name': 'max_files_per_batch',
                'setting_value': '20',
                'data_type': 'integer',
                'category': 'file_limits',
                'description': 'Maximum number of files that can be attached to a single batch',
                'unit': 'files',
                'min_value': 1,
                'max_value': 100,
            },
            {
                'setting_name': 'allowed_file_extensions',
                'setting_value': 'pdf,doc,docx,xls,xlsx,txt,jpg,jpeg,png',
                'data_type': 'string',
                'category': 'file_limits',
                'description': 'Comma-separated list of allowed file extensions',
            },
            
            # Concurrent Operations
            {
                'setting_name': 'max_concurrent_users',
                'setting_value': '100',
                'data_type': 'integer',
                'category': 'concurrent_operations',
                'description': 'Maximum number of concurrent active users',
                'unit': 'users',
                'min_value': 10,
                'max_value': 1000,
            },
            {
                'setting_name': 'max_concurrent_phase_executions',
                'setting_value': '50',
                'data_type': 'integer',
                'category': 'concurrent_operations',
                'description': 'Maximum number of phases that can be executing simultaneously',
                'unit': 'phases',
                'min_value': 5,
                'max_value': 200,
            },
            {
                'setting_name': 'max_api_requests_per_minute',
                'setting_value': '1000',
                'data_type': 'integer',
                'category': 'concurrent_operations',
                'description': 'Maximum API requests per minute per user',
                'unit': 'requests/min',
                'min_value': 10,
                'max_value': 10000,
            },
            
            # Resource Limits
            {
                'setting_name': 'database_query_timeout_seconds',
                'setting_value': '30',
                'data_type': 'integer',
                'category': 'resource_limits',
                'description': 'Maximum time to wait for database queries',
                'unit': 'seconds',
                'min_value': 5,
                'max_value': 300,
                'requires_restart': True,
            },
            {
                'setting_name': 'export_max_records',
                'setting_value': '10000',
                'data_type': 'integer',
                'category': 'resource_limits',
                'description': 'Maximum records allowed in data exports',
                'unit': 'records',
                'min_value': 100,
                'max_value': 100000,
            },
            {
                'setting_name': 'report_generation_timeout_minutes',
                'setting_value': '15',
                'data_type': 'integer',
                'category': 'resource_limits',
                'description': 'Maximum time to wait for report generation',
                'unit': 'minutes',
                'min_value': 1,
                'max_value': 60,
            },
        ]
        
        created_count, updated_count = self._create_or_update_settings(
            ProductionLimitsSettings, settings, update_existing
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'⚙️ Production Limits: {created_count} created, {updated_count} updated'
            )
        )

    def _create_or_update_settings(self, model_class, settings, update_existing):
        """Helper method to create or update settings"""
        created_count = 0
        updated_count = 0
        
        for setting_data in settings:
            setting_name = setting_data['setting_name']
            
            try:
                setting_obj, created = model_class.objects.get_or_create(
                    setting_name=setting_name,
                    defaults=setting_data
                )
                
                if created:
                    created_count += 1
                elif update_existing:
                    # Update existing setting with new values
                    for key, value in setting_data.items():
                        if key != 'setting_name':  # Don't update the key field
                            setattr(setting_obj, key, value)
                    setting_obj.save()
                    updated_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Failed to create/update {setting_name}: {e}')
                )
        
        return created_count, updated_count