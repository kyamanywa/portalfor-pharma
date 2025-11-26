from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
import json
from .models import DashboardMetrics, NotificationAlert, UserDashboardPreferences, DashboardPermission

class DashboardPermissionAdminForm(forms.ModelForm):
    """Custom form for DashboardPermission admin with proper JSONField handling"""
    
    allowed_roles_text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 60}),
        help_text='Enter roles as a JSON list. Example: ["qa", "admin", "production_manager"] or [] for no roles',
        required=False,
        label='Allowed Roles (JSON)'
    )
    
    class Meta:
        model = DashboardPermission
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Convert allowed_roles list to JSON string for editing
            allowed_roles = self.instance.allowed_roles
            if allowed_roles is None:
                allowed_roles = []
            self.fields['allowed_roles_text'].initial = json.dumps(allowed_roles)
        else:
            # Default for new instances
            self.fields['allowed_roles_text'].initial = '[]'
    
    def clean_allowed_roles_text(self):
        """Validate and convert JSON text to list"""
        text = self.cleaned_data.get('allowed_roles_text', '').strip()
        
        # If empty, default to empty list
        if not text:
            return []
        
        try:
            roles = json.loads(text)
            if not isinstance(roles, list):
                raise ValidationError('Allowed roles must be a JSON list (array)')
            
            # Validate each role is a string
            for role in roles:
                if not isinstance(role, str):
                    raise ValidationError('Each role must be a string')
            
            return roles
        except json.JSONDecodeError as e:
            raise ValidationError(f'Invalid JSON format: {e}')
    
    def save(self, commit=True):
        # Ensure allowed_roles is always a list
        allowed_roles = self.cleaned_data.get('allowed_roles_text', [])
        if allowed_roles is None:
            allowed_roles = []
        
        self.instance.allowed_roles = allowed_roles
        
        if commit:
            self.instance.save()
        return self.instance

@admin.register(DashboardMetrics)
class DashboardMetricsAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'active_batches', 'completed_phases_today', 'pending_phases']
    list_filter = ['date', 'user__role']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

@admin.register(NotificationAlert)
class NotificationAlertAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'title', 'is_read', 'priority', 'created_date']
    list_filter = ['notification_type', 'priority', 'is_read', 'created_date']
    search_fields = ['recipient__username', 'title', 'message']

@admin.register(UserDashboardPreferences)
class UserDashboardPreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'show_metrics_summary', 'show_recent_activities', 'auto_refresh_enabled']
    list_filter = ['show_metrics_summary', 'auto_refresh_enabled']
    search_fields = ['user__username']

@admin.register(DashboardPermission)
class DashboardPermissionAdmin(admin.ModelAdmin):
    form = DashboardPermissionAdminForm
    list_display = ['name', 'get_allowed_roles_display', 'requires_staff', 'requires_superuser', 'is_active']
    list_filter = ['requires_staff', 'requires_superuser', 'is_active']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('System Permissions', {
            'fields': ('requires_staff', 'requires_superuser'),
            'description': 'System-level permission requirements'
        }),
        ('Role-Based Access', {
            'fields': ('allowed_roles_text',),
            'description': 'Enter roles that can access this dashboard as a JSON list'
        }),
        ('User-Specific Access', {
            'fields': ('allowed_users', 'blocked_users'),
            'description': 'Override role permissions for specific users'
        }),
    )
    
    filter_horizontal = ['allowed_users', 'blocked_users']
    
    def get_allowed_roles_display(self, obj):
        """Display allowed roles in list view"""
        if not obj.allowed_roles:
            return "None"
        return ", ".join(obj.allowed_roles)
    get_allowed_roles_display.short_description = 'Allowed Roles'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return ['name']  # Make name readonly when editing
        return []