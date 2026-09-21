from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
import json
from .models import (
    DashboardMetrics, DashboardPermission, NotificationAlert, NotificationSettings,
    QMSAction, QMSApprovalRoute, QMSApprovalStep, QMSAudit, QMSCAPA,
    QMSCalibrationEvent, QMSCalibrationRecord, QMSChangeControl, QMSChangeImpactAssessment, QMSComplaintRecall,
    QMSDeviation, QMSDocument, QMSElectronicSignature, QMSFieldAuditTrail,
    QMSRecordLink,
    QMSLabInvestigation, QMSLabSpecification, QMSNotificationRule,
    QMSQualityQuery, QMSRegulatoryPackage,
    QMSReportExport, QMSRiskAssessment, QMSSamplingPlan, QMSStabilitySchedule,
    QMSStabilityResult, QMSCOA, QMSMaterialQC, QMSSupplierQualification, QMSTrainingRecord,
    QualityDefect, QualityInspectionCharacteristic, QualityInspectionLot,
    QualityResult, UserDashboardPreferences,
)

class DashboardPermissionAdminForm(forms.ModelForm):
    """Custom form for DashboardPermission admin with proper JSONField handling"""
    
    allowed_roles_text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'cols': 60, 'placeholder': '["qa", "admin", "production_manager"]'}),
        help_text='Enter roles as a JSON list. Example: ["qa", "admin", "production_manager"] or [] for no roles',
        required=False,
        label='Allowed Roles (JSON)'
    )
    
    class Meta:
        model = DashboardPermission
        exclude = ['allowed_roles']  # Exclude the actual JSONField, use allowed_roles_text instead
    
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
        
        # Save the instance first
        instance = super().save(commit=commit)
        
        return instance
    
    def save_m2m(self):
        """Save many-to-many relationships (required for Django Admin)"""
        # Call the parent's save_m2m to properly save allowed_users and blocked_users
        super().save_m2m()

@admin.register(DashboardMetrics)
class DashboardMetricsAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'active_batches', 'completed_phases_today', 'pending_phases', 'rejected_phases_today']
    list_filter = ['date', 'user__role', 'user__is_active']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['date']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'date')
        }),
        ('General Metrics', {
            'fields': ('active_batches', 'completed_phases_today', 'pending_phases', 'rejected_phases_today')
        }),
        ('Role-Specific Data', {
            'fields': ('role_specific_data',),
            'classes': ('collapse',),
            'description': 'Additional metrics stored as JSON for specific roles'
        }),
    )
    
    def has_add_permission(self, request):
        # Metrics should be auto-generated, not manually added
        return False

@admin.register(NotificationAlert)
class NotificationAlertAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'title', 'is_read', 'priority', 'created_date']
    list_filter = ['notification_type', 'priority', 'is_read', 'created_date']
    search_fields = ['recipient__username', 'title', 'message']


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ['role', 'show_notification_panel', 'auto_refresh_notifications', 'notification_sound', 'max_notifications_display']
    list_filter = ['show_notification_panel', 'auto_refresh_notifications', 'notification_sound']
    search_fields = ['role']
    
    fieldsets = (
        ('Role Configuration', {
            'fields': ('role',),
            'description': 'Select the user role to configure notification settings for.'
        }),
        ('Panel Visibility', {
            'fields': ('show_notification_panel',),
            'description': 'Control whether this role can see the notification panel on their dashboard.'
        }),
        ('Notification Behavior', {
            'fields': ('auto_refresh_notifications', 'notification_sound', 'max_notifications_display'),
            'description': 'Configure how notifications behave for this role.'
        }),
    )


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


class QualityInspectionCharacteristicInline(admin.TabularInline):
    model = QualityInspectionCharacteristic
    extra = 0


class QualityResultInline(admin.TabularInline):
    model = QualityResult
    extra = 0
    readonly_fields = ('recorded_at',)


class QualityDefectInline(admin.TabularInline):
    model = QualityDefect
    extra = 0
    readonly_fields = ('created_at', 'closed_at')


@admin.register(QualityInspectionLot)
class QualityInspectionLotAdmin(admin.ModelAdmin):
    list_display = (
        'lot_number', 'bmr', 'product', 'inspection_type', 'status',
        'usage_decision', 'assigned_to', 'decision_by', 'created_at',
    )
    list_filter = ('inspection_type', 'origin', 'status', 'usage_decision', 'created_at')
    search_fields = ('lot_number', 'bmr__batch_number', 'product__product_name')
    readonly_fields = ('lot_number', 'created_at', 'updated_at', 'started_at', 'completed_at', 'decision_at')
    inlines = [QualityInspectionCharacteristicInline, QualityDefectInline]


