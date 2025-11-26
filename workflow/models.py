from django.db import models
from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from bmr.models import BMR

# Import the extended admin settings models
from .models_admin_settings import (
    DashboardSettings, SystemAlertSettings, SessionManagementSettings, 
    ProductionLimitsSettings, get_dashboard_setting, get_alert_setting,
    get_session_setting, get_production_limit
)

class SystemTimingSettings(models.Model):
    """Configurable system-wide timing settings"""
    
    setting_name = models.CharField(
        max_length=100, 
        unique=True,
        help_text="Unique identifier for this timing setting"
    )
    setting_value = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        help_text="Numeric value for this setting"
    )
    description = models.TextField(
        help_text="Description of what this setting controls"
    )
    unit = models.CharField(
        max_length=20,
        default='hours',
        help_text="Unit of measurement (hours, minutes, percentage, etc.)"
    )
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['setting_name']
        verbose_name = "System Timing Setting"
        verbose_name_plural = "System Timing Settings"
    
    def __str__(self):
        return f"{self.setting_name}: {self.setting_value} {self.unit}"
    
    @classmethod
    def get_setting(cls, setting_name, default_value=None):
        """Get a system timing setting value"""
        try:
            return float(cls.objects.get(setting_name=setting_name).setting_value)
        except cls.DoesNotExist:
            return default_value
    
    @classmethod
    def get_default_duration(cls):
        """Get the default phase duration"""
        return cls.get_setting('default_phase_duration_hours', None)
    
    @classmethod
    def get_warning_threshold(cls):
        """Get warning threshold percentage"""
        return cls.get_setting('warning_threshold_percentage', 80.0)
    
    @classmethod
    def get_overrun_threshold(cls):
        """Get overrun threshold percentage"""
        return cls.get_setting('overrun_threshold_percentage', 120.0)
    
    @classmethod
    def get_warning_time_minutes(cls):
        """Get warning time in minutes"""
        return cls.get_setting('warning_time_minutes', 30.0)

class Machine(models.Model):
    """Machine model for production phases"""
    
    MACHINE_TYPE_CHOICES = [
        ('granulation', 'Granulation'),
        ('blending', 'Blending'),
        ('compression', 'Compression'),
        ('coating', 'Coating'),
        ('blister_packing', 'Blister Packing'),
        ('filling', 'Filling'),  # For capsules
    ]
    
    name = models.CharField(max_length=100)
    machine_type = models.CharField(max_length=20, choices=MACHINE_TYPE_CHOICES)
    is_active = models.BooleanField(default=True, help_text="Active machines are available for selection")
    created_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['machine_type', 'name']
        unique_together = ['name', 'machine_type']
    
    def __str__(self):
        return f"{self.name} ({self.get_machine_type_display()})"

class ProductionPhase(models.Model):
    """Defines the production phases for different product types"""
    
    PHASE_CHOICES = [
        # Common phases
        ('bmr_creation', 'BMR Creation'),
        ('regulatory_approval', 'Regulatory Approval'),
        ('material_dispensing', 'Material Dispensing'),
        ('quality_control', 'Quality Control'),
        ('post_compression_qc', 'Post-Compression QC'),
        ('post_mixing_qc', 'Post-Mixing QC'),
        ('post_blending_qc', 'Post-Blending QC'),
        ('packaging_material_release', 'Packaging Material Release'),
        ('secondary_packaging', 'Secondary Packaging'),
        ('final_qa', 'Final QA'),
        ('finished_goods_store', 'Finished Goods Store'),
        
        # Ointment specific phases
        ('mixing', 'Mixing'),
        ('tube_filling', 'Tube Filling'),
        
        # Tablet specific phases
        ('granulation', 'Granulation'),
        ('blending', 'Blending'),
        ('compression', 'Compression'),
        ('sorting', 'Sorting'),
        ('coating', 'Coating'),
        ('blister_packing', 'Blister Packing'),
        ('bulk_packing', 'Bulk Packing'),
        
        # Capsule specific phases
        ('drying', 'Drying'),
        ('filling', 'Filling'),
    ]
    
    PRODUCT_TYPE_CHOICES = [
        ('ointment', 'Ointment'),
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
    ]
    
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)
    phase_name = models.CharField(max_length=30, choices=PHASE_CHOICES)
    phase_order = models.IntegerField()
    description = models.TextField(blank=True, help_text="Description of this phase")
    is_mandatory = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    can_rollback_to = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Phase to rollback to if this phase fails"
    )
    estimated_duration_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['product_type', 'phase_name']
        ordering = ['product_type', 'phase_order']
    
    def __str__(self):
        return f"{self.get_product_type_display()} - {self.get_phase_name_display()}"

