from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import (
    ProductionPhase, BatchPhaseExecution, Machine, 
    PhaseTimingSetting, PhaseOverrunNotification, PhaseTimeOverrunNotification,
    WorkflowTemplate, WorkflowTemplatePhase, ProductMachineTimingSetting, SystemTimingSettings
)

# Import the enhanced admin settings
from .admin_settings import *

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ['name', 'machine_type', 'is_active', 'created_date']
    list_filter = ['machine_type', 'is_active', 'created_date']
    search_fields = ['name']
    ordering = ['machine_type', 'name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'machine_type', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_date',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_date']

class ProductionPhaseAdminForm(forms.ModelForm):
    """Custom form for ProductionPhase with validation"""
    
    class Meta:
        model = ProductionPhase
        fields = '__all__'
        help_texts = {
            'phase_order': 'Order in which this phase executes (1-based). Lower numbers execute first.',
            'is_mandatory': 'Unchecked phases can be skipped in certain conditions.',
            'requires_approval': 'Phases requiring QA/QC approval before proceeding.',
            'can_rollback_to': 'Phase to rollback to if this phase fails QC.',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        product_type = cleaned_data.get('product_type')
        phase_order = cleaned_data.get('phase_order')
        phase_name = cleaned_data.get('phase_name')
        
        if product_type and phase_order:
            # Check for duplicate phase orders within the same product type
            existing_phases = ProductionPhase.objects.filter(
                product_type=product_type,
                phase_order=phase_order
            )
            if self.instance.pk:
                existing_phases = existing_phases.exclude(pk=self.instance.pk)
            
            if existing_phases.exists():
                raise ValidationError({
                    'phase_order': f'Phase order {phase_order} already exists for {product_type} product type. '
                                  f'Existing phase: {existing_phases.first().phase_name}'
                })
        
        # Validate rollback target exists and has lower order
        rollback_to = cleaned_data.get('can_rollback_to')
        if rollback_to and product_type and phase_order:
            if rollback_to.product_type != product_type:
                raise ValidationError({
                    'can_rollback_to': 'Rollback target must be from the same product type.'
                })
            
            if rollback_to.phase_order >= phase_order:
                raise ValidationError({
                    'can_rollback_to': 'Rollback target must have a lower phase order than current phase.'
                })
        
        return cleaned_data

@admin.register(ProductionPhase)
class ProductionPhaseAdmin(admin.ModelAdmin):
    form = ProductionPhaseAdminForm
    list_display = [
        'phase_name', 'product_type', 'phase_order', 'is_mandatory', 
        'requires_approval', 'get_rollback_target', 'estimated_duration_hours'
    ]
    list_filter = ['product_type', 'is_mandatory', 'requires_approval']
    search_fields = ['phase_name', 'description']
    ordering = ['product_type', 'phase_order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('product_type', 'phase_name', 'description')
        }),
        ('Workflow Configuration', {
            'fields': ('phase_order', 'is_mandatory', 'requires_approval'),
            'description': 'Configure how this phase fits into the workflow'
        }),
        ('Quality Control', {
            'fields': ('can_rollback_to',),
            'description': 'Configure rollback behavior for failed QC'
        }),
        ('Timing', {
            'fields': ('estimated_duration_hours',),
            'description': 'Expected duration for planning and overrun detection'
        }),
    )
    
    def get_rollback_target(self, obj):
        """Display rollback target with order"""
        if obj.can_rollback_to:
            return format_html(
                '<span style="color: #e74c3c;">→ {} (Order: {})</span>',
                obj.can_rollback_to.phase_name,
                obj.can_rollback_to.phase_order
            )
        return format_html('<span style="color: #95a5a6;">No rollback</span>')
    get_rollback_target.short_description = 'Rollback Target'
    get_rollback_target.admin_order_field = 'can_rollback_to__phase_order'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('can_rollback_to')
    
    actions = ['reorder_phases', 'validate_workflow']
    
    def reorder_phases(self, request, queryset):
        """Action to reorder selected phases"""
        if not queryset.exists():
            self.message_user(request, "No phases selected.", level='warning')
            return
        
        product_types = queryset.values_list('product_type', flat=True).distinct()
        if len(product_types) > 1:
            self.message_user(
                request, 
                "Cannot reorder phases from different product types. Please select phases from one product type only.",
                level='error'
            )
            return
        
        # Auto-reorder phases for the product type
        product_type = product_types[0]
        phases = ProductionPhase.objects.filter(product_type=product_type).order_by('phase_order', 'phase_name')
        
        for index, phase in enumerate(phases, 1):
            phase.phase_order = index
            phase.save(update_fields=['phase_order'])
        
        self.message_user(
            request, 
            f"Reordered {phases.count()} phases for {product_type} product type. New orders: 1-{phases.count()}",
            level='success'
        )
    reorder_phases.short_description = "Auto-reorder selected phases (1, 2, 3...)"
    
    def validate_workflow(self, request, queryset):
        """Validate workflow integrity"""
        issues = []
        
        for product_type in queryset.values_list('product_type', flat=True).distinct():
            phases = ProductionPhase.objects.filter(product_type=product_type).order_by('phase_order')
            
            # Check for gaps in ordering
            expected_order = 1
            for phase in phases:
                if phase.phase_order != expected_order:
                    issues.append(f"{product_type}: Gap in ordering at {phase.phase_name} (expected {expected_order}, got {phase.phase_order})")
                expected_order = phase.phase_order + 1
            
            # Check for mandatory workflow phases
            required_phases = ['bmr_creation', 'regulatory_approval', 'final_qa', 'finished_goods_store']
            existing_phase_names = phases.values_list('phase_name', flat=True)
            
            for required in required_phases:
                if required not in existing_phase_names:
                    issues.append(f"{product_type}: Missing required phase '{required}'")
        
        if issues:
            self.message_user(request, f"Workflow issues found: {'; '.join(issues)}", level='warning')
        else:
            self.message_user(request, "All workflows are valid!", level='success')
    validate_workflow.short_description = "Validate workflow integrity"


