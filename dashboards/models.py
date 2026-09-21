from datetime import timedelta

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
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
        ('capa_overdue', 'CAPA Overdue'),
        ('capa_review_due', 'CAPA Review Due'),
        ('change_control_overdue', 'Change Control Overdue'),
        ('change_control_due', 'Change Control Due'),
        ('calibration_overdue', 'Calibration Overdue'),
        ('calibration_due', 'Calibration Due'),
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
        ('maintenance', 'Maintenance Technician'),
        ('equipment_operator', 'Equipment Operator'),
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


class QualityInspectionLot(models.Model):
    """SAP-QM-style inspection lot linked to the existing BMR workflow."""

    INSPECTION_TYPE_CHOICES = [
        ('in_process', 'In-Process Inspection'),
        ('final', 'Final Inspection'),
        ('quarantine', 'Quarantine Sample'),
        ('material', 'Material Inspection'),
        ('manual', 'Manual Inspection'),
    ]
    ORIGIN_CHOICES = [
        ('workflow_phase', 'Workflow Phase'),
        ('quarantine', 'Quarantine'),
        ('manual', 'Manual'),
    ]
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('released', 'Released'),
        ('in_inspection', 'In Inspection'),
        ('results_recorded', 'Results Recorded'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    USAGE_DECISION_CHOICES = [
        ('', 'No Decision'),
        ('unrestricted', 'Release / Unrestricted Use'),
        ('rework', 'Rework Required'),
        ('reject', 'Reject'),
        ('hold', 'Hold / Investigate'),
    ]

    lot_number = models.CharField(max_length=30, unique=True, blank=True)
    bmr = models.ForeignKey(BMR, on_delete=models.CASCADE, related_name='quality_lots')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='quality_lots')
    phase_execution = models.OneToOneField(
        BatchPhaseExecution,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='quality_lot',
    )
    inspection_type = models.CharField(max_length=20, choices=INSPECTION_TYPE_CHOICES)
    origin = models.CharField(max_length=20, choices=ORIGIN_CHOICES, default='workflow_phase')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    usage_decision = models.CharField(max_length=20, choices=USAGE_DECISION_CHOICES, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quality_lots_created',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quality_lots_assigned',
    )
    decision_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quality_lots_decided',
    )
    decision_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    decision_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Quality Inspection Lot'
        verbose_name_plural = 'Quality Inspection Lots'

    def __str__(self):
        return f'{self.lot_number} - {self.bmr.batch_number}'

    def save(self, *args, **kwargs):
        if not self.lot_number:
            self.lot_number = self.generate_lot_number()
        super().save(*args, **kwargs)

    @classmethod
    def generate_lot_number(cls):
        from django.db.models import Max
        from django.utils import timezone

        year = timezone.now().year
        prefix = f'QI{year}'
        max_lot = cls.objects.filter(lot_number__startswith=prefix).aggregate(Max('lot_number'))['lot_number__max']
        if max_lot:
            try:
                next_num = int(max_lot.replace(prefix, '')) + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1

        while True:
            candidate = f'{prefix}{next_num:05d}'
            if not cls.objects.filter(lot_number=candidate).exists():
                return candidate
            next_num += 1

    @property
    def open_defect_count(self):
        return self.defects.exclude(status='closed').count()


class QualityInspectionCharacteristic(models.Model):
    """Inspection characteristic/specification row for a quality lot."""

    lot = models.ForeignKey(QualityInspectionLot, on_delete=models.CASCADE, related_name='characteristics')
    template_section = models.ForeignKey(
        'bmr.BMRTemplateSection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quality_characteristics',
    )
    template_field = models.ForeignKey(
        'bmr.BMRTemplateField',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quality_characteristics',
    )
    name = models.CharField(max_length=120)
    test_method = models.CharField(max_length=200, blank=True)
    specification = models.CharField(max_length=255)
    lower_limit = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    upper_limit = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    unit = models.CharField(max_length=30, blank=True)
    required = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['lot', 'order', 'name']
        verbose_name = 'Quality Inspection Characteristic'
        verbose_name_plural = 'Quality Inspection Characteristics'

    def __str__(self):
        return f'{self.lot.lot_number} - {self.name}'


