from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from products.models import Product
from datetime import datetime
import re
import logging
from django.contrib.auth import get_user_model
from django.utils.text import slugify
import json

# Import template models
from .template_models import (
    BMRTemplateSection, BMRTemplateField, BMRTemplateTable, 
    BMRTemplateTableColumn, BMRFormData
)

class BMRTemplate(models.Model):
    """Defines a configurable template structure for the entire BMR document."""

    PRODUCT_TYPE_CHOICES = [
        ('', 'Universal (all types)'),
        ('tablet', 'Tablet (Coated / Normal)'),
        ('tablet_normal', 'Tablet Normal (legacy)'),
        ('tablet_type_2', 'Tablet Type 2 (Bulk Packing)'),
        ('ointment', 'Ointment'),
        ('capsule', 'Capsule'),
    ]

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)

    # Product-specific override: if set, this template applies ONLY to this product
    # Priority: product-specific > product_type > universal (is_active)
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bmr_templates',
        help_text=(
            "Link to a specific product. If set, this template is used exclusively "
            "for that product, overriding the product_type template."
        )
    )

    # Product type this template is for (empty = universal fallback)
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPE_CHOICES,
        blank=True,
        default='',
        db_index=True,
        help_text="The product type this template applies to. Leave blank for a universal template."
    )
    structure = models.JSONField(
        default=list,
        blank=True,
        help_text="JSON schema defining pages, sections, tables, and placeholders"
    )
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_active', '-updated_at']
        verbose_name = 'BMR Template'
        verbose_name_plural = 'BMR Templates'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        if self.is_active:
            # Only deactivate other templates of the SAME product_type so that
            # ointment / capsule / tablet templates remain independent.
            BMRTemplate.objects.filter(
                product_type=self.product_type
            ).exclude(pk=self.pk).update(is_active=False)

    @classmethod
    def get_active_template(cls):
        return cls.objects.filter(is_active=True).first()

    @classmethod
    def for_product_type(cls, product_type):
        """Return the matching template for a specific product type, or None."""
        return cls.objects.filter(product_type=product_type, product__isnull=True).first()

    @classmethod
    def for_product(cls, product):
        """
        3-tier lookup (industrial standard MFR resolution):
          1. Product-specific template (product FK matches exactly)
          2. Product-type template     (matching product_type, no product FK)
          3. Universal active template (legacy fallback)
        Returns the first match found.
        """
        if product is None:
            return cls.get_active_template()
        # Tier 1: exact product match
        specific = cls.objects.filter(product=product).first()
        if specific:
            return specific
        # Tier 2: product_type match (no product FK set = shared base for this type)
        by_type = cls.objects.filter(
            product_type=product.product_type,
            product__isnull=True
        ).first()
        if by_type:
            return by_type
        # Tier 3: global active fallback
        return cls.get_active_template()

logger = logging.getLogger(__name__)

User = get_user_model()

def validate_batch_number(value):
    """Validate batch number format XXXYYYY"""
    pattern = r'^\d{3}\d{4}$'  # 3 digits + 4 digits (e.g., 3332025)
    if not re.match(pattern, value):
        raise ValidationError(
            'Batch number must be in format XXXYYYY (e.g., 3332025)'
        )

