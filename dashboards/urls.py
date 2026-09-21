from django.urls import path
from . import views
from . import bmr_form_views
from . import qms_detail_views
from django.views.generic.base import RedirectView

app_name = 'dashboards'

urlpatterns = [
    path('export-wip/', views.export_wip, name='export_wip'),
    path('', views.dashboard_home, name='dashboard_home'),
    
    # QA Dashboard
    path('qa/', views.qa_dashboard, name='qa_dashboard'),
    path('head-qa/', views.head_qa_dashboard, name='head_qa_dashboard'),
    
    # Regulatory Dashboard
    path('regulatory/', views.regulatory_dashboard, name='regulatory_dashboard'),
    
    # Production Manager Dashboard
    path('production-manager/', views.production_manager_dashboard, name='production_manager_dashboard'),
    
    # Store Manager Dashboard (Raw Material Release)
    path('store/', views.store_dashboard, name='store_dashboard'),
    
    # Generic Operator Dashboard
    path('operator/', views.operator_dashboard, name='operator_dashboard'),
    # Maintenance Dashboard
    path('maintenance/', views.maintenance_dashboard, name='maintenance_dashboard'),
    path('maintenance/breakdown/<int:phase_execution_id>/', views.maintenance_breakdown_detail, name='maintenance_breakdown_detail'),
    
    # BMR Detailed Forms - All phases use unified phase_form_view
    path('bmr-forms/phase/<int:phase_execution_id>/', bmr_form_views.phase_form_selector, name='phase_form_selector'),
    path('bmr-forms/view/<int:phase_execution_id>/', bmr_form_views.phase_form_view, name='phase_form'),
    path('bmr-forms/operator/<int:phase_execution_id>/', bmr_form_views.phase_form_view, name='phase_form_operator'),
    path('bmr-forms/granulation/<int:phase_execution_id>/', bmr_form_views.phase_form_view, name='granulation_form'),  # Legacy
    path('api/save-form-draft/', bmr_form_views.save_form_draft, name='save_form_draft'),
    path('api/dynamic-save/', bmr_form_views.dynamic_save, name='dynamic_save'),
    path('api/save-page-field/', bmr_form_views.save_page_field, name='save_page_field'),
    path('bmr-forms/packaging-req/<int:phase_execution_id>/', bmr_form_views.packaging_req_action, name='packaging_req_action'),
    
    # Phase Notifications & Timing
    path('phase-notifications/', views.phase_notifications_view, name='phase_notifications'),
    path('api/phase-timing-alerts/<int:alert_id>/acknowledge/', views.acknowledge_phase_timing_alert, name='acknowledge_phase_timing_alert'),
    path('api/phase-timing-alerts/acknowledge-all/', views.acknowledge_all_phase_timing_alerts, name='acknowledge_all_phase_timing_alerts'),
    
    # System Logs Viewer (Admin/QA access)
    path('system-logs/', views.system_logs_viewer, name='system_logs'),
    
    # Production Operator Dashboards
    path('mixing/', views.mixing_dashboard, name='mixing_dashboard'),
    path('granulation/', views.granulation_dashboard, name='granulation_dashboard'),
    path('blending/', views.blending_dashboard, name='blending_dashboard'),
    path('compression/', views.compression_dashboard, name='compression_dashboard'),
    path('coating/', views.coating_dashboard, name='coating_dashboard'),
    path('drying/', views.drying_dashboard, name='drying_dashboard'),
    path('filling/', views.filling_dashboard, name='filling_dashboard'),
    path('tube-filling/', views.tube_filling_dashboard, name='tube_filling_dashboard'),
    path('sorting/', views.sorting_dashboard, name='sorting_dashboard'),
    
    # Quality Control Dashboard
    path('qc/', views.qc_dashboard, name='qc_dashboard'),
    path('qc/quality-lots/<int:lot_id>/', views.quality_lot_detail, name='quality_lot_detail'),
    path('qms/reports/', views.qms_reports, name='qms_reports'),
    path('qms/reports/<str:report_type>/<int:object_id>/', views.qms_report_detail, name='qms_report_detail'),
    
    # Packaging Dashboards
    path('packaging/', views.packaging_dashboard, name='packaging_dashboard'),
    path('packing/', views.packing_dashboard, name='packing_dashboard'),
    path('finished-goods/', views.finished_goods_dashboard, name='finished_goods_dashboard'),
    
    # Admin Dashboard
        # Redirect for old URL pattern
    path('admin/', views.admin_redirect, name='admin_redirect'),
    path('admin-overview/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/timeline/', views.admin_timeline_view, name='admin_timeline'),
    path('admin/fgs-monitor/', views.admin_fgs_monitor, name='admin_fgs_monitor'),
    path('admin/export-timeline/', views.export_timeline_data, name='export_timeline_data'),
    path('admin/live-tracking/', views.live_tracking_view, name='live_tracking'),
    # path('export-wip/', views.export_wip, name='export_wip'),  # Commented out - missing view function
    
    # Admin section routes for direct URL links
    path('machine-management/', views.admin_machine_management, name='machine_management'),
    path('quality-control/', views.admin_quality_control, name='quality_control'),
    path('inventory/', views.admin_inventory, name='inventory'),
    path('user-management/', views.admin_user_management, name='user_management'),
    path('system-health/', views.admin_system_health, name='system_health'),
    
    # Notification API endpoints
    path('api/notification-counts/', views.notification_counts_api, name='notification_counts_api'),
    path('api/notifications-feed/', views.notifications_feed_api, name='notifications_feed_api'),
    path('api/overrun-alerts/', views.overrun_alerts_api, name='overrun_alerts_api'),
    path('api/notifications/<int:notification_id>/mark-read/', views.mark_notification_read_api, name='mark_notification_read_api'),
    path('api/notifications/<int:notification_id>/dismiss/', views.dismiss_notification_api, name='dismiss_notification_api'),
    path('api/request-explanation/', views.request_explanation_api, name='request_explanation_api'),
    path('api/request-all-explanations/', views.request_all_explanations_api, name='request_all_explanations_api'),
    
    # Notification mark as read
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    
    # Clear all notifications
    path('notifications/clear-all/', views.clear_all_notifications, name='clear_all_notifications'),
    
    # Timer expiration notification
    path('api/phase-timer-expired/', views.phase_timer_expired_api, name='phase_timer_expired'),
    
    # Monthly Production Analytics API
    path('api/monthly-production-analytics/', views.monthly_production_analytics_api, name='monthly_production_analytics_api'),
    
    # Excel Export
    path('export/monthly-production-excel/', views.export_monthly_production_excel, name='export_monthly_production_excel'),
    
    # Detailed Product Breakdown API
    path('api/detailed-product-breakdown/', views.get_detailed_product_breakdown_api, name='detailed_product_breakdown_api'),
    
    # Phase Chart Filter API
    
    # ========================================================================
    # QMS DETAIL VIEWS - View full record with attachments, comments, history
    # ========================================================================
    path('qms/action/<int:action_id>/', qms_detail_views.qms_action_detail, name='qms_action_detail'),
    path('qms/capa/<int:capa_id>/', qms_detail_views.qms_capa_detail, name='qms_capa_detail'),
    path('qms/change-control/<int:change_id>/', qms_detail_views.qms_change_control_detail, name='qms_change_control_detail'),
    path('qms/audit/<int:audit_id>/', qms_detail_views.qms_audit_detail, name='qms_audit_detail'),
    path('qms/risk/<int:risk_id>/', qms_detail_views.qms_risk_detail, name='qms_risk_detail'),
    path('qms/document/<int:document_id>/', qms_detail_views.qms_document_detail, name='qms_document_detail'),
    path('qms/deviation/<int:deviation_id>/', qms_detail_views.qms_deviation_detail, name='qms_deviation_detail'),
    path('qms/query/<int:query_id>/', qms_detail_views.qms_quality_query_detail, name='qms_quality_query_detail'),
    path('qms/regulatory/<int:package_id>/', qms_detail_views.qms_regulatory_package_detail, name='qms_regulatory_package_detail'),
    path('qms/regulatory/', qms_detail_views.qms_regulatory_packages, name='qms_regulatory_packages'),
    path('qms/training/<int:training_id>/', qms_detail_views.qms_training_detail, name='qms_training_detail'),
    path('qms/calibration/<int:calibration_id>/', qms_detail_views.qms_calibration_detail, name='qms_calibration_detail'),
    path('qms/qc/', qms_detail_views.qms_qc_register, name='qms_qc_register'),
    path('qms/qc/oos/<int:investigation_id>/', qms_detail_views.qms_lab_investigation_detail, name='qms_lab_investigation_detail'),
    path('qms/qc/stability/<int:stability_id>/', qms_detail_views.qms_stability_detail, name='qms_stability_detail'),
    path('qms/qc/coa/<int:coa_id>/', qms_detail_views.qms_coa_detail, name='qms_coa_detail'),
    path('qms/qc/material/<int:material_qc_id>/', qms_detail_views.qms_material_qc_detail, name='qms_material_qc_detail'),
    path('qms/qc/supplier/<int:supplier_id>/', qms_detail_views.qms_supplier_quality_detail, name='qms_supplier_quality_detail'),
    path('qms/record-links/create/', qms_detail_views.qms_record_link_create, name='qms_record_link_create'),
    path('qms/record-links/<int:link_id>/delete/', qms_detail_views.qms_record_link_delete, name='qms_record_link_delete'),
    
    # QMS File Upload & Comments (AJAX handlers)
    path('qms/action/<int:action_id>/upload/', qms_detail_views.qms_action_upload_file, name='qms_action_upload'),
    path('qms/action/<int:action_id>/comment/', qms_detail_views.qms_action_add_comment, name='qms_action_comment'),
    path('qms/audit/<int:audit_id>/upload/', qms_detail_views.qms_audit_upload_file, name='qms_audit_upload'),
    path('qms/audit/<int:audit_id>/comment/', qms_detail_views.qms_audit_add_comment, name='qms_audit_comment'),
    path('qms/risk/<int:risk_id>/upload/', qms_detail_views.qms_risk_upload_file, name='qms_risk_upload'),
    path('qms/risk/<int:risk_id>/comment/', qms_detail_views.qms_risk_add_comment, name='qms_risk_comment'),
    path('qms/document/<int:document_id>/upload/', qms_detail_views.qms_document_upload_file, name='qms_document_upload'),
    path('qms/document/<int:document_id>/comment/', qms_detail_views.qms_document_add_comment, name='qms_document_comment'),
    path('qms/deviation/<int:deviation_id>/upload/', qms_detail_views.qms_deviation_upload_file, name='qms_deviation_upload'),
    path('qms/deviation/<int:deviation_id>/comment/', qms_detail_views.qms_deviation_add_comment, name='qms_deviation_comment'),
    path('qms/query/<int:query_id>/upload/', qms_detail_views.qms_quality_query_upload_file, name='qms_quality_query_upload'),
    path('qms/query/<int:query_id>/comment/', qms_detail_views.qms_quality_query_add_comment, name='qms_quality_query_comment'),
    path('qms/regulatory/<int:package_id>/upload/', qms_detail_views.qms_regulatory_package_upload_file, name='qms_regulatory_package_upload'),
    path('qms/regulatory/<int:package_id>/comment/', qms_detail_views.qms_regulatory_package_add_comment, name='qms_regulatory_package_comment'),
    
    # QMS Attachment Download & Delete
    path('qms/attachment/<int:attachment_id>/download/', qms_detail_views.qms_attachment_download, name='qms_attachment_download'),
    path('qms/attachment/<int:attachment_id>/delete/', qms_detail_views.qms_attachment_delete, name='qms_attachment_delete'),
    path('api/phase-chart-data/', views.get_phase_chart_data_api, name='phase_chart_data_api'),
]
