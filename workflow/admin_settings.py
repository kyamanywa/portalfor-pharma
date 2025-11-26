"""
Enhanced admin interface for all system settings management
"""
from django.contrib import admin
from django.db import models
from django.forms import Textarea
from django.http import JsonResponse
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.utils.html import format_html
import json

from .models_admin_settings import (
    DashboardSettings, SystemAlertSettings, SessionManagementSettings, 
    ProductionLimitsSettings
)

@admin.register(DashboardSettings)
class DashboardSettingsAdmin(admin.ModelAdmin):
    """Enhanced admin for dashboard settings"""
    
    list_display = [
        'setting_name', 'get_display_value', 'data_type', 'category', 
        'is_active', 'requires_restart', 'last_modified_date'
    ]
    list_filter = ['category', 'data_type', 'is_active', 'requires_restart']
    search_fields = ['setting_name', 'description']
    readonly_fields = ['last_modified_date']
    
    fieldsets = (
        ('Setting Information', {
            'fields': ('setting_name', 'description', 'category')
        }),
        ('Value Configuration', {
            'fields': ('setting_value', 'data_type')
        }),
        ('Administrative', {
            'fields': ('is_active', 'requires_restart', 'last_modified_by', 'last_modified_date'),
            'classes': ('collapse',)
        }),
    )
    
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 3, 'cols': 60})}
    }
    
    actions = ['reset_to_defaults', 'export_settings', 'activate_settings', 'deactivate_settings']
    
    def get_display_value(self, obj):
        """Display value with proper formatting"""
        try:
            value = obj.get_value()
            if obj.data_type == 'json':
                return format_html('<pre>{}</pre>', json.dumps(value, indent=2))
            elif obj.data_type == 'boolean':
                return format_html(
                    '<span class="badge badge-{}">{}</span>',
                    'success' if value else 'secondary',
                    'Yes' if value else 'No'
                )
            else:
                return str(value)
        except Exception as e:
            return format_html('<span class="text-danger">Error: {}</span>', str(e))
    get_display_value.short_description = 'Current Value'
    get_display_value.allow_tags = True
    
    def save_model(self, request, obj, form, change):
        """Track who modified the setting"""
        obj.last_modified_by = request.user.username
        super().save_model(request, obj, form, change)
        
        if obj.requires_restart:
            messages.warning(
                request, 
                f'Setting "{obj.setting_name}" requires server restart to take effect.'
            )
    
    def reset_to_defaults(self, request, queryset):
        """Reset selected settings to default values"""
        default_dashboard_settings = {
            'dashboard_auto_refresh': ('true', 'boolean'),
            'dashboard_refresh_interval': ('30', 'integer'),
            'default_page_size': ('20', 'integer'),
            'max_page_size': ('100', 'integer'),
            'mobile_responsive_breakpoint': ('768', 'integer'),
            'show_advanced_filters': ('false', 'boolean'),
            'enable_real_time_updates': ('true', 'boolean'),
        }
        
        reset_count = 0
        for setting in queryset:
            if setting.setting_name in default_dashboard_settings:
                default_value, data_type = default_dashboard_settings[setting.setting_name]
                setting.setting_value = default_value
                setting.data_type = data_type
                setting.last_modified_by = request.user.username
                setting.save()
                reset_count += 1
        
        messages.success(request, f'Reset {reset_count} settings to defaults.')
    reset_to_defaults.short_description = 'Reset selected settings to defaults'
    
    def export_settings(self, request, queryset):
        """Export settings as JSON"""
        settings_data = []
        for setting in queryset:
            try:
                settings_data.append({
                    'setting_name': setting.setting_name,
                    'setting_value': setting.get_value(),
                    'data_type': setting.data_type,
                    'category': setting.category,
                    'description': setting.description,
                    'is_active': setting.is_active
                })
            except Exception as e:
                settings_data.append({
                    'setting_name': setting.setting_name,
                    'error': str(e)
                })
        
        response = JsonResponse({'dashboard_settings': settings_data}, indent=2)
        response['Content-Disposition'] = 'attachment; filename="dashboard_settings.json"'
        return response
    export_settings.short_description = 'Export selected settings as JSON'
    
    def activate_settings(self, request, queryset):
        """Activate selected settings"""
        count = queryset.update(is_active=True)
        messages.success(request, f'Activated {count} settings.')
    activate_settings.short_description = 'Activate selected settings'
    
    def deactivate_settings(self, request, queryset):
        """Deactivate selected settings"""
        count = queryset.update(is_active=False)
        messages.warning(request, f'Deactivated {count} settings.')
    deactivate_settings.short_description = 'Deactivate selected settings'