@admin.register(QualityInspectionCharacteristic)
class QualityInspectionCharacteristicAdmin(admin.ModelAdmin):
    list_display = ('lot', 'name', 'specification', 'unit', 'required', 'order')
    list_filter = ('required', 'unit')
    search_fields = ('lot__lot_number', 'name', 'specification')
    inlines = [QualityResultInline]


@admin.register(QualityResult)
class QualityResultAdmin(admin.ModelAdmin):
    list_display = ('characteristic', 'get_lot', 'passed', 'recorded_by', 'recorded_at')
    list_filter = ('passed', 'recorded_at')
    search_fields = ('characteristic__lot__lot_number', 'characteristic__name', 'value_text')
    readonly_fields = ('recorded_at',)

    def get_lot(self, obj):
        return obj.characteristic.lot
    get_lot.short_description = 'Inspection Lot'


@admin.register(QualityDefect)
class QualityDefectAdmin(admin.ModelAdmin):
    list_display = ('lot', 'defect_type', 'severity', 'status', 'reported_by', 'created_at')
    list_filter = ('defect_type', 'severity', 'status', 'created_at')
    search_fields = ('lot__lot_number', 'lot__bmr__batch_number', 'description', 'corrective_action')
    readonly_fields = ('created_at', 'closed_at')


@admin.register(QMSAction)
class QMSActionAdmin(admin.ModelAdmin):
    list_display = ('qms_number', 'category', 'owner_role', 'priority', 'status', 'bmr', 'assigned_to', 'due_date')
    list_filter = ('category', 'owner_role', 'priority', 'status', 'created_at', 'due_date')
    search_fields = ('qms_number', 'title', 'description', 'bmr__batch_number', 'product__product_name')
    readonly_fields = ('qms_number', 'created_at', 'updated_at', 'closed_at')


@admin.register(QMSDocument)
class QMSDocumentAdmin(admin.ModelAdmin):
    list_display = ('document_number', 'document_type', 'title', 'version', 'status', 'effective_date', 'expiry_date', 'approved_by')
    list_filter = ('document_type', 'status', 'effective_date', 'expiry_date', 'created_at')
    search_fields = ('document_number', 'title', 'version', 'revision_reason')
    readonly_fields = ('document_number', 'revision_history', 'created_at', 'updated_at', 'signed_at')


@admin.register(QMSDeviation)
class QMSDeviationAdmin(admin.ModelAdmin):
    list_display = ('deviation_number', 'title', 'severity', 'status', 'qa_decision', 'bmr', 'assigned_to', 'closed_at')
    list_filter = ('severity', 'status', 'qa_decision', 'created_at', 'closed_at')
    search_fields = ('deviation_number', 'title', 'description', 'impact_assessment', 'root_cause', 'bmr__batch_number')
    readonly_fields = ('deviation_number', 'created_at', 'updated_at', 'closed_at')


@admin.register(QMSRiskAssessment)
class QMSRiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ('risk_number', 'method', 'title', 'risk_level', 'rpn', 'residual_rpn', 'status', 'owner')
    list_filter = ('method', 'risk_level', 'status', 'created_at')
    search_fields = ('risk_number', 'title', 'process_area', 'hazard', 'failure_mode', 'mitigation_plan')
    readonly_fields = ('risk_number', 'rpn', 'residual_rpn', 'created_at', 'updated_at', 'approved_at')


@admin.register(QMSAudit)
class QMSAuditAdmin(admin.ModelAdmin):
    list_display = ('audit_number', 'audit_type', 'title', 'finding_type', 'severity', 'status', 'responsible_person', 'due_date')
    list_filter = ('audit_type', 'finding_type', 'severity', 'status', 'planned_date', 'due_date')
    search_fields = ('audit_number', 'title', 'auditee', 'department', 'standard_reference', 'observation', 'corrective_action')
    readonly_fields = ('audit_number', 'created_at', 'updated_at', 'closed_at')


@admin.register(QMSCAPA)
class QMSCAPAAdmin(admin.ModelAdmin):
    list_display = ('capa_number', 'qms_action', 'source_type', 'priority', 'status', 'action_owner', 'target_completion_date', 'approved_by')
    list_filter = ('source_type', 'priority', 'status', 'effectiveness_result', 'target_completion_date')
    search_fields = ('capa_number', 'qms_action__qms_number', 'qms_action__title', 'source_reference', 'root_cause_analysis')
    readonly_fields = ('capa_number', 'created_at', 'updated_at', 'approved_at', 'closed_at')


