import pkgutil_compat  # noqa
import os, django, json
os.environ['DJANGO_SETTINGS_MODULE'] = 'kampala_pharma.settings'
django.setup()

from workflow.models import BatchPhaseExecution

# Reset KAMADOL coding_setup (submitted out of order)
print("=== RESETTING KAMADOL coding_setup ===")
for pe in BatchPhaseExecution.objects.filter(bmr__product__product_name__icontains='KAMADOL', phase__phase_name='blister_packing'):
    pd = pe.phase_data or {}
    ps = pd.get('packing_sections', {})
    statuses = ps.get('section_statuses', {})
    
    # Remove coding_setup data and status
    ps.pop('coding_setup', None)
    statuses.pop('coding_setup', None)
    statuses.pop('coding_setup_submitted_by', None)
    statuses.pop('coding_setup_submitted_date', None)
    
    ps['section_statuses'] = statuses
    pd['packing_sections'] = ps
    pe.phase_data = pd
    pe.save()
    
    print(f"PE#{pe.id} — coding_setup removed")
    print(f"  Remaining statuses: {json.dumps(statuses, indent=4)}")