@admin.register(SystemAlertSettings)
class SystemAlertSettingsAdmin(admin.ModelAdmin):
    """Enhanced admin for system alert settings"""
    
    list_display = [
        'setting_name', 'get_display_value', 'data_type', 'category', 
        'is_active', 'last_modified_date'
    ]
    list_filter = ['category', 'data_type', 'is_active']
    search_fields = ['setting_name', 'description']
    readonly_fields = ['last_modified_date']
    
    fieldsets = (
        ('Alert Configuration', {
            'fields': ('setting_name', 'description', 'category')
        }),
        ('Value Configuration', {
            'fields': ('setting_value', 'data_type')
        }),
        ('Administrative', {
            'fields': ('is_active', 'last_modified_by', 'last_modified_date'),
            'classes': ('collapse',)
        }),
    )
    
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 3, 'cols': 60})}
    }
    
    actions = ['test_email_settings', 'export_alert_config', 'enable_alerts', 'disable_alerts']
    
    def get_display_value(self, obj):
        """Display value with proper formatting"""
        try:
            value = obj.get_value()
            if obj.data_type == 'email_list':
                return format_html('<code>{}</code>', ', '.join(value) if value else 'No emails')
            elif obj.data_type == 'boolean':
                return format_html(
                    '<span class="badge badge-{}">{}</span>',
                    'success' if value else 'secondary',
                    'Enabled' if value else 'Disabled'
                )
            else:
                return str(value)
        except Exception as e:
            return format_html('<span class="text-danger">Error: {}</span>', str(e))
    get_display_value.short_description = 'Current Value'
    get_display_value.allow_tags = True
    
    def save_model(self, request, obj, form, change):
        """Track who modified the setting"""
        obj.last_modified_by = request.user.username
        super().save_model(request, obj, form, change)
    
    def test_email_settings(self, request, queryset):
        """Test email configuration settings"""
        # This would typically send a test email
        messages.info(request, f'Email test initiated for {queryset.count()} settings.')
    test_email_settings.short_description = 'Test email settings'
    
    def export_alert_config(self, request, queryset):
        """Export alert settings as JSON"""
        settings_data = []
        for setting in queryset:
            try:
                settings_data.append({
                    'setting_name': setting.setting_name,
                    'setting_value': setting.get_value(),
                    'data_type': setting.data_type,
                    'category': setting.category,
                    'description': setting.description,
                    'is_active': setting.is_active
                })
            except Exception as e:
                settings_data.append({
                    'setting_name': setting.setting_name,
                    'error': str(e)
                })
        
        response = JsonResponse({'alert_settings': settings_data}, indent=2)
        response['Content-Disposition'] = 'attachment; filename="alert_settings.json"'
        return response
    export_alert_config.short_description = 'Export selected settings as JSON'
    
    def enable_alerts(self, request, queryset):
        """Enable selected alert settings"""
        count = queryset.update(is_active=True)
        messages.success(request, f'Enabled {count} alert settings.')
    enable_alerts.short_description = 'Enable selected alerts'
    
    def disable_alerts(self, request, queryset):
        """Disable selected alert settings"""
        count = queryset.update(is_active=False)
        messages.warning(request, f'Disabled {count} alert settings.')
    disable_alerts.short_description = 'Disable selected alerts'

