from django.db import models
from django.conf import settings
from bmr.models import BMR
from workflow.models import BatchPhaseExecution

class DashboardMetrics(models.Model):
    """Dashboard metrics and KPIs for different user roles"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    
    # General metrics
    active_batches = models.IntegerField(default=0)
    completed_phases_today = models.IntegerField(default=0)
    pending_phases = models.IntegerField(default=0)
    rejected_phases_today = models.IntegerField(default=0)
    
    # Role-specific metrics stored as JSON
    role_specific_data = models.JSONField(default=dict)
    
    class Meta:
        unique_together = ['user', 'date']
        verbose_name = 'Dashboard Metric'
        verbose_name_plural = 'Dashboard Metrics'
        ordering = ['-date', 'user__username']
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"
    
    @classmethod
    def record_metrics(cls, user, active_batches=0, completed_phases_today=0, pending_phases=0, rejected_phases_today=0, role_specific_data=None):
        """Record or update metrics for a user for today"""
        from django.utils import timezone
        today = timezone.now().date()
        
        metric, created = cls.objects.update_or_create(
            user=user,
            date=today,
            defaults={
                'active_batches': active_batches,
                'completed_phases_today': completed_phases_today,
                'pending_phases': pending_phases,
                'rejected_phases_today': rejected_phases_today,
                'role_specific_data': role_specific_data or {},
            }
        )
        return metric

class NotificationAlert(models.Model):
    """System notifications and alerts for users"""
    
    NOTIFICATION_TYPE_CHOICES = [
        ('phase_assigned', 'Phase Assigned'),
        ('phase_completed', 'Phase Completed'),
        ('phase_rejected', 'Phase Rejected'),
        ('bmr_approved', 'BMR Approved'),
        ('quality_alert', 'Quality Alert'),
        ('deadline_approaching', 'Deadline Approaching'),
        ('system_maintenance', 'System Maintenance'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Related objects
    bmr = models.ForeignKey(BMR, on_delete=models.CASCADE, null=True, blank=True)
    phase_execution = models.ForeignKey(
        BatchPhaseExecution, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    
    # Status
    is_read = models.BooleanField(default=False)
    is_acknowledged = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    read_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.recipient.username} - {self.title}"


class NotificationSettings(models.Model):
    """Admin-configurable settings for notification panel visibility by role"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('qa', 'QA'),
        ('qc', 'QC'),
        ('regulatory', 'Regulatory'),
        ('production_manager', 'Production Manager'),
        ('store_manager', 'Store Manager'),
        ('mixing_operator', 'Mixing Operator'),
        ('granulation_operator', 'Granulation Operator'),
        ('blending_operator', 'Blending Operator'),
        ('compression_operator', 'Compression Operator'),
        ('coating_operator', 'Coating Operator'),
        ('filling_operator', 'Filling Operator'),
        ('tube_filling_operator', 'Tube Filling Operator'),
        ('packing_operator', 'Packing Operator'),
        ('sorting_operator', 'Sorting Operator'),
        ('dispensing_operator', 'Dispensing Operator'),
    ]
    
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    show_notification_panel = models.BooleanField(
        default=True,
        help_text="Enable/disable notification panel for this role"
    )
    auto_refresh_notifications = models.BooleanField(
        default=True,
        help_text="Auto-refresh notifications without page reload"
    )
    notification_sound = models.BooleanField(
        default=False,
        help_text="Play sound when new notification arrives"
    )
    max_notifications_display = models.IntegerField(
        default=10,
        help_text="Maximum number of notifications to display in panel"
    )
    
    class Meta:
        verbose_name = 'Notification Setting'
        verbose_name_plural = 'Notification Settings'
        ordering = ['role']
    
    def __str__(self):
        return f"Notifications for {self.get_role_display()}"
    
    @classmethod
    def can_see_notifications(cls, user_role):
        """Check if a role can see the notification panel"""
        try:
            setting = cls.objects.get(role=user_role)
            return setting.show_notification_panel
        except cls.DoesNotExist:
            # Default: show notifications for all roles if not configured
            return True