class BMR(models.Model):
    """Batch Manufacturing Record - Core document for pharmaceutical production"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('in_production', 'In Production'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # BMR Header Information
    bmr_number = models.CharField(max_length=20, unique=True)
    batch_number = models.CharField(
        max_length=10, 
        unique=False,
        validators=[validate_batch_number],
        help_text="Enter batch number in format XXXYYYY (e.g., 3332025)"
    )
    manufacturing_date = models.DateField(
        null=True,
        blank=False,
        help_text="Enter the manufacturing date for this batch"
    )
    expiry_date = models.DateField(
        null=True,
        blank=False,
        help_text="Enter the expiry date for this batch"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    template = models.ForeignKey(
        BMRTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bmrs',
        help_text='Template structure used to render this BMR'
    )
    # Batch size now comes from Product model - these fields are for actual batch size if different from standard
    actual_batch_size = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual batch size (if different from standard product batch size)"
    )
    actual_batch_size_unit = models.CharField(
        max_length=20, 
        blank=True,
        help_text="Unit for actual batch size (inherits from product if not specified)"
    )
    
    # Dates
    created_date = models.DateTimeField(auto_now_add=True)
    planned_start_date = models.DateTimeField(null=True, blank=True)
    planned_completion_date = models.DateTimeField(null=True, blank=True)
    actual_start_date = models.DateTimeField(null=True, blank=True)
    actual_completion_date = models.DateTimeField(null=True, blank=True)
    
    # Status and Approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Personnel
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_bmrs'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='approved_bmrs'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Manufacturing Instructions
    manufacturing_instructions = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    
    # Quality Parameters
    in_process_controls = models.TextField(blank=True)
    quality_checks_required = models.TextField(blank=True)
    
    # Comments and Notes
    qa_comments = models.TextField(blank=True)
    regulatory_comments = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_date']
        verbose_name = 'Batch Manufacturing Record'
        verbose_name_plural = 'Batch Manufacturing Records'
        constraints = [
            models.UniqueConstraint(fields=['product', 'batch_number'], name='unique_product_batch_number')
        ]
    
    def __str__(self):
        return f"BMR-{self.bmr_number} | Batch: {self.batch_number} | {self.product.product_name}"

    def __init__(self, *args, **kwargs):
        # Accept legacy `quantity` kwarg used in old tests/fixtures and map to actual_batch_size
        legacy_quantity = kwargs.pop('quantity', None)
        super().__init__(*args, **kwargs)
        if legacy_quantity is not None:
            try:
                self.actual_batch_size = legacy_quantity
            except Exception:
                pass
    
    @property
    def batch_size(self):
        """Get batch size - actual if specified, otherwise standard from product"""
        return self.actual_batch_size or self.product.standard_batch_size
    
    @property
    def batch_size_unit(self):
        """Get batch size unit - actual if specified, otherwise from product"""
        return self.actual_batch_size_unit or self.product.batch_size_unit
    
    def get_template(self):
        if self.template:
            return self.template
        return BMRTemplate.for_product(self.product)

    @property
    def template_structure(self):
        template = self.get_template()
        return template.structure if template else []

    def save(self, *args, **kwargs):
        # Check if this is a status change to approved
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            try:
                old_instance = BMR.objects.get(pk=self.pk)
                old_status = old_instance.status
            except BMR.DoesNotExist:
                pass
        
        if not self.template:
            self.template = BMRTemplate.get_active_template()

        if not self.bmr_number:
            self.bmr_number = self.generate_unique_bmr_number()
        
        # Save the BMR first
        super().save(*args, **kwargs)
        
        # Initialize workflow when BMR is created or when status changes to approved
        if is_new or (old_status != 'approved' and self.status == 'approved'):
            from workflow.services import WorkflowService
            try:
                # Use new template-based initialization
                WorkflowService.initialize_workflow_from_template(self)
                logger.info(f"Workflow initialized for BMR {self.bmr_number} using template system")
                
                # If BMR is new, activate the regulatory approval phase
                if is_new:
                    from workflow.models import BatchPhaseExecution
                    regulatory_phase = BatchPhaseExecution.objects.filter(
                        bmr=self,
                        phase__phase_name='regulatory_approval'
                    ).first()
                    
                    if regulatory_phase and regulatory_phase.status == 'not_ready':
                        regulatory_phase.status = 'pending'
                        regulatory_phase.save()
                        logger.info(f"Activated regulatory approval phase for BMR {self.bmr_number}")
                
                # If status is approved, activate the raw material release phase
                elif self.status == 'approved':
                    from workflow.models import BatchPhaseExecution
                    raw_material_phase = BatchPhaseExecution.objects.filter(
                        bmr=self,
                        phase__phase_name='raw_material_release'
                    ).first()
                    
                    if raw_material_phase and raw_material_phase.status == 'not_ready':
                        raw_material_phase.status = 'pending'
                        raw_material_phase.save()
                        logger.info(f"Activated raw material release phase for BMR {self.bmr_number}")
                        
            except Exception as e:
                logger.error(f"Error initializing workflow for BMR {self.bmr_number}: {e}")

    def generate_unique_bmr_number(self):
        """Generate a truly unique BMR number for the year, even if BMRs are deleted or created concurrently."""
        from django.db.models import Max
        from datetime import datetime
        year = datetime.now().year
        prefix = f"BMR{year}"
        # Find the max number used so far for this year
        max_bmr = BMR.objects.filter(bmr_number__startswith=prefix).aggregate(Max('bmr_number'))['bmr_number__max']
        if max_bmr:
            # Extract the numeric part and increment
            try:
                last_num = int(max_bmr.replace(prefix, ""))
            except Exception:
                last_num = 0
            next_num = last_num + 1
        else:
            next_num = 1
        # Loop to ensure uniqueness in case of race condition
        while True:
            candidate = f"{prefix}{next_num:04d}"
            if not BMR.objects.filter(bmr_number=candidate).exists():
                return candidate
            next_num += 1
    
    def update_status_based_on_phases(self):
        """Automatically update BMR status based on phase completion"""
        from workflow.models import BatchPhaseExecution
        
        # Get phase statistics
        total_phases = BatchPhaseExecution.objects.filter(bmr=self).count()
        if total_phases == 0:
            return  # No phases created yet
        
        completed_phases = BatchPhaseExecution.objects.filter(bmr=self, status='completed').count()
        active_phases = BatchPhaseExecution.objects.filter(
            bmr=self, 
            status__in=['pending', 'in_progress']
        ).count()
        
        old_status = self.status
        
        # Determine appropriate status
        if completed_phases == total_phases:
            # All phases completed
            self.status = 'completed'
        elif completed_phases > 0 or active_phases > 0:
            # Some phases started or in progress
            if self.status not in ['in_production', 'completed']:
                self.status = 'in_production'
        elif self.status == 'in_production' and completed_phases == 0 and active_phases == 0:
            # Was in production but no active phases - likely rolled back
            self.status = 'approved'
        
        # Save if status changed
        if old_status != self.status:
            self.save(update_fields=['status'])
            logger.info(f"BMR {self.bmr_number} status updated from '{old_status}' to '{self.status}'")

class BMRMaterial(models.Model):
    """Materials required for BMR production"""
    
    bmr = models.ForeignKey(BMR, on_delete=models.CASCADE, related_name='materials')
    material_name = models.CharField(max_length=200)
    material_code = models.CharField(max_length=50)
    required_quantity = models.DecimalField(max_digits=10, decimal_places=4)
    unit_of_measure = models.CharField(max_length=20)
    batch_lot_number = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    supplier = models.CharField(max_length=200, blank=True)
    
    # Dispensing information
    dispensed_quantity = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    dispensed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    dispensed_date = models.DateTimeField(null=True, blank=True)
    is_dispensed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.bmr.bmr_number} - {self.material_name}"

class RawMaterialRelease(models.Model):
    """Track raw material releases from Store to Dispensing Store"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Release'),
        ('released', 'Released to Dispensing'),
        ('received', 'Received by Dispensing'),
        ('cancelled', 'Cancelled'),
    ]
    
    bmr = models.ForeignKey(BMR, on_delete=models.CASCADE, related_name='material_releases')
    release_number = models.CharField(max_length=20, unique=True)
    
    # Release details
    release_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Personnel
    released_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='released_materials'
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_materials'
    )
    
    # Dates
    release_started_date = models.DateTimeField(null=True, blank=True)
    release_completed_date = models.DateTimeField(null=True, blank=True)
    received_date = models.DateTimeField(null=True, blank=True)
    
    # Comments
    release_comments = models.TextField(blank=True)
    receiving_comments = models.TextField(blank=True)
    
    def __str__(self):
        return f"Release-{self.release_number} for {self.bmr.batch_number}"
    
    def save(self, *args, **kwargs):
        if not self.release_number:
            self.release_number = self.generate_release_number()
        super().save(*args, **kwargs)
    
    def generate_release_number(self):
        """Generate unique release number"""
        from django.db.models import Max
        from datetime import datetime
        year = datetime.now().year
        prefix = f"REL{year}"
        max_release = RawMaterialRelease.objects.filter(release_number__startswith=prefix).aggregate(Max('release_number'))['release_number__max']
        if max_release:
            try:
                last_num = int(max_release.replace(prefix, ""))
            except Exception:
                last_num = 0
            next_num = last_num + 1
        else:
            next_num = 1
        while True:
            candidate = f"{prefix}{next_num:04d}"
            if not RawMaterialRelease.objects.filter(release_number=candidate).exists():
                return candidate
            next_num += 1
    
    class Meta:
        ordering = ['-release_date']