class BatchPhaseExecution(models.Model):
    """Tracks the execution of phases for each batch"""
    
    STATUS_CHOICES = [
        ('not_ready', 'Not Ready'),
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
        ('rolled_back', 'Rolled Back'),
    ]
    
    bmr = models.ForeignKey(BMR, on_delete=models.CASCADE, related_name='phase_executions')
    phase = models.ForeignKey(ProductionPhase, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Execution tracking
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='started_phases'
    )
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='completed_phases'
    )
    
    # Timestamps
    created_date = models.DateTimeField(auto_now_add=True)
    started_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    # Phase specific data
    phase_data = models.JSONField(default=dict, blank=True)
    operator_comments = models.TextField(blank=True)
    qa_comments = models.TextField(blank=True)
    
    # Machine tracking
    machine_used = models.ForeignKey('Machine', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Breakdown tracking
    breakdown_occurred = models.BooleanField(default=False)
    breakdown_start_time = models.DateTimeField(null=True, blank=True)
    breakdown_end_time = models.DateTimeField(null=True, blank=True)
    breakdown_reason = models.TextField(blank=True)
    
    # Changeover tracking
    changeover_occurred = models.BooleanField(default=False)
    changeover_start_time = models.DateTimeField(null=True, blank=True)
    changeover_end_time = models.DateTimeField(null=True, blank=True)
    changeover_reason = models.TextField(blank=True)
    
    # Quality control
    qc_approved = models.BooleanField(null=True, blank=True)
    qc_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='qc_approved_phases'
    )
    qc_approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['bmr', 'phase']
        ordering = ['bmr', 'phase__phase_order']
    
    def __str__(self):
        return f"{self.bmr.batch_number} - {self.phase.get_phase_name_display()} ({self.status})"
    
    def requires_machine_selection(self):
        """Check if this phase requires machine selection"""
        machine_required_phases = [
            'granulation', 'blending', 'compression', 
            'coating', 'blister_packing', 'filling'
        ]
        return self.phase.phase_name in machine_required_phases
    
    def get_breakdown_duration(self):
        """Calculate breakdown duration in minutes"""
        if self.breakdown_occurred and self.breakdown_start_time and self.breakdown_end_time:
            delta = self.breakdown_end_time - self.breakdown_start_time
            return delta.total_seconds() / 60
        return 0
    
    def get_changeover_duration(self):
        """Calculate changeover duration in minutes"""
        if self.changeover_occurred and self.changeover_start_time and self.changeover_end_time:
            delta = self.changeover_end_time - self.changeover_start_time
            return delta.total_seconds() / 60
        return 0
    
    @property
    def breakdown_duration_minutes(self):
        """Property for template use - breakdown duration in minutes"""
        return round(self.get_breakdown_duration(), 1) if self.get_breakdown_duration() > 0 else None
    
    @property
    def changeover_duration_minutes(self):
        """Property for template use - changeover duration in minutes"""
        return round(self.get_changeover_duration(), 1) if self.get_changeover_duration() > 0 else None
        
    def get_phase_duration_hours(self):
        """Calculate the duration of this phase execution in hours"""
        if self.started_date:
            if self.completed_date:
                # For completed phases, use actual completion time
                duration = self.completed_date - self.started_date
            else:
                # For active phases, calculate from start to now
                from django.utils import timezone
                duration = timezone.now() - self.started_date
            return round(duration.total_seconds() / 3600, 2)
        return None
        
    @property
    def duration_hours(self):
        """Property for template use - phase duration in hours"""
        return self.get_phase_duration_hours()
        
    @property
    def formatted_duration(self):
        """Return a formatted string representation of the phase duration"""
        hours = self.get_phase_duration_hours()
        if hours is not None:
            h = int(hours)
            m = int((hours - h) * 60)
            if h > 0:
                return f"{h}h {m}m"
            else:
                return f"{m}m"
        return "--"
    
    def get_next_phase(self):
        """Get the next phase in the workflow"""
        product_type = self.bmr.product.product_type
        current_order = self.phase.phase_order
        # Handle special cases for tablet coating
        if (product_type in ['tablet_normal', 'tablet_2'] and 
            self.phase.phase_name == 'sorting'):
            if self.bmr.product.is_coated:
                # Go to coating phase
                next_phase = ProductionPhase.objects.filter(
                    product_type=product_type,
                    phase_name='coating'
                ).first()
            else:
                # Skip coating, go to packaging
                next_phase = ProductionPhase.objects.filter(
                    product_type=product_type,
                    phase_name='packaging_material_release'
                ).first()
        else:
            # Normal sequential flow
            next_phase = ProductionPhase.objects.filter(
                product_type=product_type,
                phase_order__gt=current_order
            ).first()
        return next_phase
    
    def trigger_next_phase(self):
        """Automatically trigger the next phase when current phase completes"""
        if self.status == 'completed':
            next_phase = self.get_next_phase()
            if next_phase:
                BatchPhaseExecution.objects.get_or_create(
                    bmr=self.bmr,
                    phase=next_phase,
                    defaults={'status': 'pending'}
                )

