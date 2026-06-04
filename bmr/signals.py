"""
Signals for BMR app.
Auto-update BMR Issuance Log entries when workflow phases complete.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from workflow.models import BatchPhaseExecution


@receiver(post_save, sender=BatchPhaseExecution)
def update_issuance_log_on_phase_complete(sender, instance, **kwargs):
    """
    Auto-populate BMR Issuance Log fields when workflow phases complete.
    
    Updates:
    - pack_size when blister_packing or bulk_packing completes
    - submitted_by & release_date when final_qa completes (QA releases to finished goods)
    
    NOTE: received_by is NOT auto-populated - Production Manager signs manually
    """
    # Only process completed phases
    if instance.status != 'completed':
        return
    
    # Only process these specific phases
    relevant_phases = ['blister_packing', 'bulk_packing', 'final_qa', 'finished_goods_store']
    if instance.phase.phase_name not in relevant_phases:
        return
    
    # Get the issuance log entry for this BMR
    from bmr.models import BMRIssuanceLogEntry
    
    try:
        entry = BMRIssuanceLogEntry.objects.get(bmr=instance.bmr)
        entry.auto_populate_from_workflow()
    except BMRIssuanceLogEntry.DoesNotExist:
        # No entry exists yet - might be an old BMR
        pass
    except Exception as e:
        # Log error but don't crash
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error updating issuance log for BMR {instance.bmr.batch_number}: {str(e)}')