class QualityResult(models.Model):
    """Recorded inspection result for one characteristic."""

    characteristic = models.ForeignKey(QualityInspectionCharacteristic, on_delete=models.CASCADE, related_name='results')
    value_text = models.CharField(max_length=255, blank=True)
    numeric_value = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    passed = models.BooleanField(null=True, blank=True)
    comments = models.TextField(blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']
        verbose_name = 'Quality Result'
        verbose_name_plural = 'Quality Results'

    def __str__(self):
        return f'{self.characteristic} - {self.get_result_display()}'

    def get_result_display(self):
        if self.passed is True:
            return 'Pass'
        if self.passed is False:
            return 'Fail'
        return 'Recorded'


class QualityDefect(models.Model):
    """Defect/notification-style record for failed or held inspections."""

    DEFECT_TYPE_CHOICES = [
        ('out_of_specification', 'Out of Specification'),
        ('deviation', 'Deviation'),
        ('documentation', 'Documentation Issue'),
        ('contamination', 'Contamination'),
        ('other', 'Other'),
    ]
    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('major', 'Major'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('corrective_action', 'Corrective Action'),
        ('closed', 'Closed'),
    ]

    lot = models.ForeignKey(QualityInspectionLot, on_delete=models.CASCADE, related_name='defects')
    defect_type = models.CharField(max_length=30, choices=DEFECT_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='major')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='open')
    description = models.TextField()
    corrective_action = models.TextField(blank=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_defects_reported')
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_defects_closed')
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Quality Defect'
        verbose_name_plural = 'Quality Defects'

    def __str__(self):
        return f'{self.lot.lot_number} - {self.get_defect_type_display()}'


class QMSAction(models.Model):
    """Full-scale QMS work item routed to QA or QC without changing BMR flow."""

    CATEGORY_CHOICES = [
        ('deviation', 'Deviation / OOS Investigation'),
        ('capa', 'CAPA'),
        ('change_control', 'Change Control'),
        ('complaint', 'Complaint / Recall'),
        ('supplier_quality', 'Supplier Quality'),
        ('stability', 'Stability Study'),
        ('coa', 'Certificate of Analysis'),
        ('audit', 'Audit Finding'),
        ('document_control', 'SOP / Document Control'),
        ('risk', 'Quality Risk Management'),
    ]
    OWNER_ROLE_CHOICES = [
        ('qa', 'Quality Assurance'),
        ('qc', 'Quality Control'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigation', 'Investigation'),
        ('action_required', 'Action Required'),
        ('pending_approval', 'Pending Approval'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    qms_number = models.CharField(max_length=30, unique=True, blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    owner_role = models.CharField(max_length=10, choices=OWNER_ROLE_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', db_index=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')

    title = models.CharField(max_length=180)
    description = models.TextField()
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    preventive_action = models.TextField(blank=True)
    effectiveness_check = models.TextField(blank=True)

    bmr = models.ForeignKey(BMR, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_actions')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_actions')
    quality_lot = models.ForeignKey(QualityInspectionLot, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_actions')
    defect = models.ForeignKey(QualityDefect, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_actions')

    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_actions_created')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_actions_assigned')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_actions_approved')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'QMS Action'
        verbose_name_plural = 'QMS Actions'

    def __str__(self):
        return f'{self.qms_number} - {self.get_category_display()}'

    def save(self, *args, **kwargs):
        if not self.qms_number:
            self.qms_number = self.generate_qms_number()
        super().save(*args, **kwargs)

    @classmethod
    def generate_qms_number(cls):
        from django.db.models import Max
        from django.utils import timezone

        year = timezone.now().year
        prefix = f'QMS{year}'
        max_number = cls.objects.filter(qms_number__startswith=prefix).aggregate(Max('qms_number'))['qms_number__max']
        if max_number:
            try:
                next_num = int(max_number.replace(prefix, '')) + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1

        while True:
            candidate = f'{prefix}{next_num:05d}'
            if not cls.objects.filter(qms_number=candidate).exists():
                return candidate
            next_num += 1

    @property
    def is_open(self):
        return self.status not in ('closed', 'cancelled')


class QMSDocument(models.Model):
    """Controlled QMS document with version, review, approval, and signature trail."""

    DOCUMENT_TYPE_CHOICES = [
        ('sop', 'SOP'),
        ('bmr', 'BMR'),
        ('batch_packing_record', 'Batch Packing Record'),
        ('master_formula_record', 'Master Formula Record'),
        ('policy', 'Policy'),
        ('validation_report', 'Validation Report'),
        ('other', 'Other Controlled Document'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('effective', 'Effective'),
        ('obsolete', 'Obsolete'),
        ('archived', 'Archived'),
    ]

    document_number = models.CharField(max_length=30, unique=True, blank=True)
    document_type = models.CharField(max_length=40, choices=DOCUMENT_TYPE_CHOICES, db_index=True)
    title = models.CharField(max_length=200)
    version = models.CharField(max_length=20, default='1.0')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    controlled_file = models.FileField(upload_to='qms_documents/', null=True, blank=True)

    effective_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    revision_date = models.DateField(null=True, blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    revision_reason = models.TextField(blank=True)
    revision_history = models.JSONField(default=list, blank=True)
    document_summary = models.TextField(blank=True)
    change_control_reference = models.CharField(max_length=180, blank=True)
    supersedes_version = models.CharField(max_length=20, blank=True)
    review_comments = models.TextField(blank=True)
    approval_notes = models.TextField(blank=True)
    retention_period_years = models.PositiveIntegerField(default=7)

    related_qms_action = models.ForeignKey(QMSAction, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_documents_owned')
    prepared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_documents_prepared')
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_documents_reviewed')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_documents_approved')
    electronic_signature = models.CharField(max_length=180, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'QMS Document'
        verbose_name_plural = 'QMS Documents'

    def __str__(self):
        return f'{self.document_number} - {self.title}'

    def save(self, *args, **kwargs):
        if not self.document_number:
            self.document_number = self.generate_document_number()
        if self.pk:
            original = QMSDocument.objects.filter(pk=self.pk).first()
            if original and (original.version != self.version or original.status != self.status):
                self.revision_history = list(self.revision_history or [])
                self.revision_history.append({
                    'from_version': original.version,
                    'to_version': self.version,
                    'from_status': original.status,
                    'to_status': self.status,
                })
        super().save(*args, **kwargs)

    @classmethod
    def generate_document_number(cls):
        from django.db.models import Max
        from django.utils import timezone

        year = timezone.now().year
        prefix = f'DOC{year}'
        max_number = cls.objects.filter(document_number__startswith=prefix).aggregate(Max('document_number'))['document_number__max']
        if max_number:
            try:
                next_num = int(max_number.replace(prefix, '')) + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        while True:
            candidate = f'{prefix}{next_num:05d}'
            if not cls.objects.filter(document_number=candidate).exists():
                return candidate
            next_num += 1

    @property
    def ready_for_review(self):
        return bool(self.title.strip() and self.document_type and self.version.strip() and self.owner_id and self.controlled_file)

    @property
    def ready_for_approval(self):
        return bool(self.ready_for_review and self.reviewed_by_id and self.review_comments.strip())

    @property
    def ready_for_effective(self):
        return bool(self.ready_for_approval and self.approved_by_id and self.effective_date)


class QMSDeviation(models.Model):
    """Deviation lifecycle: SOP reference, impact assessment, QA decision, CAPA, closure."""

    SEVERITY_CHOICES = [
        ('minor', 'Minor'),
        ('major', 'Major'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('impact_assessment', 'Impact Assessment'),
        ('root_cause', 'Root Cause'),
        ('capa_required', 'CAPA Required'),
        ('pending_qa_decision', 'Pending QA Decision'),
        ('closed', 'Closed'),
    ]
    QA_DECISION_CHOICES = [
        ('', 'Pending'),
        ('no_impact', 'No Impact'),
        ('accept_with_justification', 'Accept With Justification'),
        ('rework', 'Rework'),
        ('reject', 'Reject'),
        ('capa_required', 'CAPA Required'),
    ]

    deviation_number = models.CharField(max_length=30, unique=True, blank=True)
    qms_action = models.OneToOneField(QMSAction, on_delete=models.SET_NULL, null=True, blank=True, related_name='deviation_record')
    sop_document = models.ForeignKey(QMSDocument, on_delete=models.SET_NULL, null=True, blank=True, related_name='deviations')
    bmr = models.ForeignKey(BMR, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_deviations')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_deviations')
    quality_lot = models.ForeignKey(QualityInspectionLot, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_deviations')
    defect = models.ForeignKey(QualityDefect, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_deviations')

    title = models.CharField(max_length=180)
    description = models.TextField()
    deviation_type = models.CharField(max_length=80, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='major')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='open', db_index=True)
    detection_date = models.DateField(null=True, blank=True)
    immediate_action = models.TextField(blank=True)
    impact_assessment = models.TextField(blank=True)
    root_cause = models.TextField(blank=True)
    qa_decision = models.CharField(max_length=40, choices=QA_DECISION_CHOICES, blank=True)
    capa_action = models.ForeignKey(QMSAction, on_delete=models.SET_NULL, null=True, blank=True, related_name='deviations_as_capa')
    closure_summary = models.TextField(blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_deviations_created')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_deviations_assigned')
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_deviations_closed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'QMS Deviation'
        verbose_name_plural = 'QMS Deviations'

    def __str__(self):
        return f'{self.deviation_number} - {self.title}'

    def save(self, *args, **kwargs):
        if not self.deviation_number:
            self.deviation_number = self.generate_deviation_number()
        super().save(*args, **kwargs)

    @classmethod
    def generate_deviation_number(cls):
        from django.db.models import Max
        from django.utils import timezone

        year = timezone.now().year
        prefix = f'DEV{year}'
        max_number = cls.objects.filter(deviation_number__startswith=prefix).aggregate(Max('deviation_number'))['deviation_number__max']
        if max_number:
            try:
                next_num = int(max_number.replace(prefix, '')) + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        while True:
            candidate = f'{prefix}{next_num:05d}'
            if not cls.objects.filter(deviation_number=candidate).exists():
                return candidate
            next_num += 1


class QMSRiskAssessment(models.Model):
    """Quality risk record supporting FMEA, HACCP, and risk-matrix methods."""

    METHOD_CHOICES = [
        ('fmea', 'FMEA'),
        ('haccp', 'HACCP'),
        ('risk_matrix', 'Risk Matrix'),
    ]
    LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('mitigation', 'Mitigation'),
        ('closed', 'Closed'),
    ]

    risk_number = models.CharField(max_length=30, unique=True, blank=True)
    qms_action = models.ForeignKey(QMSAction, on_delete=models.SET_NULL, null=True, blank=True, related_name='risk_assessments')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='fmea', db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    risk_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='medium')

    title = models.CharField(max_length=180)
    process_area = models.CharField(max_length=120, blank=True)
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_risks')
    bmr = models.ForeignKey(BMR, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_risks')
    hazard = models.TextField(blank=True)
    failure_mode = models.TextField(blank=True)
    cause = models.TextField(blank=True)
    effect = models.TextField(blank=True)
    current_controls = models.TextField(blank=True)
    mitigation_plan = models.TextField(blank=True)

    severity = models.PositiveSmallIntegerField(default=1)
    occurrence = models.PositiveSmallIntegerField(default=1)
    detectability = models.PositiveSmallIntegerField(default=1)
    rpn = models.PositiveIntegerField(default=1)
    residual_severity = models.PositiveSmallIntegerField(default=1)
    residual_occurrence = models.PositiveSmallIntegerField(default=1)
    residual_detectability = models.PositiveSmallIntegerField(default=1)
    residual_rpn = models.PositiveIntegerField(default=1)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_risks_owned')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_risks_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'QMS Risk Assessment'
        verbose_name_plural = 'QMS Risk Assessments'

    def __str__(self):
        return f'{self.risk_number} - {self.get_method_display()}'

    def save(self, *args, **kwargs):
        if not self.risk_number:
            self.risk_number = self.generate_risk_number()
        self.rpn = self._score(self.severity, self.occurrence, self.detectability)
        self.residual_rpn = self._score(self.residual_severity, self.residual_occurrence, self.residual_detectability)
        self.risk_level = self._level_for_score(self.rpn)
        super().save(*args, **kwargs)

    @staticmethod
    def _score(severity, occurrence, detectability):
        return max(1, int(severity or 1)) * max(1, int(occurrence or 1)) * max(1, int(detectability or 1))

    @staticmethod
    def _level_for_score(score):
        if score >= 200:
            return 'critical'
        if score >= 80:
            return 'high'
        if score >= 30:
            return 'medium'
        return 'low'

    @classmethod
    def generate_risk_number(cls):
        from django.db.models import Max
        from django.utils import timezone

        year = timezone.now().year
        prefix = f'RISK{year}'
        max_number = cls.objects.filter(risk_number__startswith=prefix).aggregate(Max('risk_number'))['risk_number__max']
        if max_number:
            try:
                next_num = int(max_number.replace(prefix, '')) + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        while True:
            candidate = f'{prefix}{next_num:05d}'
            if not cls.objects.filter(risk_number=candidate).exists():
                return candidate
            next_num += 1


class QMSAudit(models.Model):
    """Audit management for internal, supplier, regulatory, FDA, ISO, and stores audits."""

    AUDIT_TYPE_CHOICES = [
        ('internal', 'Internal Audit'),
        ('supplier', 'Supplier Audit'),
        ('regulatory', 'Regulatory Audit'),
        ('fda', 'FDA Audit'),
        ('iso', 'ISO Audit'),
        ('stores', 'Stores Audit'),
    ]
    FINDING_TYPE_CHOICES = [
        ('observation', 'Observation'),
        ('minor_nc', 'Minor Non-Conformance'),
        ('major_nc', 'Major Non-Conformance'),
        ('critical_nc', 'Critical Non-Conformance'),
        ('opportunity', 'Opportunity for Improvement'),
    ]
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('finding_open', 'Finding Open'),
        ('corrective_action', 'Corrective Action'),
        ('pending_verification', 'Pending Verification'),
        ('closed', 'Closed'),
    ]
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    audit_number = models.CharField(max_length=30, unique=True, blank=True)
    audit_type = models.CharField(max_length=20, choices=AUDIT_TYPE_CHOICES, db_index=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='planned', db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    finding_type = models.CharField(max_length=30, choices=FINDING_TYPE_CHOICES, default='observation')

    title = models.CharField(max_length=180)
    scope = models.TextField(blank=True)
    auditee = models.CharField(max_length=160, blank=True)
    department = models.CharField(max_length=120, blank=True)
    standard_reference = models.CharField(max_length=180, blank=True)
    observation = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    verification_notes = models.TextField(blank=True)
    evidence_file = models.FileField(upload_to='qms_audits/', null=True, blank=True)

    qms_action = models.ForeignKey(QMSAction, on_delete=models.SET_NULL, null=True, blank=True, related_name='audits')
    risk_assessment = models.ForeignKey(QMSRiskAssessment, on_delete=models.SET_NULL, null=True, blank=True, related_name='audits')
    due_date = models.DateField(null=True, blank=True)
    planned_date = models.DateField(null=True, blank=True)
    conducted_date = models.DateField(null=True, blank=True)
    responsible_person = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_audits_responsible')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_audits_created')
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_audits_closed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'QMS Audit'
        verbose_name_plural = 'QMS Audits'

    def __str__(self):
        return f'{self.audit_number} - {self.get_audit_type_display()}'

    def save(self, *args, **kwargs):
        if not self.audit_number:
            self.audit_number = self.generate_audit_number()
        super().save(*args, **kwargs)

    @classmethod
    def generate_audit_number(cls):
        from django.db.models import Max
        from django.utils import timezone

        year = timezone.now().year
        prefix = f'AUD{year}'
        max_number = cls.objects.filter(audit_number__startswith=prefix).aggregate(Max('audit_number'))['audit_number__max']
        if max_number:
            try:
                next_num = int(max_number.replace(prefix, '')) + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        while True:
            candidate = f'{prefix}{next_num:05d}'
            if not cls.objects.filter(audit_number=candidate).exists():
                return candidate
            next_num += 1


class QMSCAPA(models.Model):
    """Dedicated CAPA lifecycle linked to the generic QMS action record."""

    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('investigation', 'Investigation'),
        ('root_cause_analysis', 'Root Cause Analysis'),
        ('action_plan', 'Action Plan'),
        ('implementation', 'Implementation'),
        ('effectiveness_review', 'Effectiveness Review'),
        ('overdue', 'Overdue'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]
    PRIORITY_CHOICES = QMSAction.PRIORITY_CHOICES
    SOURCE_CHOICES = [
        ('deviation', 'Deviation / OOS'),
        ('audit', 'Audit Finding'),
        ('complaint', 'Complaint / Recall'),
        ('trend', 'Trend / KPI'),
        ('other', 'Other'),
    ]
    EFFECTIVENESS_CHOICES = [
        ('', 'Not assessed'),
        ('effective', 'Effective'),
        ('partially_effective', 'Partially Effective'),
        ('not_effective', 'Not Effective'),
    ]

    capa_number = models.CharField(max_length=30, unique=True, blank=True)
    qms_action = models.OneToOneField(QMSAction, on_delete=models.CASCADE, related_name='capa_record')
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='other')
    source_reference = models.CharField(max_length=180, blank=True)
    source_deviation = models.ForeignKey(QMSDeviation, on_delete=models.SET_NULL, null=True, blank=True, related_name='capa_records')
    source_audit = models.ForeignKey(QMSAudit, on_delete=models.SET_NULL, null=True, blank=True, related_name='capa_records')

    problem_statement = models.TextField(blank=True)
    containment_action = models.TextField(blank=True)
    root_cause_method = models.CharField(max_length=80, blank=True, default='5 Whys')
    root_cause_analysis = models.TextField(blank=True)
    corrective_action_plan = models.TextField(blank=True)
    preventive_action_plan = models.TextField(blank=True)
    action_owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='capa_actions_owned')
    target_completion_date = models.DateField(null=True, blank=True)

    effectiveness_method = models.CharField(max_length=180, blank=True)
    effectiveness_criteria = models.TextField(blank=True)
    effectiveness_result = models.CharField(max_length=30, choices=EFFECTIVENESS_CHOICES, blank=True)
    effectiveness_evidence = models.TextField(blank=True)
    effectiveness_review_date = models.DateField(null=True, blank=True)
    effectiveness_verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='capas_effectiveness_verified')

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='initiated', db_index=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    qa_reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='capas_reviewed')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='capas_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    closure_justification = models.TextField(blank=True)
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='capas_closed')
    closed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='capas_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'CAPA Record'
        verbose_name_plural = 'CAPA Records'

    def __str__(self):
        return f'{self.capa_number} - {self.qms_action.title}'

    def save(self, *args, **kwargs):
        if not self.capa_number:
            self.capa_number = self.generate_capa_number()
        super().save(*args, **kwargs)

    @classmethod
    def generate_capa_number(cls):
        from django.db.models import Max
        from django.utils import timezone

        prefix = f'CAPA{timezone.now().year}'
        maximum = cls.objects.filter(capa_number__startswith=prefix).aggregate(Max('capa_number'))['capa_number__max']
        try:
            next_number = int(maximum.replace(prefix, '')) + 1 if maximum else 1
        except (AttributeError, ValueError):
            next_number = 1
        while True:
            candidate = f'{prefix}{next_number:05d}'
            if not cls.objects.filter(capa_number=candidate).exists():
                return candidate
            next_number += 1

    @property
    def is_ready_for_closure(self):
        return bool(
            self.root_cause_analysis.strip()
            and self.corrective_action_plan.strip()
            and self.preventive_action_plan.strip()
            and self.effectiveness_result == 'effective'
            and self.effectiveness_evidence.strip()
            and self.effectiveness_verified_by_id
            and self.effectiveness_review_date
            and self.approved_by_id
        )

    @property
    def has_source_link(self):
        return bool(self.source_deviation_id or self.source_audit_id or self.source_reference.strip())


class QMSApprovalRoute(models.Model):
    """Configurable approval route for QMS records."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    route_number = models.CharField(max_length=30, unique=True, blank=True)
    title = models.CharField(max_length=180)
    target_model = models.CharField(max_length=80)
    target_object_id = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    current_step = models.PositiveSmallIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_approval_routes_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'QMS Approval Route'
        verbose_name_plural = 'QMS Approval Routes'

    def __str__(self):
        return f'{self.route_number} - {self.title}'

    def save(self, *args, **kwargs):
        if not self.route_number:
            self.route_number = self.generate_number('APR')
        super().save(*args, **kwargs)

    @classmethod
    def generate_number(cls, prefix_base):
        from django.db.models import Max
        from django.utils import timezone

        prefix = f'{prefix_base}{timezone.now().year}'
        max_number = cls.objects.filter(route_number__startswith=prefix).aggregate(Max('route_number'))['route_number__max']
        next_num = 1
        if max_number:
            try:
                next_num = int(max_number.replace(prefix, '')) + 1
            except ValueError:
                next_num = 1
        while True:
            candidate = f'{prefix}{next_num:05d}'
            if not cls.objects.filter(route_number=candidate).exists():
                return candidate
            next_num += 1


class QMSApprovalStep(models.Model):
    DECISION_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned for Revision'),
    ]

    route = models.ForeignKey(QMSApprovalRoute, on_delete=models.CASCADE, related_name='steps')
    sequence = models.PositiveSmallIntegerField(default=1)
    role = models.CharField(max_length=80)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_approval_steps_assigned')
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default='pending')
    comments = models.TextField(blank=True)
    signed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_approval_steps_signed')
    signed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['route', 'sequence']
        unique_together = ['route', 'sequence']

    def __str__(self):
        return f'{self.route.route_number} step {self.sequence} - {self.role}'


class QMSElectronicSignature(models.Model):
    """Electronic signature event for a QMS object."""

    signature_number = models.CharField(max_length=30, unique=True, blank=True)
    target_model = models.CharField(max_length=80)
    target_object_id = models.PositiveIntegerField(null=True, blank=True)
    meaning = models.CharField(max_length=180)
    signer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_electronic_signatures')
    signature_hash = models.CharField(max_length=128, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    reauthenticated = models.BooleanField(default=False)
    reauthenticated_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-signed_at']
        verbose_name = 'QMS Electronic Signature'
        verbose_name_plural = 'QMS Electronic Signatures'

    def __str__(self):
        return f'{self.signature_number} - {self.meaning}'

    def save(self, *args, **kwargs):
        if not self.signature_number:
            self.signature_number = self._generate_number()
        if not self.signature_hash:
            import hashlib
            raw = f'{self.target_model}:{self.target_object_id}:{self.meaning}:{self.signer_id}'
            self.signature_hash = hashlib.sha256(raw.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)

    @classmethod
    def _generate_number(cls):
        from django.db.models import Max
        from django.utils import timezone

        prefix = f'SIG{timezone.now().year}'
        max_number = cls.objects.filter(signature_number__startswith=prefix).aggregate(Max('signature_number'))['signature_number__max']
        next_num = 1
        if max_number:
            try:
                next_num = int(max_number.replace(prefix, '')) + 1
            except ValueError:
                next_num = 1
        while True:
            candidate = f'{prefix}{next_num:05d}'
            if not cls.objects.filter(signature_number=candidate).exists():
                return candidate
            next_num += 1


class QMSFieldAuditTrail(models.Model):
    model_name = models.CharField(max_length=80, db_index=True)
    object_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    field_name = models.CharField(max_length=120)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    reason = models.TextField(blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_field_audit_changes')
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'QMS Field Audit Trail'
        verbose_name_plural = 'QMS Field Audit Trails'

    def __str__(self):
        return f'{self.model_name}#{self.object_id} {self.field_name}'


class QMSReportExport(models.Model):
    REPORT_CHOICES = [
        ('document', 'Document Register'),
        ('deviation', 'Deviation Report'),
        ('capa', 'CAPA Report'),
        ('audit', 'Audit Report'),
        ('risk', 'Risk Report'),
        ('coa', 'COA Report'),
        ('stability', 'Stability Report'),
        ('supplier', 'Supplier Quality Report'),
    ]
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('generated', 'Generated'),
        ('failed', 'Failed'),
    ]

    report_type = models.CharField(max_length=30, choices=REPORT_CHOICES)
    export_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    filters = models.JSONField(default=dict, blank=True)
    export_file = models.FileField(upload_to='qms_reports/', null=True, blank=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_report_exports')
    created_at = models.DateTimeField(auto_now_add=True)
    generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'QMS Report Export'
        verbose_name_plural = 'QMS Report Exports'

    def __str__(self):
        return f'{self.get_report_type_display()} - {self.get_export_format_display()}'


class QMSSamplingPlan(models.Model):
    name = models.CharField(max_length=160)
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_sampling_plans')
    inspection_type = models.CharField(max_length=80, blank=True)
    aql_level = models.CharField(max_length=40, blank=True)
    sample_size = models.PositiveIntegerField(default=0)
    acceptance_number = models.PositiveIntegerField(default=0)
    rejection_number = models.PositiveIntegerField(default=0)
    procedure_reference = models.CharField(max_length=160, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class QMSLabSpecification(models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_lab_specifications')
    test_name = models.CharField(max_length=160)
    method_reference = models.CharField(max_length=160, blank=True)
    specification = models.CharField(max_length=255)
    lower_limit = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    upper_limit = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    unit = models.CharField(max_length=30, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['product', 'test_name']

    def __str__(self):
        return f'{self.test_name} - {self.specification}'


class QMSStabilitySchedule(models.Model):
    CONDITION_CHOICES = [
        ('long_term', 'Long Term'),
        ('accelerated', 'Accelerated'),
        ('intermediate', 'Intermediate'),
    ]
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('pulled', 'Pulled'),
        ('tested', 'Tested'),
        ('reviewed', 'Reviewed'),
        ('qa_review', 'QA Review'),
        ('failed', 'Failed / Investigation'),
        ('closed', 'Closed'),
    ]

    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_stability_schedules')
    bmr = models.ForeignKey(BMR, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_stability_schedules')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    time_point = models.CharField(max_length=40)
    chamber = models.CharField(max_length=80, blank=True)
    pull_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    result_summary = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_stability_reviews')
    study_number = models.CharField(max_length=30, unique=True, blank=True)
    protocol_reference = models.CharField(max_length=160, blank=True)
    storage_condition = models.CharField(max_length=160, blank=True)
    specification_reference = models.CharField(max_length=160, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_stability_owned')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_stability_created')
    qa_review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['pull_date']

    def __str__(self):
        return f'{self.study_number or self.pk} - {self.product} {self.get_condition_display()} {self.time_point}'

    def save(self, *args, **kwargs):
        if not self.study_number:
            prefix = f'STAB{timezone.now().year}'
            maximum = type(self).objects.filter(study_number__startswith=prefix).aggregate(models.Max('study_number'))['study_number__max']
            try:
                number = int(maximum.replace(prefix, '')) + 1 if maximum else 1
            except (AttributeError, ValueError):
                number = 1
            self.study_number = f'{prefix}{number:05d}'
        super().save(*args, **kwargs)


class QMSStabilityResult(models.Model):
    schedule = models.ForeignKey(QMSStabilitySchedule, on_delete=models.CASCADE, related_name='results')
    test_name = models.CharField(max_length=160)
    result_value = models.CharField(max_length=120, blank=True)
    specification = models.CharField(max_length=255, blank=True)
    passed = models.BooleanField(null=True, blank=True)
    test_date = models.DateField(null=True, blank=True)
    analyst = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_stability_results')
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['test_date', 'test_name']

    def __str__(self):
        return f'{self.schedule} - {self.test_name}'


class QMSSupplierQualification(models.Model):
    STATUS_CHOICES = [
        ('candidate', 'Candidate'),
        ('approved', 'Approved'),
        ('conditional', 'Conditional'),
        ('disqualified', 'Disqualified'),
        ('requalification_due', 'Requalification Due'),
    ]
    RISK_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    supplier_name = models.CharField(max_length=180)
    material_name = models.CharField(max_length=180, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='candidate')
    risk_level = models.CharField(max_length=20, choices=RISK_CHOICES, default='medium')
    qualification_score = models.PositiveSmallIntegerField(default=0)
    last_audit_date = models.DateField(null=True, blank=True)
    next_audit_date = models.DateField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    supplier_code = models.CharField(max_length=80, blank=True)
    contact_details = models.TextField(blank=True)
    material_specification = models.CharField(max_length=180, blank=True)
    quality_agreement_reference = models.CharField(max_length=160, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_supplier_quality_owned')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_suppliers_approved')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['supplier_name']

    def __str__(self):
        return self.supplier_name


class QMSMaterialQC(models.Model):
    STATUS_CHOICES = [
        ('received', 'Received'), ('sampling', 'Sampling'), ('testing', 'Testing'),
        ('qa_review', 'QA Review'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('on_hold', 'On Hold'),
    ]
    material_lot_number = models.CharField(max_length=100, unique=True)
    material_name = models.CharField(max_length=180)
    material_code = models.CharField(max_length=80, blank=True)
    supplier = models.ForeignKey(QMSSupplierQualification, on_delete=models.SET_NULL, null=True, blank=True, related_name='material_qc_records')
    bmr = models.ForeignKey(BMR, on_delete=models.SET_NULL, null=True, blank=True, related_name='material_qc_records')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received', db_index=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    unit = models.CharField(max_length=30, blank=True)
    received_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    supplier_certificate_file = models.FileField(upload_to='qms_material_qc/', null=True, blank=True)
    sampling_plan = models.ForeignKey(QMSSamplingPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='material_qc_records')
    specification = models.ForeignKey(QMSLabSpecification, on_delete=models.SET_NULL, null=True, blank=True, related_name='material_qc_records')
    result_summary = models.TextField(blank=True)
    qa_decision_notes = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_material_qc_owned')
    qa_reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_material_qc_reviewed')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_material_qc_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.material_lot_number} - {self.material_name}'


class QMSCOA(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'), ('qc_prepared', 'Prepared by QC'), ('qa_review', 'QA Review'),
        ('approved', 'Approved / Released'), ('rejected', 'Rejected'), ('void', 'Void'),
    ]
    coa_number = models.CharField(max_length=30, unique=True, blank=True)
    bmr = models.ForeignKey(BMR, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_coas')
    quality_lot = models.ForeignKey(QualityInspectionLot, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_coas')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_coas')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    market = models.CharField(max_length=120, blank=True)
    specification_reference = models.CharField(max_length=160, blank=True)
    result_summary = models.TextField(blank=True)
    certificate_file = models.FileField(upload_to='qms_coa/', null=True, blank=True)
    prepared_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_coas_prepared')
    qa_reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_coas_reviewed')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_coas_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.coa_number} - {self.product or self.bmr}'

    def save(self, *args, **kwargs):
        if not self.coa_number:
            prefix = f'COA{timezone.now().year}'
            maximum = type(self).objects.filter(coa_number__startswith=prefix).aggregate(models.Max('coa_number'))['coa_number__max']
            try:
                number = int(maximum.replace(prefix, '')) + 1 if maximum else 1
            except (AttributeError, ValueError):
                number = 1
            self.coa_number = f'{prefix}{number:05d}'
        super().save(*args, **kwargs)


class QMSCalibrationRecord(models.Model):
    STATUS_CHOICES = [
        ('in_service', 'In Service'),
        ('due', 'Due'),
        ('overdue', 'Overdue'),
        ('out_of_service', 'Out of Service'),
    ]

    equipment_id = models.CharField(max_length=80)
    equipment_name = models.CharField(max_length=160)
    department = models.CharField(max_length=120, blank=True)
    manufacturer = models.CharField(max_length=160, blank=True)
    model_number = models.CharField(max_length=120, blank=True)
    serial_number = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=160, blank=True)
    calibration_interval_days = models.PositiveIntegerField(default=365)
    method_reference = models.CharField(max_length=180, blank=True)
    acceptance_criteria = models.TextField(blank=True)
    last_calibrated = models.DateField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_service')
    certificate_file = models.FileField(upload_to='qms_calibration/', null=True, blank=True)
    notes = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_calibration_owned')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_calibration_created')
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_calibration_verified')
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_due_date', 'equipment_id']

    def __str__(self):
        return f'{self.equipment_id} - {self.equipment_name}'

    @property
    def calculated_status(self):
        if self.status == 'out_of_service':
            return 'out_of_service'
        if not self.next_due_date:
            return self.status
        today = timezone.now().date()
        if self.next_due_date < today:
            return 'overdue'
        if self.next_due_date <= today + timedelta(days=30):
            return 'due'
        return 'in_service'

    @property
    def calculated_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.calculated_status, self.get_status_display())

    @property
    def ready_for_use(self):
        return bool(self.last_calibrated and self.next_due_date and self.calculated_status == 'in_service' and self.certificate_file)


class QMSCalibrationEvent(models.Model):
    RESULT_CHOICES = [('pass', 'Pass'), ('fail', 'Fail'), ('conditional', 'Conditional')]

    calibration = models.ForeignKey(QMSCalibrationRecord, on_delete=models.CASCADE, related_name='events')
    calibration_date = models.DateField()
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='pass')
    certificate_number = models.CharField(max_length=120, blank=True)
    certificate_file = models.FileField(upload_to='qms_calibration/events/', null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_calibration_events_performed')
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_calibration_events_verified')
    verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-calibration_date', '-created_at']

    def __str__(self):
        return f'{self.calibration.equipment_id} - {self.calibration_date} - {self.get_result_display()}'


class QMSTrainingRecord(models.Model):
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('awaiting_verification', 'Awaiting Verification'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('failed', 'Failed'),
        ('waived', 'Waived'),
    ]

    training_number = models.CharField(max_length=30, unique=True, blank=True)
    document = models.ForeignKey(QMSDocument, on_delete=models.SET_NULL, null=True, blank=True, related_name='training_records')
    trainee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_training_records')
    training_type = models.CharField(max_length=80, default='SOP Revision')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='assigned')
    assigned_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_training_delivered')
    evidence_file = models.FileField(upload_to='qms_training/', null=True, blank=True)
    objective = models.TextField(blank=True)
    content_summary = models.TextField(blank=True)
    delivery_method = models.CharField(max_length=80, default='Instructor-led')
    completion_notes = models.TextField(blank=True)
    assessment_result = models.CharField(max_length=120, blank=True)
    effectiveness_due_date = models.DateField(null=True, blank=True)
    effectiveness_result = models.TextField(blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_training_verified')
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f'{self.training_number} - {self.trainee} - {self.document}'

    def save(self, *args, **kwargs):
        if not self.training_number:
            from django.db.models import Max
            from django.utils import timezone
            prefix = f'TRN{timezone.now().year}'
            maximum = type(self).objects.filter(training_number__startswith=prefix).aggregate(Max('training_number'))['training_number__max']
            try:
                next_number = int(maximum.replace(prefix, '')) + 1 if maximum else 1
            except (AttributeError, ValueError):
                next_number = 1
            self.training_number = f'{prefix}{next_number:05d}'
        super().save(*args, **kwargs)

    @property
    def ready_for_completion(self):
        return bool(self.trainee_id and self.document_id and self.completion_notes.strip() and self.assessment_result.strip() and self.completed_date)

    @property
    def ready_for_verification(self):
        return bool(self.ready_for_completion and self.effectiveness_result.strip() and self.verified_by_id)


class QMSChangeImpactAssessment(models.Model):
    change_action = models.ForeignKey(QMSAction, on_delete=models.SET_NULL, null=True, blank=True, related_name='impact_assessments')
    bmr_impact = models.BooleanField(default=False)
    validation_impact = models.BooleanField(default=False)
    regulatory_impact = models.BooleanField(default=False)
    training_impact = models.BooleanField(default=False)
    stability_impact = models.BooleanField(default=False)
    inventory_impact = models.BooleanField(default=False)
    impact_summary = models.TextField(blank=True)
    qa_decision = models.CharField(max_length=120, blank=True)
    assessed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_change_impacts_assessed')
    assessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assessed_at']

    def __str__(self):
        return f'Impact for {self.change_action}'


class QMSChangeControl(models.Model):
    """Full change-control lifecycle linked to a QMS action."""

    CHANGE_TYPE_CHOICES = [
        ('process', 'Process'),
        ('equipment', 'Equipment'),
        ('facility', 'Facility'),
        ('material', 'Material'),
        ('document', 'Document / SOP'),
        ('system', 'Computerized System'),
    ]
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('impact_assessment', 'Impact Assessment'),
        ('qa_review', 'QA Review'),
        ('approved', 'Approved'),
        ('implementation', 'Implementation'),
        ('effectiveness_review', 'Effectiveness Review'),
        ('overdue', 'Overdue'),
        ('closed', 'Closed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    RISK_CHOICES = QMSAction.PRIORITY_CHOICES
    EFFECTIVENESS_CHOICES = [
        ('', 'Not assessed'),
        ('effective', 'Effective'),
        ('partially_effective', 'Partially Effective'),
        ('not_effective', 'Not Effective'),
    ]

    change_number = models.CharField(max_length=30, unique=True, blank=True)
    qms_action = models.OneToOneField(QMSAction, on_delete=models.CASCADE, related_name='change_control_record')
    change_type = models.CharField(max_length=30, choices=CHANGE_TYPE_CHOICES, default='process')
    risk_level = models.CharField(max_length=20, choices=RISK_CHOICES, default='medium')
    source_reference = models.CharField(max_length=180, blank=True)
    justification = models.TextField(blank=True)
    current_state = models.TextField(blank=True)
    proposed_state = models.TextField(blank=True)

    quality_impact = models.BooleanField(default=False)
    gmp_impact = models.BooleanField(default=False)
    validation_impact = models.BooleanField(default=False)
    regulatory_impact = models.BooleanField(default=False)
    documentation_impact = models.BooleanField(default=False)
    training_impact = models.BooleanField(default=False)
    stability_impact = models.BooleanField(default=False)
    inventory_impact = models.BooleanField(default=False)
    impact_summary = models.TextField(blank=True)
    qa_impact_decision = models.CharField(max_length=180, blank=True)

    implementation_plan = models.TextField(blank=True)
    implementation_notes = models.TextField(blank=True)
    affected_documents = models.TextField(blank=True)
    training_plan = models.TextField(blank=True)
    validation_plan = models.TextField(blank=True)
    implementation_owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='change_controls_implementation_owned')
    planned_implementation_date = models.DateField(null=True, blank=True)
    actual_implementation_date = models.DateField(null=True, blank=True)

    effectiveness_method = models.CharField(max_length=180, blank=True)
    effectiveness_criteria = models.TextField(blank=True)
    effectiveness_result = models.CharField(max_length=30, choices=EFFECTIVENESS_CHOICES, blank=True)
    effectiveness_evidence = models.TextField(blank=True)
    effectiveness_review_date = models.DateField(null=True, blank=True)
    effectiveness_verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='change_controls_effectiveness_verified')

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='initiated', db_index=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='change_controls_owned')
    qa_reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='change_controls_reviewed')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='change_controls_approved')
    approved_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='change_controls_closed')
    closed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='change_controls_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Change Control'
        verbose_name_plural = 'Change Controls'

    def __str__(self):
        return f'{self.change_number} - {self.qms_action.title}'

    def save(self, *args, **kwargs):
        if not self.change_number:
            self.change_number = self.generate_change_number()
        super().save(*args, **kwargs)

    @classmethod
    def generate_change_number(cls):
        from django.db.models import Max
        from django.utils import timezone
        prefix = f'CC{timezone.now().year}'
        maximum = cls.objects.filter(change_number__startswith=prefix).aggregate(Max('change_number'))['change_number__max']
        try:
            next_number = int(maximum.replace(prefix, '')) + 1 if maximum else 1
        except (AttributeError, ValueError):
            next_number = 1
        while True:
            candidate = f'{prefix}{next_number:05d}'
            if not cls.objects.filter(change_number=candidate).exists():
                return candidate
            next_number += 1

    @property
    def impact_assessed(self):
        return bool(self.impact_summary.strip() and any((
            self.quality_impact, self.gmp_impact, self.validation_impact,
            self.regulatory_impact, self.documentation_impact, self.training_impact,
            self.stability_impact, self.inventory_impact,
        )))

    @property
    def ready_for_approval(self):
        return bool(self.justification.strip() and self.proposed_state.strip() and self.impact_assessed and self.owner_id)

    @property
    def ready_for_closure(self):
        return bool(
            self.approved_by_id and self.actual_implementation_date
            and self.implementation_notes.strip()
            and self.effectiveness_result == 'effective'
            and self.effectiveness_criteria.strip()
            and self.effectiveness_evidence.strip()
            and self.effectiveness_verified_by_id
        )


class QMSRecordLink(models.Model):
    """Auditable relationship between any two QMS records.

    This keeps cross-module traceability extensible: a deviation can point to a
    CAPA, risk, change, document, audit, batch result, or another governed record
    without adding a new nullable foreign key for every future module.
    """

    LINK_TYPE_CHOICES = [
        ('source', 'Source / Origin'),
        ('caused_by', 'Caused By'),
        ('addresses', 'Addresses'),
        ('implements', 'Implements'),
        ('impacts', 'Impacts'),
        ('supports', 'Supports'),
        ('supersedes', 'Supersedes'),
        ('related', 'Related'),
    ]

    from_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='qms_links_from')
    from_object_id = models.PositiveBigIntegerField()
    from_record = GenericForeignKey('from_content_type', 'from_object_id')
    to_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='qms_links_to')
    to_object_id = models.PositiveBigIntegerField()
    to_record = GenericForeignKey('to_content_type', 'to_object_id')
    link_type = models.CharField(max_length=30, choices=LINK_TYPE_CHOICES, default='related')
    rationale = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_record_links_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['from_content_type', 'from_object_id', 'to_content_type', 'to_object_id', 'link_type'],
                name='unique_qms_record_link',
            ),
        ]

    def __str__(self):
        return f'{self.from_record} {self.get_link_type_display()} {self.to_record}'


class QMSComplaintRecall(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigation', 'Investigation'),
        ('recall_assessment', 'Recall Assessment'),
        ('response_sent', 'Response Sent'),
        ('closed', 'Closed'),
    ]
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    complaint_number = models.CharField(max_length=30, unique=True, blank=True)
    qms_action = models.ForeignKey(QMSAction, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaint_recalls')
    bmr = models.ForeignKey(BMR, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_complaints')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_complaints')
    market = models.CharField(max_length=120, blank=True)
    customer = models.CharField(max_length=160, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='open')
    description = models.TextField()
    health_risk_assessment = models.TextField(blank=True)
    recall_decision = models.CharField(max_length=120, blank=True)
    customer_response = models.TextField(blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.complaint_number} - {self.product}'

    def save(self, *args, **kwargs):
        if not self.complaint_number:
            self.complaint_number = self._generate_number()
        super().save(*args, **kwargs)

    @classmethod
    def _generate_number(cls):
        from django.db.models import Max
        from django.utils import timezone

        prefix = f'COM{timezone.now().year}'
        max_number = cls.objects.filter(complaint_number__startswith=prefix).aggregate(Max('complaint_number'))['complaint_number__max']
        next_num = 1
        if max_number:
            try:
                next_num = int(max_number.replace(prefix, '')) + 1
            except ValueError:
                next_num = 1
        while True:
            candidate = f'{prefix}{next_num:05d}'
            if not cls.objects.filter(complaint_number=candidate).exists():
                return candidate
            next_num += 1


class QMSRegulatoryPackage(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('compiling', 'Compiling'),
        ('qa_review', 'QA Review'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
        ('closed', 'Closed'),
    ]

    package_number = models.CharField(max_length=30, unique=True, blank=True)
    title = models.CharField(max_length=180)
    market = models.CharField(max_length=120, blank=True)
    authority = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    dossier_reference = models.CharField(max_length=160, blank=True)
    submission_type = models.CharField(max_length=100, blank=True)
    scope_summary = models.TextField(blank=True)
    dossier_summary = models.TextField(blank=True)
    internal_qa_notes = models.TextField(blank=True)
    authority_reference = models.CharField(max_length=160, blank=True)
    authority_response = models.TextField(blank=True)
    deficiencies = models.TextField(blank=True)
    commitments = models.TextField(blank=True)
    outcome_notes = models.TextField(blank=True)
    included_documents = models.ManyToManyField(QMSDocument, blank=True, related_name='regulatory_packages')
    submission_date = models.DateField(null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_regulatory_packages')
    qa_reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_regulatory_packages_reviewed')
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_regulatory_packages_submitted')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_regulatory_packages_approved')
    internal_approval_date = models.DateField(null=True, blank=True)
    authority_response_date = models.DateField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submission_date', 'title']

    def __str__(self):
        return f'{self.package_number} - {self.title}'

    def save(self, *args, **kwargs):
        if not self.package_number:
            self.package_number = self._generate_number()
        super().save(*args, **kwargs)

    @classmethod
    def _generate_number(cls):
        from django.db.models import Max
        from django.utils import timezone

        prefix = f'REG{timezone.now().year}'
        max_number = cls.objects.filter(package_number__startswith=prefix).aggregate(Max('package_number'))['package_number__max']
        next_num = 1
        if max_number:
            try:
                next_num = int(max_number.replace(prefix, '')) + 1
            except ValueError:
                next_num = 1
        while True:
            candidate = f'{prefix}{next_num:05d}'
            if not cls.objects.filter(package_number=candidate).exists():
                return candidate
            next_num += 1

    @property
    def ready_for_qa_review(self):
        return bool(self.title.strip() and self.market.strip() and self.authority.strip() and self.owner_id and self.scope_summary.strip() and self.dossier_summary.strip() and self.included_documents.exists())

    @property
    def ready_for_submission(self):
        return bool(self.status == 'qa_review' and self.qa_reviewer_id and self.internal_approval_date and self.internal_qa_notes.strip())

    @property
    def ready_for_close(self):
        return bool(self.status == 'approved' and self.approved_by_id and self.outcome_notes.strip())


class QMSNotificationRule(models.Model):
    TRIGGER_CHOICES = [
        ('document_expiry', 'Document Expiry'),
        ('capa_overdue', 'CAPA Overdue'),
        ('change_control_overdue', 'Change Control Overdue'),
        ('change_control_due', 'Change Control Due'),
        ('audit_due', 'Audit Due'),
        ('calibration_due', 'Calibration Due'),
        ('training_overdue', 'Training Overdue'),
        ('stability_pull_due', 'Stability Pull Due'),
    ]

    name = models.CharField(max_length=160)
    trigger_type = models.CharField(max_length=40, choices=TRIGGER_CHOICES)
    days_before = models.PositiveSmallIntegerField(default=7)
    role_to_notify = models.CharField(max_length=80, default='qa')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['trigger_type', 'days_before']

    def __str__(self):
        return self.name


class QMSLabInvestigation(models.Model):
    """QC-led OOS/OOT/atypical-result investigation with QA escalation."""

    EVENT_TYPE_CHOICES = [
        ('oos', 'Out of Specification'),
        ('oot', 'Out of Trend'),
        ('atypical', 'Atypical Result'),
        ('lab_error', 'Laboratory Error'),
        ('method_deviation', 'Method Deviation'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('phase1_lab_review', 'Phase 1 Lab Review'),
        ('phase2_full_investigation', 'Phase 2 Full Investigation'),
        ('qa_review', 'QA Review'),
        ('capa_required', 'CAPA Required'),
        ('closed', 'Closed'),
    ]
    DISPOSITION_CHOICES = [
        ('pending', 'Pending'),
        ('valid_result', 'Valid Result'),
        ('invalid_lab_error', 'Invalid - Lab Error'),
        ('retest_required', 'Retest Required'),
        ('batch_reject', 'Batch Reject'),
        ('batch_release_with_justification', 'Release With Justification'),
    ]

    investigation_number = models.CharField(max_length=30, unique=True, blank=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES, db_index=True)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='open', db_index=True)
    disposition = models.CharField(max_length=40, choices=DISPOSITION_CHOICES, default='pending')
    qms_action = models.ForeignKey(QMSAction, on_delete=models.SET_NULL, null=True, blank=True, related_name='lab_investigations')
    quality_lot = models.ForeignKey(QualityInspectionLot, on_delete=models.SET_NULL, null=True, blank=True, related_name='lab_investigations')
    bmr = models.ForeignKey(BMR, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_lab_investigations')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_lab_investigations')
    test_name = models.CharField(max_length=160)
    specification = models.CharField(max_length=255, blank=True)
    result_value = models.CharField(max_length=120, blank=True)
    trend_reference = models.CharField(max_length=160, blank=True)
    analyst_review = models.TextField(blank=True)
    instrument_review = models.TextField(blank=True)
    method_review = models.TextField(blank=True)
    sample_review = models.TextField(blank=True)
    retest_result = models.CharField(max_length=120, blank=True)
    root_cause = models.TextField(blank=True)
    qa_conclusion = models.TextField(blank=True)
    capa_action = models.ForeignKey(QMSAction, on_delete=models.SET_NULL, null=True, blank=True, related_name='lab_investigation_capas')
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_lab_investigations_opened')
    qa_reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_lab_investigations_reviewed')
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-opened_at']
        verbose_name = 'QMS Lab Investigation'
        verbose_name_plural = 'QMS Lab Investigations'

    def __str__(self):
        return f'{self.investigation_number} - {self.get_event_type_display()}'

    def save(self, *args, **kwargs):
        if not self.investigation_number:
            self.investigation_number = self._generate_number()
        super().save(*args, **kwargs)

    @classmethod
    def _generate_number(cls):
        from django.db.models import Max
        from django.utils import timezone

        prefix = f'LAB{timezone.now().year}'
        max_number = cls.objects.filter(investigation_number__startswith=prefix).aggregate(Max('investigation_number'))['investigation_number__max']
        next_num = 1
        if max_number:
            try:
                next_num = int(max_number.replace(prefix, '')) + 1
            except ValueError:
                next_num = 1
        while True:
            candidate = f'{prefix}{next_num:05d}'
            if not cls.objects.filter(investigation_number=candidate).exists():
                return candidate
            next_num += 1


class QMSQualityQuery(models.Model):
    """Customer, regulatory, supplier, internal, and recall query tracker."""

    QUERY_TYPE_CHOICES = [
        ('customer', 'Customer Query'),
        ('regulatory', 'Regulatory Query'),
        ('supplier', 'Supplier Query'),
        ('internal', 'Internal Query'),
        ('recall', 'Recall Query'),
        ('market_complaint', 'Market Complaint Query'),
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('triage', 'Triage'),
        ('investigation', 'Investigation'),
        ('response_draft', 'Response Draft'),
        ('qa_review', 'QA Review'),
        ('qa_approved', 'QA Approved'),
        ('responded', 'Responded'),
        ('closed', 'Closed'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    query_number = models.CharField(max_length=30, unique=True, blank=True)
    query_type = models.CharField(max_length=30, choices=QUERY_TYPE_CHOICES, db_index=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='open', db_index=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    source = models.CharField(max_length=160, blank=True)
    subject = models.CharField(max_length=180)
    question = models.TextField()
    response = models.TextField(blank=True)
    impact_assessment = models.TextField(blank=True)
    containment_action = models.TextField(blank=True)
    investigation_notes = models.TextField(blank=True)
    root_cause = models.TextField(blank=True)
    qa_review_notes = models.TextField(blank=True)
    resolution = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    qms_action = models.ForeignKey(QMSAction, on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_queries')
    complaint_recall = models.ForeignKey(QMSComplaintRecall, on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_queries')
    regulatory_package = models.ForeignKey(QMSRegulatoryPackage, on_delete=models.SET_NULL, null=True, blank=True, related_name='quality_queries')
    bmr = models.ForeignKey(BMR, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_quality_queries')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_quality_queries')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_quality_queries_assigned')
    responded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_quality_queries_responded')
    qa_approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_quality_queries_approved')
    qa_approved_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_quality_queries_closed')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='qms_quality_queries_created')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'QMS Quality Query'
        verbose_name_plural = 'QMS Quality Queries'

    def __str__(self):
        return f'{self.query_number} - {self.subject}'

    def save(self, *args, **kwargs):
        if not self.query_number:
            self.query_number = self._generate_number()
        super().save(*args, **kwargs)

    @classmethod
    def _generate_number(cls):
        from django.db.models import Max
        from django.utils import timezone

        prefix = f'QRY{timezone.now().year}'
        max_number = cls.objects.filter(query_number__startswith=prefix).aggregate(Max('query_number'))['query_number__max']
        next_num = 1
        if max_number:
            try:
                next_num = int(max_number.replace(prefix, '')) + 1
            except ValueError:
                next_num = 1
        while True:
            candidate = f'{prefix}{next_num:05d}'
            if not cls.objects.filter(query_number=candidate).exists():
                return candidate
            next_num += 1

    @property
    def ready_for_qa_review(self):
        return bool(self.question.strip() and self.assigned_to_id and self.investigation_notes.strip() and self.response.strip())

    @property
    def ready_for_close(self):
        return bool(self.qa_approved_by_id and self.resolution.strip() and self.responded_by_id)


# ============================================================================
# QMS COLLABORATION & AUDIT TRAIL MODELS
# ============================================================================

class QMSAttachment(models.Model):
    """File attachments for any QMS record (Actions, Audits, Risks, Documents, etc.)"""
    
    # Generic foreign key to attach to any QMS model
    qms_action = models.ForeignKey(QMSAction, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    qms_audit = models.ForeignKey(QMSAudit, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    qms_risk = models.ForeignKey(QMSRiskAssessment, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    qms_document = models.ForeignKey(QMSDocument, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    qms_deviation = models.ForeignKey(QMSDeviation, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    qms_quality_query = models.ForeignKey(QMSQualityQuery, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    qms_regulatory_package = models.ForeignKey(QMSRegulatoryPackage, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    qms_training = models.ForeignKey(QMSTrainingRecord, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    qms_calibration = models.ForeignKey(QMSCalibrationRecord, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    qms_coa = models.ForeignKey(QMSCOA, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    qms_material_qc = models.ForeignKey(QMSMaterialQC, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    qms_stability = models.ForeignKey(QMSStabilitySchedule, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    lab_investigation = models.ForeignKey(QMSLabInvestigation, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    qms_supplier_quality = models.ForeignKey(QMSSupplierQualification, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    
    file = models.FileField(upload_to='qms_attachments/%Y/%m/')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100, blank=True)  # PDF, DOCX, JPG, etc.
    file_size = models.PositiveIntegerField(default=0)  # bytes
    description = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='qms_uploads')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f'{self.filename} ({self.uploaded_by})'
    
    def save(self, *args, **kwargs):
        if self.file:
            self.filename = self.file.name.split('/')[-1]
            self.file_size = self.file.size
            # Extract file extension
            if '.' in self.filename:
                self.file_type = self.filename.split('.')[-1].upper()
        super().save(*args, **kwargs)


class QMSComment(models.Model):
    """Comments/discussion thread for QMS records"""
    
    # Generic foreign key to attach to any QMS model
    qms_action = models.ForeignKey(QMSAction, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    qms_audit = models.ForeignKey(QMSAudit, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    qms_risk = models.ForeignKey(QMSRiskAssessment, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    qms_document = models.ForeignKey(QMSDocument, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    qms_deviation = models.ForeignKey(QMSDeviation, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    qms_quality_query = models.ForeignKey(QMSQualityQuery, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    qms_regulatory_package = models.ForeignKey(QMSRegulatoryPackage, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    qms_training = models.ForeignKey(QMSTrainingRecord, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    qms_calibration = models.ForeignKey(QMSCalibrationRecord, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    qms_coa = models.ForeignKey(QMSCOA, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    qms_material_qc = models.ForeignKey(QMSMaterialQC, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    qms_stability = models.ForeignKey(QMSStabilitySchedule, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    lab_investigation = models.ForeignKey(QMSLabInvestigation, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    qms_supplier_quality = models.ForeignKey(QMSSupplierQualification, on_delete=models.CASCADE, null=True, blank=True, related_name='comments')
    
    comment_text = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='qms_comments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_internal = models.BooleanField(default=False)  # Internal QA notes vs visible to all
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f'{self.user} - {self.created_at.strftime("%Y-%m-%d %H:%M")}'


class QMSActivityLog(models.Model):
    """Audit trail for all changes to QMS records"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('status_changed', 'Status Changed'),
        ('assigned', 'Assigned'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('file_uploaded', 'File Uploaded'),
        ('comment_added', 'Comment Added'),
        ('linked', 'Linked Record'),
        ('deleted', 'Deleted'),
    ]
    
    # Generic foreign key to attach to any QMS model
    qms_action = models.ForeignKey(QMSAction, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_log')
    qms_audit = models.ForeignKey(QMSAudit, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_log')
    qms_risk = models.ForeignKey(QMSRiskAssessment, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_log')
    qms_document = models.ForeignKey(QMSDocument, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_log')
    qms_deviation = models.ForeignKey(QMSDeviation, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_log')
    qms_quality_query = models.ForeignKey(QMSQualityQuery, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_log')
    qms_regulatory_package = models.ForeignKey(QMSRegulatoryPackage, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_log')
    qms_training = models.ForeignKey(QMSTrainingRecord, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_log')
    qms_calibration = models.ForeignKey(QMSCalibrationRecord, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_log')
    qms_coa = models.ForeignKey(QMSCOA, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_log')
    qms_material_qc = models.ForeignKey(QMSMaterialQC, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_log')
    qms_stability = models.ForeignKey(QMSStabilitySchedule, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_log')
    lab_investigation = models.ForeignKey(QMSLabInvestigation, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_log')
    qms_supplier_quality = models.ForeignKey(QMSSupplierQualification, on_delete=models.CASCADE, null=True, blank=True, related_name='activity_log')
    
    action_type = models.CharField(max_length=30, choices=ACTION_CHOICES, db_index=True)
    field_changed = models.CharField(max_length=100, blank=True)  # e.g., "status", "priority"
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    description = models.TextField(blank=True)  # Human-readable description
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='qms_activities')
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
        ]
    
    def __str__(self):
        return f'{self.action_type} by {self.user} at {self.timestamp.strftime("%Y-%m-%d %H:%M")}'
