"""
Django signals for real-time notifications
Sends WebSocket notifications when actions occur across the system
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


@receiver(post_save, sender='workflow.BatchPhaseExecution')
def phase_execution_saved(sender, instance, created, update_fields, **kwargs):
    """
    Send real-time notification when a phase execution is created or updated
    """
    try:
        # Only send notification on updates (status changes), not initial creation
        if not created or (update_fields and 'status' in update_fields):
            layer = get_channel_layer()
            
            # Get all users who should be notified about this phase
            # This includes: users involved in this BMR, users with relevant roles
            bmr = instance.bmr
            phase = instance.phase
            
            # Determine which roles should be notified
            notify_roles = set()
            
            # Always notify admin and production manager
            notify_roles.add('admin')
            notify_roles.add('production_manager')
            
            # Add role-specific notifications based on phase
            if phase.phase_name in ['mixing', 'granulation', 'blending', 'compression', 'coating', 'filling']:
                notify_roles.add('qa')
                notify_roles.add('qc')
            
            if phase.phase_name in ['regulatory_approval']:
                notify_roles.add('regulatory')
            
            if phase.phase_name in ['raw_material_release']:
                notify_roles.add('store_manager')
                notify_roles.add('dispensing_manager')
            
            if phase.phase_name in ['qc_testing', 'final_qa']:
                notify_roles.add('qa')
                notify_roles.add('qc')
                notify_roles.add('quarantine')
            
            # Send notification to each relevant role group
            for role in notify_roles:
                async_to_sync(layer.group_send)(
                    f"role_{role}",
                    {
                        'type': 'phase_update',
                        'phase_id': instance.id,
                        'bmr_number': bmr.bmr_number,
                        'phase_name': phase.get_phase_name_display(),
                        'status': instance.status,
                        'updated_by': instance.completed_by.username if instance.completed_by else instance.started_by.username if instance.started_by else 'System',
                        'timestamp': instance.completed_date.isoformat() if instance.completed_date else instance.started_date.isoformat() if instance.started_date else None,
                    }
                )
            
            logger.info(f"Sent phase update notification for {bmr.bmr_number} - {phase.phase_name}: {instance.status}")
            
    except Exception as e:
        logger.error(f"Error sending phase execution notification: {e}")


@receiver(post_save, sender='bmr.BMR')
def bmr_status_changed(sender, instance, update_fields, **kwargs):
    """
    Send real-time notification when BMR status changes
    """
    try:
        if update_fields and 'status' in update_fields:
            layer = get_channel_layer()
            
            # Determine which roles should be notified based on status
            notify_roles = set(['admin'])
            
            if instance.status == 'approved':
                notify_roles.add('production_manager')
                notify_roles.add('qa')
                notify_roles.add('store_manager')
            elif instance.status == 'rejected':
                notify_roles.add('qa')
                notify_roles.add('regulatory')
            elif instance.status == 'in_production':
                notify_roles.add('qa')
                notify_roles.add('production_manager')
            elif instance.status == 'completed':
                notify_roles.add('qa')
                notify_roles.add('production_manager')
                notify_roles.add('finished_goods_store')
            
            # Send notification to each relevant role group
            for role in notify_roles:
                async_to_sync(layer.group_send)(
                    f"role_{role}",
                    {
                        'type': 'bmr_status_update',
                        'bmr_number': instance.bmr_number,
                        'batch_number': instance.batch_number,
                        'status': instance.status,
                        'updated_by': instance.approved_by.username if instance.approved_by else instance.created_by.username,
                        'timestamp': instance.approved_date.isoformat() if instance.approved_date else instance.created_date.isoformat(),
                    }
                )
            
            logger.info(f"Sent BMR status update notification for {instance.bmr_number}: {instance.status}")
            
    except Exception as e:
        logger.error(f"Error sending BMR status notification: {e}")


@receiver(post_save, sender='bmr.RawMaterialRelease')
def material_release_updated(sender, instance, update_fields, **kwargs):
    """
    Send real-time notification when material release status changes
    """
    try:
        if update_fields and 'status' in update_fields:
            layer = get_channel_layer()
            
            # Notify relevant roles
            notify_roles = ['admin', 'store_manager', 'dispensing_manager', 'production_manager']
            
            for role in notify_roles:
                async_to_sync(layer.group_send)(
                    f"role_{role}",
                    {
                        'type': 'material_release_update',
                        'release_number': instance.release_number,
                        'status': instance.status,
                        'updated_by': instance.released_by.username if instance.released_by else instance.received_by.username if instance.received_by else 'System',
                        'timestamp': instance.release_completed_date.isoformat() if instance.release_completed_date else instance.release_date.isoformat(),
                    }
                )
            
            logger.info(f"Sent material release notification for {instance.release_number}: {instance.status}")
            
    except Exception as e:
        logger.error(f"Error sending material release notification: {e}")


@receiver(post_save, sender='quarantine.QuarantineBatch')
def quarantine_status_changed(sender, instance, update_fields, **kwargs):
    """
    Send real-time notification when quarantine status changes
    """
    try:
        if update_fields and 'status' in update_fields:
            layer = get_channel_layer()
            
            # Notify QA, QC, and production roles
            notify_roles = ['admin', 'qa', 'qc', 'quarantine', 'production_manager']
            
            for role in notify_roles:
                async_to_sync(layer.group_send)(
                    f"role_{role}",
                    {
                        'type': 'qc_update',
                        'batch_number': instance.bmr.batch_number if instance.bmr else 'Unknown',
                        'quarantine_status': instance.status,
                        'action': 'Status Updated',
                        'updated_by': 'System',
                        'timestamp': instance.created_date.isoformat() if instance.created_date else None,
                    }
                )
            
            logger.info(f"Sent quarantine status notification for batch {instance.bmr.batch_number if instance.bmr else 'Unknown'}: {instance.status}")
            
    except Exception as e:
        logger.error(f"Error sending quarantine status notification: {e}")