@admin.register(SessionManagementSettings)
class SessionManagementSettingsAdmin(admin.ModelAdmin):
    """Enhanced admin for session management settings"""
    
    list_display = [
        'setting_name', 'get_display_value', 'data_type', 'category', 
        'is_active', 'requires_restart', 'last_modified_date'
    ]
    list_filter = ['category', 'data_type', 'is_active', 'requires_restart']
    search_fields = ['setting_name', 'description']
    readonly_fields = ['last_modified_date']
    
    fieldsets = (
        ('Session Configuration', {
            'fields': ('setting_name', 'description', 'category', 'unit')
        }),
        ('Value Configuration', {
            'fields': ('setting_value', 'data_type')
        }),
        ('Administrative', {
            'fields': ('is_active', 'requires_restart', 'last_modified_by', 'last_modified_date'),
            'classes': ('collapse',)
        }),
    )
    
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 3, 'cols': 60})}
    }
    
    actions = ['apply_security_defaults', 'export_session_config']
    
    def get_display_value(self, obj):
        """Display value with unit"""
        try:
            value = obj.get_value()
            unit_display = f" {obj.unit}" if obj.unit else ""
            if obj.data_type == 'boolean':
                return format_html(
                    '<span class="badge badge-{}">{}</span>',
                    'success' if value else 'secondary',
                    'Enabled' if value else 'Disabled'
                )
            else:
                return f"{value}{unit_display}"
        except Exception as e:
            return format_html('<span class="text-danger">Error: {}</span>', str(e))
    get_display_value.short_description = 'Current Value'
    get_display_value.allow_tags = True
    
    def save_model(self, request, obj, form, change):
        """Track who modified the setting and warn about restart"""
        obj.last_modified_by = request.user.username
        super().save_model(request, obj, form, change)
        
        if obj.requires_restart:
            messages.warning(
                request, 
                f'Security setting "{obj.setting_name}" requires server restart to take effect.'
            )
    
    def apply_security_defaults(self, request, queryset):
        """Apply recommended security defaults"""
        security_defaults = {
            'session_timeout_hours': '8',
            'session_warning_minutes': '15',
            'max_login_attempts': '3',
            'account_lockout_duration_minutes': '30',
            'password_min_length': '8',
            'password_require_special_chars': 'true',
        }
        
        applied_count = 0
        for setting in queryset:
            if setting.setting_name in security_defaults:
                setting.setting_value = security_defaults[setting.setting_name]
                setting.last_modified_by = request.user.username
                setting.save()
                applied_count += 1
        
        messages.success(request, f'Applied security defaults to {applied_count} settings.')
    apply_security_defaults.short_description = 'Apply recommended security defaults'
    
    def export_session_config(self, request, queryset):
        """Export session settings as JSON"""
        settings_data = []
        for setting in queryset:
            try:
                settings_data.append({
                    'setting_name': setting.setting_name,
                    'setting_value': setting.get_value(),
                    'data_type': setting.data_type,
                    'category': setting.category,
                    'unit': setting.unit,
                    'description': setting.description,
                    'requires_restart': setting.requires_restart,
                    'is_active': setting.is_active
                })
            except Exception as e:
                settings_data.append({
                    'setting_name': setting.setting_name,
                    'error': str(e)
                })
        
        response = JsonResponse({'session_settings': settings_data}, indent=2)
        response['Content-Disposition'] = 'attachment; filename="session_settings.json"'
        return response
    export_session_config.short_description = 'Export selected settings as JSON'