class QMSApprovalStepInline(admin.TabularInline):
    model = QMSApprovalStep
    extra = 0
    readonly_fields = ('signed_at',)


@admin.register(QMSApprovalRoute)
class QMSApprovalRouteAdmin(admin.ModelAdmin):
    list_display = ('route_number', 'title', 'target_model', 'status', 'current_step', 'created_by', 'created_at')
    list_filter = ('status', 'target_model', 'created_at')
    search_fields = ('route_number', 'title', 'target_model')
    readonly_fields = ('route_number', 'created_at', 'updated_at')
    inlines = [QMSApprovalStepInline]


@admin.register(QMSElectronicSignature)
class QMSElectronicSignatureAdmin(admin.ModelAdmin):
    list_display = ('signature_number', 'target_model', 'target_object_id', 'meaning', 'signer', 'signed_at')
    list_filter = ('target_model', 'signed_at')
    search_fields = ('signature_number', 'meaning', 'signature_hash')
    readonly_fields = ('signature_number', 'signature_hash', 'signed_at')


@admin.register(QMSFieldAuditTrail)
class QMSFieldAuditTrailAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'object_id', 'field_name', 'changed_by', 'changed_at')
    list_filter = ('model_name', 'field_name', 'changed_at')
    search_fields = ('model_name', 'field_name', 'old_value', 'new_value', 'reason')
    readonly_fields = ('changed_at',)


@admin.register(QMSReportExport)
class QMSReportExportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'export_format', 'status', 'requested_by', 'created_at', 'generated_at')
    list_filter = ('report_type', 'export_format', 'status', 'created_at')
    search_fields = ('report_type',)


@admin.register(QMSSamplingPlan)
class QMSSamplingPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'inspection_type', 'aql_level', 'sample_size', 'acceptance_number', 'rejection_number', 'is_active')
    list_filter = ('inspection_type', 'aql_level', 'is_active')
    search_fields = ('name', 'procedure_reference', 'product__product_name')


@admin.register(QMSLabSpecification)
class QMSLabSpecificationAdmin(admin.ModelAdmin):
    list_display = ('test_name', 'product', 'specification', 'unit', 'effective_date', 'expiry_date', 'is_active')
    list_filter = ('is_active', 'unit', 'effective_date', 'expiry_date')
    search_fields = ('test_name', 'method_reference', 'specification', 'product__product_name')


@admin.register(QMSStabilitySchedule)
class QMSStabilityScheduleAdmin(admin.ModelAdmin):
    list_display = ('product', 'bmr', 'condition', 'time_point', 'chamber', 'pull_date', 'status')
    list_filter = ('condition', 'status', 'pull_date')
    search_fields = ('product__product_name', 'bmr__batch_number', 'chamber', 'result_summary')


@admin.register(QMSSupplierQualification)
class QMSSupplierQualificationAdmin(admin.ModelAdmin):
    list_display = ('supplier_name', 'material_name', 'status', 'risk_level', 'qualification_score', 'last_audit_date', 'next_audit_date')
    list_filter = ('status', 'risk_level', 'last_audit_date', 'next_audit_date')
    search_fields = ('supplier_name', 'material_name', 'approval_notes')


@admin.register(QMSStabilityResult)
class QMSStabilityResultAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'test_name', 'result_value', 'passed', 'test_date', 'analyst')
    list_filter = ('passed', 'test_date')
    search_fields = ('schedule__study_number', 'test_name', 'result_value', 'specification')


@admin.register(QMSMaterialQC)
class QMSMaterialQCAdmin(admin.ModelAdmin):
    list_display = ('material_lot_number', 'material_name', 'supplier', 'status', 'bmr', 'owner')
    list_filter = ('status', 'received_date', 'expiry_date')
    search_fields = ('material_lot_number', 'material_name', 'material_code', 'supplier__supplier_name', 'bmr__batch_number')


@admin.register(QMSCOA)
class QMSCOAAdmin(admin.ModelAdmin):
    list_display = ('coa_number', 'product', 'bmr', 'quality_lot', 'status', 'prepared_by', 'approved_by')
    list_filter = ('status', 'market', 'created_at')
    search_fields = ('coa_number', 'product__product_name', 'bmr__batch_number', 'specification_reference')


@admin.register(QMSCalibrationRecord)
class QMSCalibrationRecordAdmin(admin.ModelAdmin):
    list_display = ('equipment_id', 'equipment_name', 'department', 'status', 'owner', 'last_calibrated', 'next_due_date', 'verified_by')
    list_filter = ('department', 'status', 'next_due_date')
    search_fields = ('equipment_id', 'equipment_name', 'serial_number', 'manufacturer', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'verified_at')


