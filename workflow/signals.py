import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import models
from .models import BatchPhaseExecution, PhaseTimingSetting, PhaseTimeOverrunNotification, ProductMachineTimingSetting
from accounts.models import CustomUser
import threading
import time

logger = logging.getLogger('workflow')

# Store active overrun checkers to prevent duplicates
active_checkers = {}

def check_phase_for_overrun(phase_execution):
    """Check if a specific phase has overrun and create notification if needed"""
    try:
        # Skip if phase is not active or hasn't started
        if phase_execution.status != 'in_progress' or not phase_execution.started_date:
            return
            
        # Skip if notification already exists for this phase
        existing_notification = PhaseTimeOverrunNotification.objects.filter(
            phase_execution=phase_execution,
            acknowledged=False
        ).exists()
        
        if existing_notification:
            return
            
        # Calculate elapsed time
        elapsed = timezone.now() - phase_execution.started_date
        elapsed_hours = elapsed.total_seconds() / 3600
        
        # Get expected duration using the same priority system as dashboards
        # This checks ProductMachineTimingSetting first, then PhaseTimingSetting
        try:
            expected_hours = ProductMachineTimingSetting.get_expected_duration_for_execution(phase_execution)
            
            # If no proper timing is configured, allow phase to continue without notifications
            if ProductMachineTimingSetting.is_timing_configuration_missing(phase_execution):
                logger.info(f"No timing configuration for {phase_execution.bmr.batch_number} - {phase_execution.phase.phase_name}. Phase can continue without overrun notifications.")
                return  # Skip notification - let phase continue
                
        except Exception as e:
            logger.warning(f"Error getting timing configuration for {phase_execution.bmr.batch_number} - {phase_execution.phase.phase_name}: {e}. Phase continues without monitoring.")
            return  # Skip notification on any timing error
            
        # Check if phase has exceeded expected time
        if elapsed_hours > expected_hours:
            overrun_hours = elapsed_hours - expected_hours
            overrun_percent = int((elapsed_hours / expected_hours) * 100) - 100
            
            # Calculate exact overrun time for display
            overrun_minutes = int((overrun_hours % 1) * 60)
            overrun_hours_int = int(overrun_hours)
            
            # Format overrun time display
            if overrun_hours_int > 0:
                overrun_time_str = f"{overrun_hours_int}h {overrun_minutes}m"
            else:
                overrun_time_str = f"{overrun_minutes}m"
            
            # Create single notification per phase overrun (not per admin)
            PhaseTimeOverrunNotification.objects.create(
                phase_execution=phase_execution,
                threshold_exceeded_percent=overrun_percent,
                message=f"OVERRUN: Batch {phase_execution.bmr.batch_number} - {phase_execution.phase.phase_name.replace('_', ' ').title()} exceeded expected {expected_hours:.1f}h by +{overrun_time_str}"
            )
                
            logger.warning(f"OVERRUN ALERT: Created notification for batch {phase_execution.bmr.batch_number} - {phase_execution.phase.phase_name} ({overrun_hours:.1f}h overrun, {overrun_percent}% over)")
            
    except Exception as e:
        logger.error(f"Error checking phase overrun: {e}")

def start_continuous_checker(phase_execution):
    """Start a background thread to continuously check a phase for overrun"""
    phase_id = phase_execution.id
    
    # Don't start if checker already exists for this phase
    if phase_id in active_checkers:
        return
        
    def continuous_check():
        """Continuously check the phase until it's completed"""
        try:
            while True:
                # Get fresh instance from database
                try:
                    current_phase = BatchPhaseExecution.objects.get(id=phase_id)
                except BatchPhaseExecution.DoesNotExist:
                    break
                    
                # Stop checking if phase is no longer in progress
                if current_phase.status != 'in_progress':
                    break
                    
                # Check for overrun
                check_phase_for_overrun(current_phase)
                
                # Wait 1 minute before checking again (more responsive)
                time.sleep(60)  # 1 minute
                
        except Exception as e:
            logger.error(f"Error in continuous checker for phase {phase_id}: {e}")
        finally:
            # Remove from active checkers when done
            active_checkers.pop(phase_id, None)
            logger.info(f"Stopped overrun monitoring for phase {phase_id}")
    
    # Start checker thread
    checker_thread = threading.Thread(target=continuous_check, daemon=True)
    checker_thread.start()
    active_checkers[phase_id] = checker_thread
    logger.info(f"Started overrun monitoring for phase {phase_id} - batch {phase_execution.bmr.batch_number}")

@receiver(post_save, sender=BatchPhaseExecution)
def handle_phase_execution_change(sender, instance, created, **kwargs):
    """Handle phase execution changes - start overrun monitoring when phase starts"""
    
    # If phase just started (status changed to in_progress and has started_date)
    if instance.status == 'in_progress' and instance.started_date:
        # Start continuous overrun monitoring for this phase
        start_continuous_checker(instance)
        
        # Also do immediate check
        check_phase_for_overrun(instance)
    
    # Update BMR status based on phase changes (self-sustaining system)
    try:
        instance.bmr.update_status_based_on_phases()
    except Exception as e:
        logger.error(f"Error updating BMR status for {instance.bmr.bmr_number}: {e}")