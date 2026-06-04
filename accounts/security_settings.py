"""
Security Settings Model - UI-configurable security settings
"""
from django.db import models


class SecuritySettings(models.Model):
    """
    Singleton model for security configuration.
    Only one instance should exist - managed through admin.
    """
    # Brute Force Protection
    axes_enabled = models.BooleanField(
        default=True,
        verbose_name="Enable Brute Force Protection",
        help_text="Lock accounts after multiple failed login attempts"
    )
    axes_failure_limit = models.IntegerField(
        default=5,
        verbose_name="Failed Login Attempts Limit",
        help_text="Number of failed attempts before account lockout (e.g., 3, 5, 10)"
    )
    axes_cooloff_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0,
        verbose_name="Lockout Duration (Hours)",
        help_text="How long to lock account (e.g., 0.25 = 15 min, 0.5 = 30 min, 1 = 1 hour)"
    )
    
    # Password Settings
    password_min_length = models.IntegerField(
        default=12,
        verbose_name="Minimum Password Length",
        help_text="Minimum characters required for passwords"
    )
    
    # Session Settings
    session_timeout_hours = models.IntegerField(
        default=12,
        verbose_name="Session Timeout (Hours)",
        help_text="Auto-logout users after this many hours of inactivity"
    )
    
    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='security_settings_updates'
    )
    
    class Meta:
        verbose_name = "Security Configuration"
        verbose_name_plural = "Security Configuration"
        db_table = 'security_settings'
    
    def __str__(self):
        return f"Security Settings (Updated: {self.last_updated.strftime('%Y-%m-%d %H:%M')})"
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)"""
        if not self.pk and SecuritySettings.objects.exists():
            # If this is a new instance but one already exists, update the existing one
            existing = SecuritySettings.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
    
    def get_cooloff_minutes(self):
        """Return cooloff time in minutes for display"""
        return float(self.axes_cooloff_hours) * 60
