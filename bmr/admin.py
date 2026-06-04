from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html
from .models import (
    BMR, BMRMaterial, BMRSignature, BMRRequest, BMRTemplate,
    EquipmentEntry, YieldReconciliationRow, WeightRangeLimit, BMRProcedureStep,
    BMRIssuanceLog, BMRIssuanceLogEntry,
)
from .template_admin import BMRTemplateVisualAdmin

@admin.register(BMR)
class BMRAdmin(admin.ModelAdmin):
    list_display = [
        'bmr_number', 'batch_number', 'product', 'status', 
        'created_by', 'created_date', 'get_batch_size'
    ]
    list_filter = ['status', 'product__product_type', 'created_date']
    search_fields = ['bmr_number', 'batch_number', 'product__product_name']
    readonly_fields = ['bmr_number', 'created_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('product', 'batch_number', 'bmr_number', 'actual_batch_size', 'actual_batch_size_unit'),
            'description': 'Enter batch number manually in format XXXYYYY (e.g., 0012025)'
        }),
        ('Dates', {
            'fields': ('created_date', 'planned_start_date', 'planned_completion_date', 
                      'actual_start_date', 'actual_completion_date')
        }),
        ('Status & Approval', {
            'fields': ('status', 'created_by', 'approved_by', 'approved_date')
        }),
        ('Template', {
            'fields': ('template',),
            'description': 'Select the template structure that should render this BMR'
        }),
        ('Instructions', {
            'fields': ('manufacturing_instructions', 'special_instructions', 
                      'in_process_controls', 'quality_checks_required')
        }),
        ('Comments', {
            'fields': ('qa_comments', 'regulatory_comments')
        }),
    )
    
    def get_batch_size(self, obj):
        return f"{obj.batch_size} {obj.batch_size_unit}"
    get_batch_size.short_description = "Batch Size"

@admin.register(BMRMaterial)
class BMRMaterialAdmin(admin.ModelAdmin):
    list_display = [
        'bmr', 'material_name', 'material_code', 'required_quantity', 
        'unit_of_measure', 'is_dispensed'
    ]
    list_filter = ['is_dispensed', 'unit_of_measure']
    search_fields = ['material_name', 'material_code', 'bmr__batch_number']

@admin.register(BMRSignature)
class BMRSignatureAdmin(admin.ModelAdmin):
    list_display = ['bmr', 'signature_type', 'signed_by', 'signed_date']
    list_filter = ['signature_type', 'signed_date']
    search_fields = ['bmr__batch_number', 'signed_by__username']

@admin.register(BMRRequest)
class BMRRequestAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'requested_by', 'request_date', 'required_date', 
        'status', 'priority', 'approved_by'
    ]
    list_filter = ['status', 'priority', 'request_date', 'required_date']
    search_fields = ['product__product_name', 'requested_by__username', 'reason']
    readonly_fields = ['request_date']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('product', 'requested_by', 'request_date', 'required_date', 'quantity_required', 'quantity_unit')
        }),
        ('Request Details', {
            'fields': ('priority', 'reason', 'status')
        }),
        ('Approval Information', {
            'fields': ('approved_by', 'bmr')
        }),
    )


@admin.register(BMRTemplate)
class BMRTemplateAdmin(BMRTemplateVisualAdmin):
    """BMR Template admin with visual editor - inherits from BMRTemplateVisualAdmin"""
    pass


# ---------------------------------------------------------------------------
# Product-linked content models
# ---------------------------------------------------------------------------

@admin.register(EquipmentEntry)
class EquipmentEntryAdmin(admin.ModelAdmin):
    list_display = ['product', 'phase', 'order', 'equipment_name', 'equipment_id']
    list_filter = ['product', 'phase']
    list_editable = ['order', 'equipment_name', 'equipment_id']
    ordering = ['product', 'phase', 'order']
    search_fields = ['product__product_name', 'equipment_name', 'equipment_id']


@admin.register(YieldReconciliationRow)
class YieldReconciliationRowAdmin(admin.ModelAdmin):
    list_display = ['product', 'phase', 'row_key', 'label', 'order']
    list_filter = ['product', 'phase']
    list_editable = ['order', 'row_key', 'label']
    ordering = ['product', 'phase', 'order']
    search_fields = ['product__product_name', 'label']


@admin.register(WeightRangeLimit)
class WeightRangeLimitAdmin(admin.ModelAdmin):
    list_display = ['product', 'phase', 'order', 'category', 'percent_of_target', 'tolerance_code', 'action', 'is_highlighted']
    list_filter = ['product', 'phase']
    list_editable = ['order', 'category', 'percent_of_target', 'tolerance_code', 'action', 'is_highlighted']
    ordering = ['product', 'phase', 'order']
    search_fields = ['product__product_name', 'category', 'action']


@admin.register(BMRProcedureStep)
class BMRProcedureStepAdmin(admin.ModelAdmin):
    list_display = ['product', 'phase', 'step_number', 'order', 'description_preview']
    list_filter = ['product', 'phase']
    list_editable = ['step_number', 'order']
    ordering = ['product', 'phase', 'order']
    search_fields = ['product__product_name', 'step_number', 'description']

    def description_preview(self, obj):
        return obj.description[:80] + '…' if len(obj.description) > 80 else obj.description
    description_preview.short_description = 'Description'


@admin.register(BMRIssuanceLog)
class BMRIssuanceLogAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'sop_reference', 'total_entries', 'latest_batch', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['product__product_name', 'sop_reference']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('product', 'sop_reference')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_batch_number(self, obj):
        latest = obj.latest_batch
        return latest.batch_number if latest else 'No batches'
    get_batch_number.short_description = 'Latest Batch'


@admin.register(BMRIssuanceLogEntry)
class BMRIssuanceLogEntryAdmin(admin.ModelAdmin):
    list_display = [
        'entry_number', 'get_product_name', 'get_batch_number', 'issue_date',
        'issued_by', 'received_by', 'submitted_by', 'received_back_by', 'release_date', 'pack_size', 'created_at'
    ]
    list_filter = ['issue_date', 'release_date', 'issued_by', 'received_by', 'submitted_by', 'received_back_by']
    search_fields = ['bmr__batch_number', 'bmr__product__product_name', 'entry_number', 'remarks']
    readonly_fields = [
        'entry_number', 'issue_date', 'bmr', 'active_ingredients', 'issued_by',
        'issued_by_signature', 'issued_by_date', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('BMR Information', {
            'fields': ('issuance_log', 'entry_number', 'bmr', 'issue_date', 'active_ingredients')
        }),
        ('Issued By (QA Approval)', {
            'fields': ('issued_by', 'issued_by_signature', 'issued_by_date')
        }),
        ('Received By (Production Officer)', {
            'fields': ('received_by', 'received_by_signature', 'received_by_date')
        }),
        ('Submitted By (QA Final)', {
            'fields': ('submitted_by', 'submitted_by_signature', 'submitted_by_date')
        }),
        ('Received Back By (QA Receives Documentation)', {
            'fields': ('received_back_by', 'received_back_by_signature', 'received_back_by_date')
        }),
        ('Additional Information', {
            'fields': ('release_date', 'pack_size', 'remarks')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_batch_number(self, obj):
        return obj.bmr.batch_number
    get_batch_number.short_description = 'Batch No.'
    get_batch_number.admin_order_field = 'bmr__batch_number'
    
    def get_product_name(self, obj):
        return obj.bmr.product.product_name
    get_product_name.short_description = 'Product'
    get_product_name.admin_order_field = 'bmr__product__product_name'
