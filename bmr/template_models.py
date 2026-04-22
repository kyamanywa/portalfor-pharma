from django.db import models
from django.contrib.auth import get_user_model
import json

User = get_user_model()

class BMRTemplateSection(models.Model):
    """Individual sections within a BMR template"""
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('textarea', 'Text Area'),
        ('number', 'Number Input'),
        ('date', 'Date Input'),
        ('datetime', 'Date & Time Input'),
        ('select', 'Dropdown Select'),
        ('checkbox', 'Checkbox'),
        ('radio', 'Radio Buttons'),
        ('signature', 'Digital Signature'),
        ('table', 'Data Table'),
        ('static_text', 'Static Text/Label'),
        ('divider', 'Section Divider'),
        ('image', 'Image Upload'),
    ]
    
    SECTION_TYPES = [
        ('info', 'Information Section'),
        ('form', 'Form Section'),
        ('table', 'Table Section'),
        ('signature', 'Signature Section'),
        ('divider', 'Page Break/Divider'),
        # Dynamic engine section types
        ('line_clearance', 'Line Clearance'),
        ('process_steps', 'Process Steps'),
        ('qa_report', 'QA Report'),
        ('yield_reconciliation', 'Yield Reconciliation'),
        ('ipc_table', 'IPC Table (In-Process Control)'),
        ('coding_control', 'Coding Control / Secondary IPC'),
        ('equipment_setup', 'Equipment Setup'),
        ('material_table', 'Material Table (Store Release / Dispensing)'),
    ]

    template = models.ForeignKey('bmr.BMRTemplate', on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    section_type = models.CharField(max_length=25, choices=SECTION_TYPES, default='info')
    phase_name = models.CharField(
        max_length=50,
        blank=True,
        default='',
        db_index=True,
        help_text="Workflow phase this section belongs to (e.g. mixing, tube_filling, blister_packing)"
    )
    order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)
    page_number = models.PositiveIntegerField(default=1, help_text="Which page this section appears on")
    
    # Layout settings
    columns = models.PositiveIntegerField(default=1, help_text="Number of columns (1-4)")
    width_class = models.CharField(max_length=20, default='col-12', help_text="Bootstrap column class")
    
    # JSON blob for section-level config (step instructions, IPC intervals, etc.)
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Section-specific config: step instructions, IPC row count, etc."
    )

    class Meta:
        ordering = ['page_number', 'order']
        verbose_name = 'BMR Template Section'
        verbose_name_plural = 'BMR Template Sections'

    def __str__(self):
        phase = f" [{self.phase_name}]" if self.phase_name else ""
        return f"Page {self.page_number}{phase}: {self.title}"