@admin.register(QMSCalibrationEvent)
class QMSCalibrationEventAdmin(admin.ModelAdmin):
    list_display = ('calibration', 'calibration_date', 'result', 'certificate_number', 'performed_by', 'verified_by', 'next_due_date')
    list_filter = ('result', 'calibration_date', 'next_due_date')
    search_fields = ('calibration__equipment_id', 'calibration__equipment_name', 'certificate_number', 'notes')
    readonly_fields = ('created_at', 'verified_at')


@admin.register(QMSTrainingRecord)
class QMSTrainingRecordAdmin(admin.ModelAdmin):
    list_display = ('document', 'trainee', 'training_type', 'status', 'assigned_date', 'due_date', 'completed_date')
    list_filter = ('training_type', 'status', 'due_date')
    search_fields = ('document__document_number', 'document__title', 'trainee__username')


@admin.register(QMSChangeImpactAssessment)
class QMSChangeImpactAssessmentAdmin(admin.ModelAdmin):
    list_display = ('change_action', 'bmr_impact', 'validation_impact', 'regulatory_impact', 'training_impact', 'stability_impact', 'assessed_by')
    list_filter = ('bmr_impact', 'validation_impact', 'regulatory_impact', 'training_impact', 'stability_impact')
    search_fields = ('impact_summary', 'qa_decision', 'change_action__qms_number')


@admin.register(QMSChangeControl)
class QMSChangeControlAdmin(admin.ModelAdmin):
    list_display = ('change_number', 'qms_action', 'change_type', 'risk_level', 'status', 'owner', 'planned_implementation_date', 'approved_by')
    list_filter = ('change_type', 'risk_level', 'status', 'planned_implementation_date')
    search_fields = ('change_number', 'qms_action__qms_number', 'qms_action__title', 'source_reference', 'justification', 'impact_summary')
    readonly_fields = ('change_number', 'created_at', 'updated_at', 'approved_at', 'closed_at')


@admin.register(QMSRecordLink)
class QMSRecordLinkAdmin(admin.ModelAdmin):
    list_display = ('from_content_type', 'from_object_id', 'link_type', 'to_content_type', 'to_object_id', 'created_by', 'created_at')
    list_filter = ('link_type', 'from_content_type', 'to_content_type', 'created_at')
    search_fields = ('rationale',)
    readonly_fields = ('created_at',)


@admin.register(QMSComplaintRecall)
class QMSComplaintRecallAdmin(admin.ModelAdmin):
    list_display = ('complaint_number', 'product', 'market', 'customer', 'severity', 'status', 'created_at', 'closed_at')
    list_filter = ('severity', 'status', 'market', 'created_at')
    search_fields = ('complaint_number', 'customer', 'description', 'health_risk_assessment', 'recall_decision')
    readonly_fields = ('complaint_number', 'created_at', 'closed_at')


@admin.register(QMSRegulatoryPackage)
class QMSRegulatoryPackageAdmin(admin.ModelAdmin):
    list_display = ('package_number', 'title', 'market', 'authority', 'status', 'submission_date', 'approval_date', 'owner')
    list_filter = ('status', 'market', 'authority', 'submission_date')
    search_fields = ('package_number', 'title', 'dossier_reference', 'authority')
    readonly_fields = ('package_number',)
    filter_horizontal = ('included_documents',)


@admin.register(QMSNotificationRule)
class QMSNotificationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'trigger_type', 'days_before', 'role_to_notify', 'is_active')
    list_filter = ('trigger_type', 'role_to_notify', 'is_active')
    search_fields = ('name',)


@admin.register(QMSLabInvestigation)
class QMSLabInvestigationAdmin(admin.ModelAdmin):
    list_display = ('investigation_number', 'event_type', 'test_name', 'status', 'disposition', 'bmr', 'product', 'opened_by', 'opened_at')
    list_filter = ('event_type', 'status', 'disposition', 'opened_at')
    search_fields = ('investigation_number', 'test_name', 'specification', 'result_value', 'root_cause', 'qa_conclusion', 'bmr__batch_number')
    readonly_fields = ('investigation_number', 'opened_at', 'closed_at')


@admin.register(QMSQualityQuery)
class QMSQualityQueryAdmin(admin.ModelAdmin):
    list_display = ('query_number', 'query_type', 'subject', 'priority', 'status', 'source', 'assigned_to', 'due_date')
    list_filter = ('query_type', 'priority', 'status', 'due_date', 'created_at')
    search_fields = ('query_number', 'subject', 'source', 'question', 'response', 'bmr__batch_number', 'product__product_name')
    readonly_fields = ('query_number', 'created_at', 'responded_at', 'closed_at')
