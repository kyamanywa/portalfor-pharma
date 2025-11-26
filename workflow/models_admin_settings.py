"""
Extended admin-manageable settings for the KPI Operations System
This module contains all the additional settings that need centralized admin management
"""
from django.db import models
from django.core.exceptions import ValidationError
import json

class DashboardSettings(models.Model):
    """Centralized dashboard configuration settings"""
    
    # Setting identification
    setting_name = models.CharField(max_length=100, unique=True, db_index=True)
    setting_value = models.TextField()  # Store as text, converted based on data_type
    data_type = models.CharField(
        max_length=20,
        choices=[
            ('integer', 'Integer'),
            ('float', 'Float'),
            ('boolean', 'Boolean'),
            ('string', 'String'),
            ('json', 'JSON'),
        ],
        default='string'
    )
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('dashboard_ui', 'Dashboard UI'),
            ('refresh_timing', 'Refresh Timing'),
            ('pagination', 'Pagination'),
            ('user_preferences', 'User Preferences'),
            ('mobile_responsive', 'Mobile Responsive'),
        ],
        default='dashboard_ui'
    )
    
    # Administrative fields
    is_active = models.BooleanField(default=True)
    requires_restart = models.BooleanField(default=False, help_text="Whether changing this setting requires server restart")
    last_modified_by = models.CharField(max_length=150, blank=True)
    last_modified_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Dashboard Setting'
        verbose_name_plural = 'Dashboard Settings'
        ordering = ['category', 'setting_name']
    
    def __str__(self):
        return f"{self.category}: {self.setting_name}"
    
    def get_value(self):
        """Convert stored string value to appropriate type"""
        try:
            if self.data_type == 'integer':
                return int(self.setting_value)
            elif self.data_type == 'float':
                return float(self.setting_value)
            elif self.data_type == 'boolean':
                return self.setting_value.lower() in ('true', '1', 'yes', 'on')
            elif self.data_type == 'json':
                return json.loads(self.setting_value)
            else:  # string
                return self.setting_value
        except (ValueError, json.JSONDecodeError):
            raise ValidationError(f"Invalid {self.data_type} value: {self.setting_value}")
    
    def set_value(self, value):
        """Set value with appropriate type conversion"""
        if self.data_type == 'json':
            self.setting_value = json.dumps(value)
        else:
            self.setting_value = str(value)
    
    @classmethod
    def get_setting(cls, setting_name, default=None):
        """Get setting value with fallback to default"""
        try:
            setting = cls.objects.get(setting_name=setting_name, is_active=True)
            return setting.get_value()
        except cls.DoesNotExist:
            return default

class SystemAlertSettings(models.Model):
    """System-wide alert and notification configuration"""
    
    setting_name = models.CharField(max_length=100, unique=True, db_index=True)
    setting_value = models.TextField()
    data_type = models.CharField(
        max_length=20,
        choices=[
            ('integer', 'Integer'),
            ('float', 'Float'),
            ('boolean', 'Boolean'),
            ('string', 'String'),
            ('email_list', 'Email List'),
        ],
        default='string'
    )
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('email_alerts', 'Email Alerts'),
            ('sms_alerts', 'SMS Alerts'),
            ('dashboard_notifications', 'Dashboard Notifications'),
            ('overrun_alerts', 'Phase Overrun Alerts'),
            ('quality_alerts', 'Quality Alerts'),
            ('system_maintenance', 'System Maintenance'),
        ],
        default='dashboard_notifications'
    )
    
    is_active = models.BooleanField(default=True)
    last_modified_by = models.CharField(max_length=150, blank=True)
    last_modified_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'System Alert Setting'
        verbose_name_plural = 'System Alert Settings'
        ordering = ['category', 'setting_name']
    
    def __str__(self):
        return f"{self.category}: {self.setting_name}"
    
    def get_value(self):
        """Convert stored string value to appropriate type"""
        try:
            if self.data_type == 'integer':
                return int(self.setting_value)
            elif self.data_type == 'float':
                return float(self.setting_value)
            elif self.data_type == 'boolean':
                return self.setting_value.lower() in ('true', '1', 'yes', 'on')
            elif self.data_type == 'email_list':
                # Parse comma-separated email list
                emails = [email.strip() for email in self.setting_value.split(',')]
                return [email for email in emails if email]  # Filter empty strings
            else:  # string
                return self.setting_value
        except ValueError:
            raise ValidationError(f"Invalid {self.data_type} value: {self.setting_value}")
    
    def set_value(self, value):
        """Set value with appropriate type conversion"""
        if self.data_type == 'email_list':
            if isinstance(value, list):
                self.setting_value = ', '.join(value)
            else:
                self.setting_value = str(value)
        else:
            self.setting_value = str(value)
    
    @classmethod
    def get_setting(cls, setting_name, default=None):
        """Get setting value with fallback to default"""
        try:
            setting = cls.objects.get(setting_name=setting_name, is_active=True)
            return setting.get_value()
        except cls.DoesNotExist:
            return default