class BMRTemplateField(models.Model):
    """Individual fields within a BMR template section"""
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('textarea', 'Text Area'),
        ('number', 'Number Input'),
        ('decimal', 'Decimal Number'),
        ('date', 'Date Input'),
        ('datetime', 'Date & Time Input'),
        ('time', 'Time Input'),
        ('select', 'Dropdown Select'),
        ('checkbox', 'Checkbox'), 
        ('radio', 'Radio Buttons'),
        ('signature', 'Digital Signature'),
        ('static_text', 'Static Text/Label'),
        ('image', 'Image Upload'),
        ('calculated', 'Calculated Field'),
    ]
    
    DATA_SOURCES = [
        ('manual', 'Manual Entry'),
        ('bmr.bmr_number', 'BMR Number'),
        ('bmr.batch_number', 'Batch Number'),
        ('bmr.product.product_name', 'Product Name'),
        ('bmr.product.generic_name', 'Generic Name'),
        ('bmr.batch_size', 'Batch Size'),
        ('bmr.manufacturing_date', 'Manufacturing Date'),
        ('bmr.created_date', 'Created Date'),
        ('bmr.status', 'BMR Status'),
        ('bmr.created_by.get_full_name', 'Created By'),
        ('bmr.approved_by.get_full_name', 'Approved By'),
        ('ingredient_table', 'Ingredient Table Data'),
        ('ingredient_table_totals_rows', 'Ingredient Totals Rows'),
        ('signature_rows', 'Signature Rows'),
        ('workflow_status', 'Workflow Status'),
        ('signatures', 'Electronic Signatures'),
        ('current_user.get_full_name', 'Current User Name'),
        ('current_date', 'Current Date'),
        ('current_time', 'Current Time'),
    ]
    
    section = models.ForeignKey(BMRTemplateSection, on_delete=models.CASCADE, related_name='fields')
    label = models.CharField(max_length=200)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='text')
    data_source = models.CharField(max_length=100, choices=DATA_SOURCES, default='manual')
    order = models.PositiveIntegerField(default=0)
    
    # Field properties
    is_required = models.BooleanField(default=False)
    is_readonly = models.BooleanField(default=False)
    placeholder = models.CharField(max_length=200, blank=True)
    help_text = models.TextField(blank=True)
    default_value = models.TextField(blank=True)
    
    # Validation
    min_length = models.PositiveIntegerField(null=True, blank=True)
    max_length = models.PositiveIntegerField(null=True, blank=True)
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    regex_pattern = models.CharField(max_length=500, blank=True, help_text="Regular expression for validation")
    
    # Options for select/radio fields (JSON)
    field_options = models.JSONField(default=list, blank=True, help_text="Options for select/radio fields as JSON array")
    
    # Layout
    width_class = models.CharField(max_length=20, default='col-12')
    css_classes = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['section', 'order']
        verbose_name = 'BMR Template Field'
        verbose_name_plural = 'BMR Template Fields'
    
    def __str__(self):
        return f"{self.section.title}: {self.label}"

class BMRTemplateTable(models.Model):
    """Table definitions within BMR templates"""
    section = models.ForeignKey(BMRTemplateSection, on_delete=models.CASCADE, related_name='tables')
    title = models.CharField(max_length=200)
    data_source = models.CharField(max_length=100, help_text="Source of table data (e.g. ingredient_table)")
    is_editable = models.BooleanField(default=False, help_text="Can users add/edit rows?")
    show_row_numbers = models.BooleanField(default=True)
    max_rows = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum allowed rows")
    
    class Meta:
        verbose_name = 'BMR Template Table'
        verbose_name_plural = 'BMR Template Tables'
    
    def __str__(self):
        return f"{self.section.title}: {self.title}"

class BMRTemplateTableColumn(models.Model):
    """Column definitions for BMR template tables"""
    table = models.ForeignKey(BMRTemplateTable, on_delete=models.CASCADE, related_name='columns')
    header = models.CharField(max_length=200)
    field_type = models.CharField(max_length=20, choices=BMRTemplateField.FIELD_TYPES, default='text')
    data_source = models.CharField(max_length=100, blank=True, help_text="Row field to display (e.g. 'description', 'total_batch_quantity')")
    order = models.PositiveIntegerField(default=0)
    width_percentage = models.PositiveIntegerField(default=10, help_text="Column width as percentage")
    is_sortable = models.BooleanField(default=False)
    is_editable = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['table', 'order']
        verbose_name = 'Table Column'
        verbose_name_plural = 'Table Columns'
    
    def __str__(self):
        return f"{self.table.title}: {self.header}"

class BMRFormData(models.Model):
    """Store form data entered by operators for each BMR"""
    bmr = models.ForeignKey('bmr.BMR', on_delete=models.CASCADE, related_name='form_data')
    section = models.ForeignKey(BMRTemplateSection, on_delete=models.CASCADE)
    field = models.ForeignKey(BMRTemplateField, on_delete=models.CASCADE)
    value = models.TextField(blank=True)
    file_value = models.FileField(upload_to='bmr_uploads/', null=True, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='bmr_form_entries')
    
    class Meta:
        unique_together = ['bmr', 'section', 'field']
        verbose_name = 'BMR Form Data'
        verbose_name_plural = 'BMR Form Data'
    
    def __str__(self):
        return f"{self.bmr.bmr_number}: {self.field.label} = {self.value[:50]}"