class UserDashboardPreferences(models.Model):
    """User preferences for dashboard customization"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='dashboard_preferences'
    )
    
    # Layout preferences
    show_metrics_summary = models.BooleanField(default=True)
    show_recent_activities = models.BooleanField(default=True)
    show_pending_tasks = models.BooleanField(default=True)
    show_notifications = models.BooleanField(default=True)
    
    # Data refresh preferences
    auto_refresh_enabled = models.BooleanField(default=True)
    refresh_interval_seconds = models.IntegerField(default=30)
    
    # Custom dashboard layout stored as JSON
    layout_config = models.JSONField(default=dict)
    
    def __str__(self):
        return f"Dashboard preferences for {self.user.username}"


class DashboardPermission(models.Model):
    """Manage dashboard access permissions for users and roles"""
    
    DASHBOARD_CHOICES = [
        # Main Dashboard Access
        ('admin_dashboard', 'Admin Dashboard'),
        ('qa_dashboard', 'QA Dashboard'),
        ('production_manager', 'Production Manager Dashboard'),
        ('store_dashboard', 'Store Dashboard'),
        ('qc_dashboard', 'QC Dashboard'),
        ('regulatory_dashboard', 'Regulatory Dashboard'),
        ('operator_dashboard', 'Operator Dashboard'),
        
        # Admin Dashboard Sections
        ('analytics', 'Analytics & Metrics'),
        ('bmr_reports', 'BMR Print & Download Reports'),
        ('bmr_tracking', 'BMR Tracking'),
        ('live_tracking', 'Live Production Tracking'),
        ('machine_management', 'Machine Management'),
        ('quality_control', 'Quality Control Management'),
        ('inventory', 'Inventory Management'),
        ('quarantine', 'Quarantine Tracking'),
        ('phase_notifications', 'Phase Timing Alerts'),
        ('user_management', 'User Management'),
        ('system_health', 'System Health'),
        ('system_logs', 'System Logs'),
        
        # Production Manager Dashboard Sections
        ('pm_notifications', 'Production Manager Notifications'),
        ('pm_bmr_reports', 'Production Manager BMR Reports'),
        ('pm_timeline', 'Production Manager Timeline'),
        ('pm_analytics', 'Production Manager Analytics'),
        ('pm_bmr_tracking', 'Production Manager BMR Tracking'),
        ('pm_live_tracking', 'Production Manager Live Tracking'),
        ('pm_quarantine', 'Production Manager Quarantine'),
    ]
    
    name = models.CharField(max_length=50, choices=DASHBOARD_CHOICES, unique=True)
    description = models.TextField(blank=True)
    
    # Role-based permissions
    allowed_roles = models.JSONField(
        default=list, 
        blank=True, 
        null=False,
        help_text="List of roles that can access this dashboard"
    )
    
    def clean(self):
        """Validate the model fields"""
        from django.core.exceptions import ValidationError
        
        # Ensure allowed_roles is always a list
        if self.allowed_roles is None:
            self.allowed_roles = []
        elif not isinstance(self.allowed_roles, list):
            raise ValidationError({'allowed_roles': 'Must be a list of role names'})
    
    def save(self, *args, **kwargs):
        # Ensure allowed_roles is always a list, never None
        if self.allowed_roles is None:
            self.allowed_roles = []
        
        # Call clean before saving
        self.clean()
        
        super().save(*args, **kwargs)
    
    # User-specific permissions (overrides role permissions)
    allowed_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, help_text="Specific users who can access this dashboard")
    blocked_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='blocked_dashboards', help_text="Users specifically blocked from this dashboard")
    
    # System permissions
    requires_staff = models.BooleanField(default=False, help_text="Requires is_staff=True")
    requires_superuser = models.BooleanField(default=False, help_text="Requires is_superuser=True")
    
    # Enable/disable
    is_active = models.BooleanField(default=True)
    
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Dashboard Permission'
        verbose_name_plural = 'Dashboard Permissions'
    
    def __str__(self):
        return f"{self.get_name_display()}"
    
    def user_has_access(self, user):
        """Check if a user has access to this dashboard"""
        if not self.is_active:
            return False
            
        # Check if user is specifically blocked
        if self.blocked_users.filter(id=user.id).exists():
            return False
            
        # Check if user is specifically allowed
        if self.allowed_users.filter(id=user.id).exists():
            return True
            
        # Check system permissions
        if self.requires_superuser and not user.is_superuser:
            return False
            
        if self.requires_staff and not user.is_staff:
            return False
            
        # Check role permissions
        # If allowed_roles is empty, allow all authenticated users
        if not self.allowed_roles:
            return True
            
        if hasattr(user, 'role') and user.role in self.allowed_roles:
            return True
            
        return False