class PhaseOperator(models.Model):
    """Maps operators to specific phases they can handle"""
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phase = models.ForeignKey(ProductionPhase, on_delete=models.CASCADE)
    is_primary_operator = models.BooleanField(default=False)
    can_approve = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'phase']
    
    def __str__(self):
        return f"{self.user.username} - {self.phase.get_phase_name_display()}"

class PhaseCheckpoint(models.Model):
    """Quality checkpoints within phases"""
    
    phase_execution = models.ForeignKey(
        BatchPhaseExecution, 
        on_delete=models.CASCADE, 
        related_name='checkpoints'
    )
    checkpoint_name = models.CharField(max_length=200)
    expected_value = models.CharField(max_length=200)
    actual_value = models.CharField(max_length=200, blank=True)
    is_within_spec = models.BooleanField(null=True, blank=True)
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    checked_date = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.phase_execution} - {self.checkpoint_name}"


class PhaseTimingSetting(models.Model):
    """Settings for phase timing and overrun notifications"""
    
    phase = models.OneToOneField(
        ProductionPhase, 
        on_delete=models.CASCADE, 
        related_name='timing_setting'
    )
    expected_duration_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text='Expected duration in hours',
        validators=[validators.MinValueValidator(0.01)]
    )
    warning_threshold_percent = models.PositiveIntegerField(
        default=20,
        help_text='Percentage over expected duration before warning (e.g. 20 for 20%)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='phase_timings_created'
    )
    
    class Meta:
        verbose_name = 'Phase Timing Setting'
        verbose_name_plural = 'Phase Timing Settings'
        ordering = ['phase__phase_name']
    
    def __str__(self):
        return f"{self.phase.get_phase_name_display()} - {self.expected_duration_hours}h"