class SessionManagementSettings(models.Model):
    """Session management and security settings"""
    
    setting_name = models.CharField(max_length=100, unique=True, db_index=True)
    setting_value = models.TextField()
    data_type = models.CharField(
        max_length=20,
        choices=[
            ('integer', 'Integer'),
            ('float', 'Float'),
            ('boolean', 'Boolean'),
            ('string', 'String'),
        ],
        default='string'
    )
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=20, blank=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('session_timeout', 'Session Timeout'),
            ('authentication', 'Authentication'),
            ('password_policy', 'Password Policy'),
            ('two_factor_auth', 'Two Factor Authentication'),
            ('security_logging', 'Security Logging'),
        ],
        default='session_timeout'
    )
    
    is_active = models.BooleanField(default=True)
    requires_restart = models.BooleanField(default=False)
    last_modified_by = models.CharField(max_length=150, blank=True)
    last_modified_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Session Management Setting'
        verbose_name_plural = 'Session Management Settings'
        ordering = ['category', 'setting_name']
    
    def __str__(self):
        return f"{self.category}: {self.setting_name}"
    
    def get_value(self):
        """Convert stored string value to appropriate type"""
        try:
            if self.data_type == 'integer':
                return int(self.setting_value)
            elif self.data_type == 'float':
                return float(self.setting_value)
            elif self.data_type == 'boolean':
                return self.setting_value.lower() in ('true', '1', 'yes', 'on')
            else:  # string
                return self.setting_value
        except ValueError:
            raise ValidationError(f"Invalid {self.data_type} value: {self.setting_value}")
    
    @classmethod
    def get_setting(cls, setting_name, default=None):
        """Get setting value with fallback to default"""
        try:
            setting = cls.objects.get(setting_name=setting_name, is_active=True)
            return setting.get_value()
        except cls.DoesNotExist:
            return default

class ProductionLimitsSettings(models.Model):
    """Production system limits and constraints"""
    
    setting_name = models.CharField(max_length=100, unique=True, db_index=True)
    setting_value = models.TextField()
    data_type = models.CharField(
        max_length=20,
        choices=[
            ('integer', 'Integer'),
            ('float', 'Float'),
            ('string', 'String'),
        ],
        default='integer'
    )
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=20, blank=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('batch_limits', 'Batch Limits'),
            ('pagination_limits', 'Pagination Limits'),
            ('file_limits', 'File Upload Limits'),
            ('concurrent_operations', 'Concurrent Operations'),
            ('resource_limits', 'Resource Limits'),
        ],
        default='batch_limits'
    )
    
    min_value = models.FloatField(null=True, blank=True, help_text="Minimum allowed value")
    max_value = models.FloatField(null=True, blank=True, help_text="Maximum allowed value")
    
    is_active = models.BooleanField(default=True)
    requires_restart = models.BooleanField(default=False)
    last_modified_by = models.CharField(max_length=150, blank=True)
    last_modified_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Production Limit Setting'
        verbose_name_plural = 'Production Limit Settings'
        ordering = ['category', 'setting_name']
    
    def __str__(self):
        return f"{self.category}: {self.setting_name}"
    
    def clean(self):
        """Validate min/max constraints"""
        super().clean()
        try:
            value = self.get_value()
            if self.min_value is not None and value < self.min_value:
                raise ValidationError(f"Value {value} is below minimum {self.min_value}")
            if self.max_value is not None and value > self.max_value:
                raise ValidationError(f"Value {value} exceeds maximum {self.max_value}")
        except (ValueError, ValidationError):
            pass  # Let get_value handle validation errors
    
    def get_value(self):
        """Convert stored string value to appropriate type"""
        try:
            if self.data_type == 'integer':
                return int(self.setting_value)
            elif self.data_type == 'float':
                return float(self.setting_value)
            else:  # string
                return self.setting_value
        except ValueError:
            raise ValidationError(f"Invalid {self.data_type} value: {self.setting_value}")
    
    @classmethod
    def get_setting(cls, setting_name, default=None):
        """Get setting value with fallback to default"""
        try:
            setting = cls.objects.get(setting_name=setting_name, is_active=True)
            return setting.get_value()
        except cls.DoesNotExist:
            return default

# Helper functions for backwards compatibility
def get_dashboard_setting(setting_name, default=None):
    """Convenience function to get dashboard setting"""
    return DashboardSettings.get_setting(setting_name, default)

def get_alert_setting(setting_name, default=None):
    """Convenience function to get alert setting"""
    return SystemAlertSettings.get_setting(setting_name, default)

def get_session_setting(setting_name, default=None):
    """Convenience function to get session setting"""
    return SessionManagementSettings.get_setting(setting_name, default)

def get_production_limit(setting_name, default=None):
    """Convenience function to get production limit"""
    return ProductionLimitsSettings.get_setting(setting_name, default)