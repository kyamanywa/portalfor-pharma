from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group
from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import CustomUser, UserSession, SecuritySettings

# Unregister the default Group admin if we don't need it
# admin.site.unregister(Group)

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'employee_id', 'department')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'employee_id', 'department', 'is_active', 'is_staff')

@admin.register(CustomUser)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'employee_id', 'department', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('role', 'department', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'employee_id')
    ordering = ('username',)
    actions = ['reset_password_to_default']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        ('Role & Department', {'fields': ('role', 'employee_id', 'department')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
        ('Additional', {'fields': ('signature', 'is_active_operator')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'role', 'employee_id', 'department', 'password1', 'password2'),
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Override to use different forms for add and change"""
        if obj is None:
            kwargs['form'] = self.add_form
        return super().get_form(request, obj, **kwargs)
    
    def reset_password_to_default(self, request, queryset):
        """Reset selected users' passwords to default pattern"""
        count = 0
        reset_info = []
        
        for user in queryset:
            # Set default password based on role
            if user.role:
                default_password = f"{user.role.split('_')[0]}123"
            else:
                default_password = "user123"
            
            user.set_password(default_password)
            user.save()
            reset_info.append(f"{user.username}: {default_password}")
            count += 1
        
        password_list = "\n".join(reset_info)
        self.message_user(
            request,
            f"Successfully reset passwords for {count} users:\n{password_list}",
            messages.SUCCESS
        )
    
    reset_password_to_default.short_description = "Reset passwords to default (role123)"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:user_id>/reset-password/',
                self.admin_site.admin_view(self.reset_single_password),
                name='accounts_customuser_reset_password',
            ),
        ]
        return custom_urls + urls
    
    def reset_single_password(self, request, user_id):
        """Reset a single user's password with custom value"""
        user = get_object_or_404(CustomUser, pk=user_id)
        
        if request.method == 'POST':
            new_password = request.POST.get('new_password', '')
            if new_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, f"Password for {user.username} reset to: {new_password}")
                return redirect('admin:accounts_customuser_changelist')
        
        # Set default password based on role
        if user.role:
            suggested_password = f"{user.role.split('_')[0]}123"
        else:
            suggested_password = "user123"
        
        context = {
            'user': user,
            'suggested_password': suggested_password,
            'title': f'Reset Password for {user.username}',
            'opts': self.model._meta,
        }
        
        return render(request, 'admin/accounts/reset_password.html', context)

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time', 'logout_time', 'ip_address')
    list_filter = ('login_time', 'logout_time')
    search_fields = ('user__username', 'user__email', 'ip_address')
    readonly_fields = ('login_time',)
    ordering = ('-login_time',)


@admin.register(SecuritySettings)
class SecuritySettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for security configuration.
    Only one instance exists - click to edit settings.
    """
    list_display = (
        'get_title',
        'axes_enabled',
        'axes_failure_limit',
        'get_cooloff_display',
        'password_min_length',
        'session_timeout_hours',
        'last_updated',
    )
    
    fieldsets = (
        ('🔒 Brute Force Protection', {
            'fields': (
                'axes_enabled',
                'axes_failure_limit',
                'axes_cooloff_hours',
            ),
            'description': 'Configure automatic account lockout after failed login attempts.'
        }),
        ('🔑 Password Security', {
            'fields': ('password_min_length',),
            'description': 'Set password complexity requirements.'
        }),
        ('⏱️ Session Management', {
            'fields': ('session_timeout_hours',),
            'description': 'Configure automatic logout timeouts.'
        }),
        ('📝 Audit Trail', {
            'fields': ('last_updated', 'updated_by'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ('last_updated', 'updated_by')
    
    def get_title(self, obj):
        return "Security Configuration"
    get_title.short_description = "Configuration"
    
    def get_cooloff_display(self, obj):
        minutes = obj.get_cooloff_minutes()
        if minutes < 60:
            return f"{int(minutes)} minutes"
        else:
            hours = minutes / 60
            return f"{hours:.1f} hour(s)"
    get_cooloff_display.short_description = "Lockout Duration"
    
    def has_add_permission(self, request):
        """Only allow one instance"""
        return not SecuritySettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of settings"""
        return False
    
    def save_model(self, request, obj, form, change):
        """Track who updated the settings"""
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        messages.success(
            request,
            f"✅ Security settings updated! Changes will apply after server restart."
        )
    
    def changelist_view(self, request, extra_context=None):
        """
        If no settings exist, create one and redirect to edit.
        If settings exist, redirect directly to edit page.
        """
        if not SecuritySettings.objects.exists():
            # Create default settings
            obj = SecuritySettings.objects.create()
            obj.updated_by = request.user
            obj.save()
        
        # Always redirect to the single settings instance
        obj = SecuritySettings.objects.first()
        return redirect('admin:accounts_securitysettings_change', obj.pk)
    
    class Media:
        css = {
            'all': ('admin/css/forms.css',)
        }