class RawMaterialReleaseItem(models.Model):
    """Individual material items in a release"""
    
    release = models.ForeignKey(RawMaterialRelease, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(BMRMaterial, on_delete=models.CASCADE)
    
    # Release quantities
    requested_quantity = models.DecimalField(max_digits=10, decimal_places=4)
    released_quantity = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    
    # Material details at time of release
    batch_lot_number = models.CharField(max_length=50)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Status
    is_released = models.BooleanField(default=False)
    release_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.release.release_number} - {self.material.material_name}"

class BMRSignature(models.Model):
    """Electronic signatures for BMR approval and sign-offs"""
    
    SIGNATURE_TYPE_CHOICES = [
        ('created', 'Created'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('dispensed', 'Materials Dispensed'),
        ('production_started', 'Production Started'),
        ('production_completed', 'Production Completed'),
        ('qc_approved', 'QC Approved'),
        ('final_approval', 'Final Approval'),
    ]
    
    bmr = models.ForeignKey(BMR, on_delete=models.CASCADE, related_name='signatures')
    signature_type = models.CharField(max_length=30, choices=SIGNATURE_TYPE_CHOICES)
    signed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    signed_date = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['bmr', 'signature_type', 'signed_by']
    

class BMRRequest(models.Model):
    """Store's request for QA to issue a BMR"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bmr_requests')
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approved_bmr_requests', null=True, blank=True)
    bmr = models.ForeignKey(BMR, on_delete=models.CASCADE, null=True, blank=True, related_name='bmr_requests')
    
    request_date = models.DateTimeField(auto_now_add=True)
    required_date = models.DateField(help_text="Date when the BMR is required")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    reason = models.TextField(help_text="Reason for requesting the BMR")
    quantity_required = models.PositiveIntegerField(help_text="Quantity required for production")
    quantity_unit = models.CharField(max_length=20, help_text="Unit of measurement for quantity (e.g., kg, tablets, etc.)")
    
    notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    approved_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"BMR Request for {self.product.product_name} - {self.get_status_display()}"
    
    class Meta:
        ordering = ['-request_date']
        verbose_name = "BMR Request"
        verbose_name_plural = "BMR Requests"

# ---------------------------------------------------------------------------
# Product-linked content models
# These store the product-specific data that is displayed in the BMR template.
# Admin staff can edit these rows per product without touching code.
# ---------------------------------------------------------------------------

class EquipmentEntry(models.Model):
    """Equipment / instrument listed in a specific manufacturing phase for a product."""

    PHASE_CHOICES = [
        ('general',           'General Equipment List (Page 5)'),
        # ── Ointment ─────────────────────────────────────────────
        ('dispensing',        'Dispensing'),
        ('mixing',            'Mixing'),
        ('tube_filling',      'Tube Filling'),
        # ── Tablet / Capsule ─────────────────────────────────────
        ('granulation_1',     'Granulation 1'),
        ('granulation_2',     'Granulation 2'),
        ('compression',       'Compression'),
        ('blending',          'Blending / Lubrication'),
        ('ipqc_lab',          'IPQC Lab'),
        ('visual_inspection', 'Visual Inspection & Sorting'),
        ('blister_packing',   'Blister Packing'),
        ('strip_packing',     'Strip Packing'),
        # ── Capsule ──────────────────────────────────────────────
        ('capsule_filling',   'Capsule Filling'),
        ('inspection',        'Inspection & Sorting'),
        ('packaging',         'Packaging / Blistering'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='equipment_entries',
    )
    phase = models.CharField(max_length=40, choices=PHASE_CHOICES, db_index=True)
    equipment_name = models.CharField(max_length=120)
    equipment_id = models.CharField(
        max_length=30,
        blank=True,
        default='—',
        help_text='Equipment ID / mark number (e.g. PN-06)',
    )
    order = models.PositiveIntegerField(default=0, help_text='Display order within the phase')

    class Meta:
        ordering = ['phase', 'order']
        verbose_name = 'Equipment Entry'
        verbose_name_plural = 'Equipment Entries'

    def __str__(self):
        return f'{self.equipment_name} ({self.equipment_id})'


class YieldReconciliationRow(models.Model):
    """A single labelled row in a yield-reconciliation table for a specific phase."""

    PHASE_CHOICES = [
        ('blending',        'Blending / Lubrication'),
        ('capsule_filling', 'Capsule Filling'),
        ('blistering',      'Blistering / Primary Packaging'),
        ('inspection',      'Inspection & Sorting'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='yield_rows',
    )
    phase = models.CharField(max_length=40, choices=PHASE_CHOICES, db_index=True)
    row_key = models.CharField(
        max_length=5,
        help_text='Short letter key shown in the "Steps" column (e.g. A, B, F.)',
    )
    label = models.CharField(max_length=255, help_text='Description shown in the "Descriptions" column')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['phase', 'order']
        verbose_name = 'Yield Reconciliation Row'
        verbose_name_plural = 'Yield Reconciliation Rows'

    def __str__(self):
        return f'[{self.row_key}] {self.label}'


class WeightRangeLimit(models.Model):
    """One row in the in-process weight-range / tolerance table for a capsule or tablet phase."""

    PHASE_CHOICES = [
        ('capsule_filling', 'Capsule Filling'),
        ('compression',     'Tablet Compression'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='weight_range_limits',
    )
    phase = models.CharField(max_length=40, choices=PHASE_CHOICES, default='capsule_filling')
    category = models.CharField(max_length=30, help_text='Category label, e.g. ">105%"')
    percent_of_target = models.CharField(max_length=30, help_text='Percentage value, e.g. ">105%"')
    tolerance_code = models.CharField(max_length=20, help_text='Code shown in Tolerance column, e.g. ">+T2"')
    action = models.CharField(max_length=30, help_text='Action text, e.g. "Action", "Alert", "Good"')
    is_highlighted = models.BooleanField(
        default=False,
        help_text='Tick for the target/nominal row (rendered with green background)',
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['phase', 'order']
        verbose_name = 'Weight Range Limit'
        verbose_name_plural = 'Weight Range Limits'

    def __str__(self):
        return f'{self.product} – {self.phase}: {self.category} → {self.action}'


class BMRProcedureStep(models.Model):
    """
    A numbered procedure step for a specific phase of a product's BMR.
    Supports sub-steps via step_number (e.g. '2', '2a', '2b').
    """

    PHASE_CHOICES = [
        ('blending',             'Blending / Lubrication'),
        ('capsule_filling',      'Capsule Filling'),
        ('mixing',               'Mixing'),
        ('tube_filling',         'Tube Filling'),
        ('inspection',           'Inspection & Sorting'),
        ('packaging',            'Primary Packaging'),
        ('secondary_packaging',  'Secondary Packaging'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='procedure_steps',
    )
    phase = models.CharField(max_length=40, choices=PHASE_CHOICES, db_index=True)
    step_number = models.CharField(
        max_length=10,
        help_text='Display step label: "1", "2", "2a", "Step 3" etc.',
    )
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['phase', 'order']
        verbose_name = 'BMR Procedure Step'
        verbose_name_plural = 'BMR Procedure Steps'

    def __str__(self):
        return f'Step {self.step_number}: {self.description[:60]}'