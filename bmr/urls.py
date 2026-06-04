from django.urls import path
from .views import (
    create_bmr_view, bmr_list_view, bmr_detail_view,
    start_phase_view, complete_phase_view, reject_phase_view,
    create_bmr_request, bmr_request_list, bmr_request_detail,
    approve_bmr_request, reject_bmr_request, save_granulation_data,
    bmr_issuance_log_list, bmr_issuance_log_detail,
    bmr_issuance_log_sign_received, bmr_issuance_log_sign_submitted,
    bmr_issuance_log_download
)

app_name = 'bmr'

urlpatterns = [
    # Original BMR URLs
    path('create/', create_bmr_view, name='create'),
    path('list/', bmr_list_view, name='list'),
    path('<int:bmr_id>/', bmr_detail_view, name='detail'),
    path('<int:bmr_id>/start-phase/<str:phase_name>/', start_phase_view, name='start_phase'),
    path('<int:bmr_id>/complete-phase/<str:phase_name>/', complete_phase_view, name='complete_phase'),
    path('<int:bmr_id>/reject-phase/<str:phase_name>/', reject_phase_view, name='reject_phase'),
    path('<int:bmr_id>/save-granulation/', save_granulation_data, name='save_granulation_data'),
    
    # BMR Request URLs
    path('request/create/', create_bmr_request, name='create_bmr_request'),
    path('requests/', bmr_request_list, name='bmr_request_list'),
    path('request/<int:request_id>/', bmr_request_detail, name='bmr_request_detail'),
    path('request/<int:request_id>/approve/', approve_bmr_request, name='approve_bmr_request'),
    path('request/<int:request_id>/reject/', reject_bmr_request, name='reject_bmr_request'),
    
    # BMR Issuance Log URLs
    path('issuance-logs/', bmr_issuance_log_list, name='issuance_log_list'),
    path('issuance-log/<int:log_id>/', bmr_issuance_log_detail, name='issuance_log_detail'),
    path('issuance-log/entry/<int:entry_id>/sign-received/', bmr_issuance_log_sign_received, name='issuance_log_sign_received'),
    path('issuance-log/entry/<int:entry_id>/sign-submitted/', bmr_issuance_log_sign_submitted, name='issuance_log_sign_submitted'),
    path('issuance-log/<int:log_id>/download/', bmr_issuance_log_download, name='issuance_log_download'),
]