class ProductMachineTimingSetting(models.Model):
    """Enhanced timing settings for Product + Machine + Phase combinations"""
    
    # Core references
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    machine = models.ForeignKey(
        Machine, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Leave blank for non-machine phases"
    )
    phase = models.ForeignKey(ProductionPhase, on_delete=models.CASCADE)
    
    # Timing settings
    expected_duration_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text='Expected duration for this product-machine-phase combination',
        validators=[validators.MinValueValidator(0.01)]
    )
    warning_threshold_percent = models.PositiveIntegerField(
        default=20,
        help_text='Percentage over expected duration before warning (e.g. 20 for 20%)'
    )
    
    # Meta information
    is_active = models.BooleanField(default=True, help_text="Active timing settings")
    notes = models.TextField(
        blank=True,
        help_text="Notes about this timing setting (e.g., 'Machine A is slower for heavy products')"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='product_machine_timings_created'
    )
    
    class Meta:
        unique_together = ['product', 'machine', 'phase']
        verbose_name = 'Product-Machine Timing Setting'
        verbose_name_plural = 'Product-Machine Timing Settings'
        ordering = ['product__product_name', 'phase__phase_name', 'machine__name']
    
    def __str__(self):
        machine_name = self.machine.name if self.machine else "No Machine"
        return f"{self.product.product_name} + {machine_name} + {self.phase.get_phase_name_display()}: {self.expected_duration_hours}h"
    
    @property
    def timing_type(self):
        """Return the type of timing setting for display"""
        if self.machine:
            return f"Product + Machine Specific"
        else:
            return f"Product Specific (No Machine)"

    @staticmethod
    def get_expected_duration_for_execution(batch_phase_execution):
        """
        Get expected duration with Product + Machine priority system
        
        Priority:
        1. Product + Machine + Phase specific timing
        2. Product + Phase (no machine) timing  
        3. Default phase timing (current PhaseTimingSetting)
        4. System default (2.0 hours)
        """
        bmr = batch_phase_execution.bmr
        phase = batch_phase_execution.phase
        machine = batch_phase_execution.machine_used
        
        # Priority 1: Product + Machine + Phase specific timing
        if machine:
            specific_timing = ProductMachineTimingSetting.objects.filter(
                product=bmr.product,
                machine=machine,
                phase=phase,
                is_active=True
            ).first()
            if specific_timing:
                return float(specific_timing.expected_duration_hours)
        
        # Priority 2: Product + Phase (no machine) timing
        product_timing = ProductMachineTimingSetting.objects.filter(
            product=bmr.product,
            machine__isnull=True,
            phase=phase,
            is_active=True
        ).first()
        if product_timing:
            return float(product_timing.expected_duration_hours)
        
        # Priority 3: Default phase timing (current system)
        try:
            if hasattr(phase, 'timing_setting') and phase.timing_setting:
                return float(phase.timing_setting.expected_duration_hours)
        except:
            pass
        
        # Priority 4: System default with warning flag
        # Return reasonable default instead of crashing the system
        return SystemTimingSettings.get_setting('default_non_machine_phase_duration_hours', 0.17)
    
    @staticmethod
    def is_timing_configuration_missing(batch_phase_execution):
        """Check if timing configuration is missing and needs admin attention"""
        bmr = batch_phase_execution.bmr
        phase = batch_phase_execution.phase
        machine = batch_phase_execution.machine_used
        
        # Check if we have any proper timing configuration
        # Priority 1: Product + Machine + Phase specific timing
        if machine:
            specific_timing = ProductMachineTimingSetting.objects.filter(
                product=bmr.product,
                machine=machine,
                phase=phase,
                is_active=True
            ).exists()
            if specific_timing:
                return False
        
        # Priority 2: Product + Phase (no machine) timing
        product_timing = ProductMachineTimingSetting.objects.filter(
            product=bmr.product,
            machine__isnull=True,
            phase=phase,
            is_active=True
        ).exists()
        if product_timing:
            return False
        
        # Priority 3: Default phase timing
        try:
            if hasattr(phase, 'timing_setting') and phase.timing_setting:
                return False
        except:
            pass
        
        # No configuration found - needs admin attention
        return True
    
    @staticmethod
    def get_safe_timing_for_execution(batch_phase_execution):
        """
        Get timing configuration with graceful fallback and user messaging
        Returns: (expected_hours, is_configured, warning_message)
        """
        try:
            expected_hours = ProductMachineTimingSetting.get_expected_duration_for_execution(batch_phase_execution)
            is_missing = ProductMachineTimingSetting.is_timing_configuration_missing(batch_phase_execution)
            
            if is_missing:
                # Use reasonable defaults based on phase type
                phase_name = batch_phase_execution.phase.phase_name
                machine_phases = ['granulation', 'blending', 'compression', 'coating', 'filling', 'blister_packing', 'tube_filling']
                
                if phase_name in machine_phases:
                    default_hours = SystemTimingSettings.get_setting('default_machine_phase_duration_hours', 4.0)
                else:
                    default_hours = SystemTimingSettings.get_setting('default_non_machine_phase_duration_hours', 0.17)
                    
                warning_msg = f"⚠️ No timing configured for {phase_name}. Using default {default_hours}h. Contact admin to set proper timing."
                return default_hours, False, warning_msg
            else:
                return expected_hours, True, None
                
        except Exception as e:
            # Ultimate fallback
            fallback_hours = SystemTimingSettings.get_setting('system_error_fallback_hours', 8.0)
            return fallback_hours, False, f"⚠️ Timing system error. Using {fallback_hours}h default. Contact admin."
    
    @staticmethod
    def get_warning_threshold_for_execution(batch_phase_execution):
        """Get warning threshold percentage with same priority system"""
        bmr = batch_phase_execution.bmr
        phase = batch_phase_execution.phase
        machine = batch_phase_execution.machine_used
        
        # Priority 1: Product + Machine + Phase specific
        if machine:
            specific_timing = ProductMachineTimingSetting.objects.filter(
                product=bmr.product,
                machine=machine,
                phase=phase,
                is_active=True
            ).first()
            if specific_timing:
                return specific_timing.warning_threshold_percent
        
        # Priority 2: Product + Phase (no machine)
        product_timing = ProductMachineTimingSetting.objects.filter(
            product=bmr.product,
            machine__isnull=True,
            phase=phase,
            is_active=True
        ).first()
        if product_timing:
            return product_timing.warning_threshold_percent
        
        # Priority 3: Default phase timing
        try:
            if hasattr(phase, 'timing_setting') and phase.timing_setting:
                return phase.timing_setting.warning_threshold_percent
        except:
            pass
        
        # Priority 4: System default
        return SystemTimingSettings.get_setting('default_warning_threshold_percent', 20)