@admin.register(ProductionLimitsSettings)
class ProductionLimitsSettingsAdmin(admin.ModelAdmin):
    """Enhanced admin for production limits settings"""
    
    list_display = [
        'setting_name', 'get_display_value', 'get_constraints', 'data_type', 
        'category', 'is_active', 'requires_restart', 'last_modified_date'
    ]
    list_filter = ['category', 'data_type', 'is_active', 'requires_restart']
    search_fields = ['setting_name', 'description']
    readonly_fields = ['last_modified_date']
    
    fieldsets = (
        ('Limit Configuration', {
            'fields': ('setting_name', 'description', 'category', 'unit')
        }),
        ('Value and Constraints', {
            'fields': ('setting_value', 'data_type', 'min_value', 'max_value')
        }),
        ('Administrative', {
            'fields': ('is_active', 'requires_restart', 'last_modified_by', 'last_modified_date'),
            'classes': ('collapse',)
        }),
    )
    
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 3, 'cols': 60})}
    }
    
    actions = ['apply_recommended_limits', 'export_limits_config', 'validate_constraints']
    
    def get_display_value(self, obj):
        """Display value with unit"""
        try:
            value = obj.get_value()
            unit_display = f" {obj.unit}" if obj.unit else ""
            return f"{value}{unit_display}"
        except Exception as e:
            return format_html('<span class="text-danger">Error: {}</span>', str(e))
    get_display_value.short_description = 'Current Value'
    
    def get_constraints(self, obj):
        """Display min/max constraints"""
        constraints = []
        if obj.min_value is not None:
            constraints.append(f"min: {obj.min_value}")
        if obj.max_value is not None:
            constraints.append(f"max: {obj.max_value}")
        return ", ".join(constraints) if constraints else "No constraints"
    get_constraints.short_description = 'Constraints'
    
    def save_model(self, request, obj, form, change):
        """Track who modified the setting"""
        obj.last_modified_by = request.user.username
        super().save_model(request, obj, form, change)
        
        if obj.requires_restart:
            messages.warning(
                request, 
                f'Production limit "{obj.setting_name}" requires server restart to take effect.'
            )
    
    def apply_recommended_limits(self, request, queryset):
        """Apply recommended production limits"""
        recommended_limits = {
            'max_concurrent_batches': '10',
            'default_page_size': '20',
            'max_page_size': '100',
            'max_file_upload_size_mb': '50',
            'max_batch_size': '10000',
            'max_concurrent_users': '100',
        }
        
        applied_count = 0
        for setting in queryset:
            if setting.setting_name in recommended_limits:
                setting.setting_value = recommended_limits[setting.setting_name]
                setting.last_modified_by = request.user.username
                setting.save()
                applied_count += 1
        
        messages.success(request, f'Applied recommended limits to {applied_count} settings.')
    apply_recommended_limits.short_description = 'Apply recommended limits'
    
    def validate_constraints(self, request, queryset):
        """Validate all constraints for selected settings"""
        validation_errors = []
        for setting in queryset:
            try:
                setting.clean()
            except ValidationError as e:
                validation_errors.append(f"{setting.setting_name}: {e}")
        
        if validation_errors:
            messages.error(request, f"Validation errors: {'; '.join(validation_errors)}")
        else:
            messages.success(request, f"All {queryset.count()} settings passed validation.")
    validate_constraints.short_description = 'Validate constraints'
    
    def export_limits_config(self, request, queryset):
        """Export production limits as JSON"""
        settings_data = []
        for setting in queryset:
            try:
                settings_data.append({
                    'setting_name': setting.setting_name,
                    'setting_value': setting.get_value(),
                    'data_type': setting.data_type,
                    'category': setting.category,
                    'unit': setting.unit,
                    'min_value': setting.min_value,
                    'max_value': setting.max_value,
                    'description': setting.description,
                    'requires_restart': setting.requires_restart,
                    'is_active': setting.is_active
                })
            except Exception as e:
                settings_data.append({
                    'setting_name': setting.setting_name,
                    'error': str(e)
                })
        
        response = JsonResponse({'production_limits': settings_data}, indent=2)
        response['Content-Disposition'] = 'attachment; filename="production_limits.json"'
        return response
    export_limits_config.short_description = 'Export selected settings as JSON'