# ============ WORKFLOW TEMPLATE MANAGEMENT ============

class WorkflowTemplatePhaseInline(admin.TabularInline):
    model = WorkflowTemplatePhase
    extra = 1
    fields = ['phase_order', 'phase_name', 'description', 'is_mandatory', 'requires_approval', 
             'estimated_duration_hours', 'rollback_target_order']
    ordering = ['phase_order']


@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'product_type', 'get_phase_count', 'is_active', 'is_default', 'updated_at'
    ]
    list_filter = ['product_type', 'is_active', 'is_default', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['product_type', 'name']
    inlines = [WorkflowTemplatePhaseInline]
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'product_type', 'description')
        }),
        ('Template Settings', {
            'fields': ('is_active', 'is_default'),
            'description': 'Configure how this template is used in the system'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['apply_templates', 'copy_from_current', 'activate_templates', 'set_as_default']
    
    def get_phase_count(self, obj):
        count = obj.get_phase_count()
        if count == 0:
            return format_html('<span style="color: #e74c3c;">0 phases</span>')
        return format_html('<span style="color: #27ae60;">{} phases</span>', count)
    get_phase_count.short_description = 'Phases'
    
    def apply_templates(self, request, queryset):
        """Apply selected templates to production phases"""
        applied = 0
        errors = []
        
        for template in queryset:
            try:
                if not template.is_active:
                    errors.append(f"Template '{template.name}' is inactive")
                    continue
                
                phase_count = template.apply_to_production_phases()
                applied += 1
                messages.success(
                    request, 
                    f"Applied template '{template.name}' - created {phase_count} phases for {template.product_type}"
                )
            except Exception as e:
                errors.append(f"Error applying '{template.name}': {str(e)}")
        
        if errors:
            messages.warning(request, f"Some templates failed: {'; '.join(errors)}")
        
        if applied > 0:
            messages.success(request, f"Successfully applied {applied} templates")
    apply_templates.short_description = "Apply selected templates to production workflow"
    
    def copy_from_current(self, request, queryset):
        """Copy current production phases to selected templates"""
        copied = 0
        
        for template in queryset:
            try:
                phase_count = template.copy_phases_from_current()
                copied += 1
                messages.success(
                    request,
                    f"Copied {phase_count} current phases to template '{template.name}'"
                )
            except Exception as e:
                messages.error(request, f"Error copying to '{template.name}': {str(e)}")
        
        if copied > 0:
            messages.success(request, f"Successfully updated {copied} templates")
    copy_from_current.short_description = "Copy current production phases to templates"
    
    def activate_templates(self, request, queryset):
        """Activate selected templates"""
        count = queryset.update(is_active=True)
        messages.success(request, f"Activated {count} templates")
    activate_templates.short_description = "Activate selected templates"
    
    def set_as_default(self, request, queryset):
        """Set selected templates as default for their product types"""
        updated = 0
        errors = []
        
        for template in queryset:
            try:
                # Clear other defaults for this product type
                WorkflowTemplate.objects.filter(
                    product_type=template.product_type
                ).update(is_default=False)
                
                # Set this as default
                template.is_default = True
                template.save()
                updated += 1
                messages.success(
                    request,
                    f"Set '{template.name}' as default template for {template.product_type}"
                )
            except Exception as e:
                errors.append(f"Error with '{template.name}': {str(e)}")
        
        if errors:
            messages.warning(request, f"Some updates failed: {'; '.join(errors)}")
    set_as_default.short_description = "Set as default template for product type"


@admin.register(WorkflowTemplatePhase)
class WorkflowTemplatePhaseAdmin(admin.ModelAdmin):
    list_display = [
        'template', 'phase_order', 'phase_name', 'is_mandatory', 
        'requires_approval', 'estimated_duration_hours', 'get_rollback_display'
    ]
    list_filter = ['template__product_type', 'is_mandatory', 'requires_approval']
    search_fields = ['template__name', 'phase_name', 'description']
    ordering = ['template__product_type', 'template__name', 'phase_order']
    
    fieldsets = (
        ('Phase Information', {
            'fields': ('template', 'phase_name', 'phase_order', 'description')
        }),
        ('Phase Configuration', {
            'fields': ('is_mandatory', 'requires_approval', 'estimated_duration_hours')
        }),
        ('Quality Control', {
            'fields': ('rollback_target_order',),
            'description': 'Phase order to rollback to if this phase fails QC'
        }),
    )
    
    def get_rollback_display(self, obj):
        if obj.rollback_target_order:
            return format_html(
                '<span style="color: #e74c3c;">→ Order {}</span>',
                obj.rollback_target_order
            )
        return format_html('<span style="color: #95a5a6;">No rollback</span>')
    get_rollback_display.short_description = 'Rollback Target'


# ============ ENHANCED PRODUCTION PHASE ADMIN ============

@admin.register(BatchPhaseExecution)
class BatchPhaseExecutionAdmin(admin.ModelAdmin):
    list_display = ['bmr', 'phase', 'status', 'machine_used', 'started_by', 'completed_by', 'started_date', 'completed_date']
    list_filter = ['status', 'phase__product_type', 'phase__phase_name', 'machine_used', 'breakdown_occurred', 'changeover_occurred', 'started_date', 'completed_date']
    search_fields = ['bmr__batch_number', 'phase__phase_name', 'operator_comments', 'machine_used__name']
    readonly_fields = ['created_date']
    ordering = ['-started_date']
    
    fieldsets = (
        (None, {
            'fields': ('bmr', 'phase', 'status', 'machine_used')
        }),
        ('Execution Details', {
            'fields': ('started_by', 'completed_by', 'started_date', 'completed_date', 'created_date')
        }),
        ('Comments', {
            'fields': ('operator_comments', 'qa_comments')
        }),
        ('Breakdown Information', {
            'fields': ('breakdown_occurred', 'breakdown_start_time', 'breakdown_end_time'),
            'classes': ('collapse',)
        }),
        ('Changeover Information', {
            'fields': ('changeover_occurred', 'changeover_start_time', 'changeover_end_time'),
            'classes': ('collapse',)
        }),
        ('Quality Control', {
            'fields': ('qc_approved', 'qc_approved_by', 'qc_approval_date', 'rejection_reason'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('bmr', 'phase', 'started_by', 'completed_by', 'machine_used')


@admin.register(PhaseTimingSetting)
class PhaseTimingSettingAdmin(admin.ModelAdmin):
    list_display = ['phase', 'expected_duration_hours', 'warning_threshold_percent', 'created_by', 'updated_at']
    list_filter = ['phase__product_type', 'phase__phase_name', 'created_at']
    search_fields = ['phase__phase_name', 'phase__product_type']
    ordering = ['phase__product_type', 'phase__phase_name']
    
    fieldsets = (
        (None, {
            'fields': ('phase', 'expected_duration_hours', 'warning_threshold_percent')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PhaseOverrunNotification)
class PhaseOverrunNotificationAdmin(admin.ModelAdmin):
    list_display = ['phase_execution', 'status', 'expected_duration', 'actual_duration', 'created_at']
    list_filter = ['status', 'created_at', 'response_time']
    search_fields = ['phase_execution__bmr__batch_number', 'phase_execution__phase__phase_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Phase Information', {
            'fields': ('phase_execution', 'expected_duration', 'actual_duration')
        }),
        ('Notification Status', {
            'fields': ('status', 'created_at')
        }),
        ('Operator Response', {
            'fields': ('operator_response', 'response_time'),
            'classes': ('collapse',)
        }),
        ('Admin Review', {
            'fields': ('admin_comments', 'admin_review_time'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PhaseTimeOverrunNotification)
class PhaseTimeOverrunNotificationAdmin(admin.ModelAdmin):
    list_display = ['phase_execution', 'threshold_exceeded_percent', 'acknowledged', 'notification_time']
    list_filter = ['acknowledged', 'threshold_exceeded_percent', 'notification_time']
    search_fields = ['phase_execution__bmr__batch_number', 'phase_execution__phase__phase_name']
    ordering = ['-notification_time']
    readonly_fields = ['notification_time']


@admin.register(ProductMachineTimingSetting)
class ProductMachineTimingSettingAdmin(admin.ModelAdmin):
    """Admin interface for Product-Machine timing settings"""
    
    list_display = [
        'product', 'machine', 'phase', 'expected_duration_hours', 
        'timing_type', 'warning_threshold_percent', 'is_active', 'created_at'
    ]
    list_filter = [
        'is_active', 'phase__product_type', 'machine__machine_type', 
        'warning_threshold_percent', 'created_at'
    ]
    search_fields = [
        'product__product_name', 'machine__name', 'phase__phase_name', 'notes'
    ]
    ordering = ['product__product_name', 'phase__phase_name', 'machine__name']
    
    fieldsets = (
        ('Configuration', {
            'fields': ('product', 'machine', 'phase', 'is_active')
        }),
        ('Timing Settings', {
            'fields': ('expected_duration_hours', 'warning_threshold_percent')
        }),
        ('Notes & Comments', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['product', 'machine', 'phase']
    
    def save_model(self, request, obj, form, change):
        """Set the created_by field when saving"""
        if not change:  # New object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'product', 'machine', 'phase', 'created_by'
        )
    
    # Custom admin actions
    actions = ['activate_timing_settings', 'deactivate_timing_settings', 'duplicate_timing_settings']
    
    def activate_timing_settings(self, request, queryset):
        """Activate selected timing settings"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} timing settings activated.')
    activate_timing_settings.short_description = "Activate selected timing settings"
    
    def deactivate_timing_settings(self, request, queryset):
        """Deactivate selected timing settings"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} timing settings deactivated.')
    deactivate_timing_settings.short_description = "Deactivate selected timing settings"
    
    def duplicate_timing_settings(self, request, queryset):
        """Duplicate selected timing settings for easy copying"""
        for obj in queryset:
            obj.pk = None  # Create new object
            obj.is_active = False  # Start as inactive
            obj.notes = f"Duplicated from ID {obj.id} - {obj.notes}"
            obj.created_by = request.user
            obj.save()
        self.message_user(request, f'{queryset.count()} timing settings duplicated (set as inactive).')
    duplicate_timing_settings.short_description = "Duplicate selected timing settings"
    
    # Custom list display methods
    def timing_type(self, obj):
        """Show timing type in list view"""
        return obj.timing_type
    timing_type.short_description = 'Timing Type'


@admin.register(SystemTimingSettings)
class SystemTimingSettingsAdmin(admin.ModelAdmin):
    """Enhanced admin interface for system-wide timing settings"""
    
    list_display = [
        'setting_name', 'setting_value', 'unit', 'description_short', 
        'created_date', 'modified_date'
    ]
    list_filter = ['unit', 'created_date', 'modified_date']
    search_fields = ['setting_name', 'description']
    ordering = ['setting_name']
    
    fieldsets = (
        ('Setting Configuration', {
            'fields': ('setting_name', 'setting_value', 'unit'),
            'description': 'Configure the setting name, value, and unit of measurement.'
        }),
        ('Documentation', {
            'fields': ('description',),
            'description': 'Detailed description of what this setting controls.'
        }),
        ('Metadata', {
            'fields': ('created_date', 'modified_date'),
            'classes': ('collapse',),
            'description': 'Automatic timestamps for auditing.'
        }),
    )
    
    readonly_fields = ['created_date', 'modified_date']
    
    # Custom actions
    actions = ['reset_to_defaults', 'export_settings', 'validate_settings']
    
    def reset_to_defaults(self, request, queryset):
        """Reset selected settings to their default values"""
        default_values = {
            'default_machine_phase_duration_hours': 4.0,
            'default_non_machine_phase_duration_hours': 0.17,
            'system_error_fallback_hours': 8.0,
            'default_warning_threshold_percent': 20,
            'warning_threshold_percentage': 80.0,
            'overrun_threshold_percentage': 120.0,
            'warning_time_minutes': 30.0,
            'critical_overrun_percentage': 150.0,
            'urgent_sample_hours': 24.0,
            'session_timeout_hours': 8.0,
            'max_breakdown_duration_hours': 4.0,
            'max_changeover_duration_hours': 2.0,
            'dashboard_refresh_seconds': 30,
            'audit_trail_retention_days': 2555,
        }
        
        reset_count = 0
        for setting in queryset:
            if setting.setting_name in default_values:
                setting.setting_value = default_values[setting.setting_name]
                setting.save()
                reset_count += 1
        
        self.message_user(
            request, 
            f'{reset_count} settings reset to default values.',
            messages.SUCCESS
        )
    reset_to_defaults.short_description = "Reset to default values"
    
    def export_settings(self, request, queryset):
        """Export selected settings for backup"""
        from django.http import JsonResponse
        import json
        
        settings_data = []
        for setting in queryset:
            settings_data.append({
                'setting_name': setting.setting_name,
                'setting_value': float(setting.setting_value),
                'description': setting.description,
                'unit': setting.unit
            })
        
        response = JsonResponse({'settings': settings_data}, indent=2)
        response['Content-Disposition'] = 'attachment; filename="system_settings_export.json"'
        return response
    export_settings.short_description = "Export settings as JSON"
    
    def validate_settings(self, request, queryset):
        """Validate that settings have reasonable values"""
        warnings = []
        errors = []
        
        for setting in queryset:
            value = float(setting.setting_value)
            name = setting.setting_name
            
            # Validation rules
            if 'hours' in name and (value < 0 or value > 168):  # 0-168 hours (1 week)
                warnings.append(f'{name}: {value} hours seems unusually high/low')
            elif 'minutes' in name and (value < 0 or value > 1440):  # 0-1440 minutes (24 hours)
                warnings.append(f'{name}: {value} minutes seems unusually high/low')
            elif 'percentage' in name and (value < 0 or value > 500):  # 0-500%
                errors.append(f'{name}: {value}% is outside reasonable range (0-500%)')
            elif 'threshold' in name and value < 0:
                errors.append(f'{name}: Threshold cannot be negative')
            elif 'duration' in name and value <= 0:
                errors.append(f'{name}: Duration must be positive')
        
        if errors:
            self.message_user(request, f'Errors found: {"; ".join(errors)}', messages.ERROR)
        elif warnings:
            self.message_user(request, f'Warnings: {"; ".join(warnings)}', messages.WARNING)
        else:
            self.message_user(request, 'All selected settings validated successfully.', messages.SUCCESS)
    validate_settings.short_description = "Validate setting values"
    
    # Custom list display methods
    def description_short(self, obj):
        """Show truncated description"""
        if len(obj.description) > 60:
            return obj.description[:57] + "..."
        return obj.description
    description_short.short_description = 'Description'
    
    # Enhanced form
    class Media:
        css = {
            'all': ('admin/css/timing_settings.css',)
        }
        js = ('admin/js/timing_settings.js',)
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form based on setting type"""
        form = super().get_form(request, obj, **kwargs)
        
        # Add help text based on setting name
        if obj and 'hours' in obj.setting_name:
            form.base_fields['setting_value'].help_text = "Value in hours (decimal allowed, e.g., 0.17 = 10 minutes)"
        elif obj and 'minutes' in obj.setting_name:
            form.base_fields['setting_value'].help_text = "Value in minutes (whole numbers)"
        elif obj and 'percentage' in obj.setting_name:
            form.base_fields['setting_value'].help_text = "Percentage value (e.g., 20 = 20%)"
        
        return form