class PhaseOverrunNotification(models.Model):
    """Notifications for phase overruns"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Response'),
        ('responded', 'Operator Responded'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    phase_execution = models.ForeignKey(
        BatchPhaseExecution,
        on_delete=models.CASCADE,
        related_name='overrun_notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expected_duration = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Expected duration in hours'
    )
    actual_duration = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Actual duration in hours'
    )
    operator_response = models.TextField(blank=True)
    response_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    admin_comments = models.TextField(blank=True)
    admin_review_time = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Phase Overrun Notification'
        verbose_name_plural = 'Phase Overrun Notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.phase_execution.bmr.batch_number} - {self.phase_execution.phase.get_phase_name_display()} Overrun"


class PhaseTimeOverrunNotification(models.Model):
    """Time-based overrun notifications for phases"""
    
    phase_execution = models.ForeignKey(
        BatchPhaseExecution,
        on_delete=models.CASCADE,
        related_name='time_overrun_notifications'
    )
    notified_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_overrun_notifications'
    )
    notification_time = models.DateTimeField(auto_now_add=True)
    threshold_exceeded_percent = models.PositiveIntegerField()
    message = models.TextField()
    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_overrun_notifications'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Phase Time Overrun Notification'
        verbose_name_plural = 'Phase Time Overrun Notifications'
        ordering = ['-notification_time']
    
    def __str__(self):
        return f"{self.phase_execution.bmr.batch_number} - Time Overrun {self.threshold_exceeded_percent}%"


# ============ WORKFLOW TEMPLATE MODELS ============

class WorkflowTemplate(models.Model):
    """Template for managing standard workflows for different product types"""
    
    PRODUCT_TYPE_CHOICES = [
        ('ointment', 'Ointment'),
        ('tablet', 'Tablet'), 
        ('capsule', 'Capsule'),
    ]
    
    name = models.CharField(max_length=100, help_text="Template name (e.g., 'Standard Tablet Workflow')")
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)
    description = models.TextField(blank=True, help_text="Description of when to use this template")
    is_active = models.BooleanField(default=True, help_text="Active templates are available for new BMRs")
    is_default = models.BooleanField(default=False, help_text="Default template for this product type")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['product_type', 'name']
        unique_together = [['product_type', 'name']]
    
    def __str__(self):
        return f"{self.name} ({self.get_product_type_display()})"
    
    def clean(self):
        # Ensure only one default template per product type
        if self.is_default:
            existing_default = WorkflowTemplate.objects.filter(
                product_type=self.product_type, 
                is_default=True
            )
            if self.pk:
                existing_default = existing_default.exclude(pk=self.pk)
            
            if existing_default.exists():
                raise ValidationError({
                    'is_default': f'A default template already exists for {self.product_type}: {existing_default.first().name}'
                })
    
    def get_phase_count(self):
        """Get number of phases in this template"""
        return self.phases.count()
    
    def copy_phases_from_current(self):
        """Copy current ProductionPhase definitions to this template"""
        current_phases = ProductionPhase.objects.filter(product_type=self.product_type)
        
        # Clear existing phases
        self.phases.all().delete()
        
        # Copy phases
        for phase in current_phases.order_by('phase_order'):
            WorkflowTemplatePhase.objects.create(
                template=self,
                phase_name=phase.phase_name,
                phase_order=phase.phase_order,
                description=phase.description,
                is_mandatory=phase.is_mandatory,
                requires_approval=phase.requires_approval,
                estimated_duration_hours=phase.estimated_duration_hours,
                rollback_target_order=phase.can_rollback_to.phase_order if phase.can_rollback_to else None
            )
        
        return self.phases.count()
    
    def apply_to_production_phases(self):
        """Apply this template to actual ProductionPhase models"""
        if not self.is_active:
            raise ValidationError("Cannot apply inactive template")
        
        # Delete existing phases for this product type
        ProductionPhase.objects.filter(product_type=self.product_type).delete()
        
        # Create new phases from template
        rollback_mapping = {}  # To handle rollback relationships
        created_phases = {}
        
        # First pass: Create all phases
        for template_phase in self.phases.order_by('phase_order'):
            production_phase = ProductionPhase.objects.create(
                product_type=self.product_type,
                phase_name=template_phase.phase_name,
                phase_order=template_phase.phase_order,
                description=template_phase.description,
                is_mandatory=template_phase.is_mandatory,
                requires_approval=template_phase.requires_approval,
                estimated_duration_hours=template_phase.estimated_duration_hours
            )
            created_phases[template_phase.phase_order] = production_phase
            
            if template_phase.rollback_target_order:
                rollback_mapping[production_phase] = template_phase.rollback_target_order
        
        # Second pass: Set rollback relationships
        for phase, rollback_order in rollback_mapping.items():
            if rollback_order in created_phases:
                phase.can_rollback_to = created_phases[rollback_order]
                phase.save(update_fields=['can_rollback_to'])
        
        return len(created_phases)


class WorkflowTemplatePhase(models.Model):
    """Individual phase within a workflow template"""
    
    template = models.ForeignKey(WorkflowTemplate, on_delete=models.CASCADE, related_name='phases')
    phase_name = models.CharField(max_length=50)
    phase_order = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    
    # Phase properties
    is_mandatory = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=False)
    estimated_duration_hours = models.DecimalField(max_digits=5, decimal_places=2, default=4.0)
    
    # Rollback configuration (store order number, not FK to avoid circular dependencies)
    rollback_target_order = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Phase order to rollback to if this phase fails (must be lower number)"
    )
    
    class Meta:
        ordering = ['template', 'phase_order']
        unique_together = [['template', 'phase_order'], ['template', 'phase_name']]
    
    def __str__(self):
        return f"{self.template.name}: {self.phase_order}. {self.phase_name}"
    
    def clean(self):
        if self.rollback_target_order:
            if self.rollback_target_order >= self.phase_order:
                raise ValidationError({
                    'rollback_target_order': 'Rollback target must have a lower order number than current phase'
                })
            
            # Check if target order exists in template
            if self.template_id and not self.template.phases.filter(phase_order=self.rollback_target_order).exists():
                if self.pk:  # Only check if we're updating existing record
                    raise ValidationError({
                        'rollback_target_order': f'No phase with order {self.rollback_target_order} exists in this template'
                    })

# Import and make available all admin settings models for migrations
from .models_admin_settings import (
    DashboardSettings, SystemAlertSettings, SessionManagementSettings, ProductionLimitsSettings
)
