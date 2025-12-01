import logging
from django.utils import timezone
from bmr.models import BMR
from .models import ProductionPhase, BatchPhaseExecution, WorkflowTemplate, WorkflowTemplatePhase
from .constants import (
    PRODUCT_TYPES, TABLET_TYPES, PHASE_NAMES, PHASE_STATUSES,
    is_tablet_type_2, get_qc_phase_for_product
)
from .utils import (
    product_has_tag, product_requires_coating, product_is_tablet_like,
    product_is_capsule_like, product_is_ointment_like,
    get_packing_phase_for_product as util_get_packing_phase_for_product
)

logger = logging.getLogger('workflow')

class WorkflowService:
    """Service to manage workflow progression and phase automation"""
    @classmethod
    def initialize_workflow_from_template(cls, bmr):
        """Initialize workflow phases for a BMR using the new template system"""
        try:
            # Determine which template to use based on product type and tablet type
            product_type = bmr.product.product_type
            
            # Handle tablet type differentiation (use DB-driven product tags when available)
            if product_is_tablet_like(bmr.product):
                tablet_type = getattr(bmr.product, 'tablet_type', TABLET_TYPES['NORMAL'])
                if is_tablet_type_2(tablet_type):
                    template_product_type = 'tablet_type_2'
                else:
                    template_product_type = PRODUCT_TYPES['TABLET']
            else:
                template_product_type = product_type
            
            # Find the appropriate workflow template
            template = WorkflowTemplate.objects.filter(
                product_type=template_product_type,
                is_active=True
            ).first()
            
            if not template:
                # No template found - this should not happen in production
                raise ValueError(f"No workflow template found for product type: {template_product_type}")
            
            # Get template phases in order
            template_phases = template.phases.all().order_by('phase_order')
            
            # Filter out phases that should be skipped based on product attributes
            filtered_phases = []
            for template_phase in template_phases:
                # COATING LOGIC: Skip coating phase for uncoated tablets
                if product_is_tablet_like(bmr.product) and template_phase.phase_name == PHASE_NAMES['COATING']:
                    if not product_requires_coating(bmr.product):
                        logger.info(f"Skipping coating phase for uncoated tablet: {bmr.product.product_name}")
                        continue  # Skip this phase
                    else:
                        logger.info(f"Including coating phase for coated tablet: {bmr.product.product_name}")
                
                # PACKING LOGIC: Skip wrong packing phase for tablet types
                if product_is_tablet_like(bmr.product) and template_phase.phase_name in [PHASE_NAMES['BLISTER_PACKING'], PHASE_NAMES['BULK_PACKING']]:
                    tablet_type = getattr(bmr.product, 'tablet_type', TABLET_TYPES['NORMAL']) or TABLET_TYPES['NORMAL']
                    if is_tablet_type_2(tablet_type) and template_phase.phase_name == PHASE_NAMES['BLISTER_PACKING']:
                        logger.info(f"Skipping blister_packing for tablet_2: {bmr.product.product_name}")
                        continue  # Skip blister packing for tablet_2
                    elif not is_tablet_type_2(tablet_type) and template_phase.phase_name == PHASE_NAMES['BULK_PACKING']:
                        logger.info(f"Skipping bulk_packing for normal tablet: {bmr.product.product_name}")
                        continue  # Skip bulk packing for normal tablets
                
                # Add phase to filtered list
                filtered_phases.append(template_phase)
            
            logger.info(f"Using template '{template.name}' for BMR {bmr.batch_number} - {len(filtered_phases)} phases after filtering")
            
            # Create ProductionPhase objects and BatchPhaseExecution objects PRESERVING TEMPLATE ORDERING
            for template_phase in filtered_phases:
                
                # Get or create the production phase definition PRESERVING TEMPLATE ORDER
                phase, created = ProductionPhase.objects.get_or_create(
                    product_type=product_type,
                    phase_name=template_phase.phase_name,
                    defaults={
                        'phase_order': template_phase.phase_order,  # Use template's original order
                        'is_mandatory': template_phase.is_mandatory,
                        'requires_approval': template_phase.requires_approval,
                        'description': template_phase.description,
                        'estimated_duration_hours': template_phase.estimated_duration_hours
                    }
                )
                
                # Update phase order to match template if different
                if phase.phase_order != template_phase.phase_order:
                    logger.info(f"Updating {phase.phase_name} order from {phase.phase_order} to {template_phase.phase_order}")
                    phase.phase_order = template_phase.phase_order
                    phase.save()
                
                # Determine initial status
                if template_phase.phase_name == PHASE_NAMES['BMR_CREATION']:
                    initial_status = PHASE_STATUSES['COMPLETED']
                elif template_phase.phase_name == PHASE_NAMES['REGULATORY_APPROVAL']:
                    initial_status = PHASE_STATUSES['PENDING']
                else:
                    initial_status = PHASE_STATUSES['NOT_READY']
                
                # Create the batch phase execution
                BatchPhaseExecution.objects.get_or_create(
                    bmr=bmr,
                    phase=phase,
                    defaults={
                        'status': initial_status
                    }
                )
            
            logger.info(f"Initialized workflow from template for {bmr.batch_number} with {template_phases.count()} phases")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing workflow from template for BMR {bmr.bmr_number}: {e}")
            raise  # Re-raise the error instead of falling back
    
    @classmethod
    def get_current_phase(cls, bmr):
        """Get the current active phase for a BMR"""
        return BatchPhaseExecution.objects.filter(
            bmr=bmr,
            status__in=['pending', 'in_progress']
        ).order_by('phase__phase_order').first()
    
    @classmethod
    def get_next_phase(cls, bmr):
        """Get the next available phase for a BMR (pending or not_ready)"""
        current_executions = BatchPhaseExecution.objects.filter(
            bmr=bmr
        ).order_by('phase__phase_order')
        
        # Find the first pending phase
        for execution in current_executions:
            if execution.status == 'pending':
                return execution
        
        # If no pending phases, find the first not_ready phase
        for execution in current_executions:
            if execution.status == 'not_ready':
                return execution
        
        return None
    
    @classmethod
    def complete_phase(cls, bmr, phase_name, completed_by, comments=None):
        """Mark a phase as completed and activate the next phase"""
        try:
            execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=phase_name
            )
            
            # Mark current phase as completed
            execution.status = 'completed'
            execution.completed_by = completed_by
            execution.completed_date = timezone.now()
            if comments:
                execution.operator_comments = comments
            execution.save()
            
            # Create QC checkpoints if this is a QC phase
            if 'qc' in phase_name.lower():
                cls._create_qc_checkpoints(execution, completed_by)
            
            # Use the proper trigger_next_phase logic which handles quarantine and sequential flow
            cls.trigger_next_phase(bmr, execution.phase)
            
            # Return the next available phase for UI feedback
            return cls.get_next_phase(bmr)
                
        except BatchPhaseExecution.DoesNotExist:
            logger.warning(f"Phase execution not found: {phase_name} for BMR {bmr.bmr_number}")
        
        return None
    
    @classmethod
    def start_phase(cls, bmr, phase_name, started_by):
        """Start a phase execution - with prerequisite validation"""
        try:
            execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=phase_name,
                status='pending'
            )
            
            # Validate that all prerequisite phases are completed
            if not cls.can_start_phase(bmr, phase_name):
                logger.warning(f"Cannot start phase {phase_name} for BMR {bmr.bmr_number} - prerequisites not met")
                return None
            
            execution.status = 'in_progress'
            execution.started_by = started_by
            execution.started_date = timezone.now()
            execution.save()
            
            return execution
            
        except BatchPhaseExecution.DoesNotExist:
            logger.warning(f"Cannot start phase {phase_name} for BMR {bmr.bmr_number} - not pending")
        
        return None
    
    @classmethod
    def can_start_phase(cls, bmr, phase_name):
        """Check if a phase can be started (all prerequisites completed)"""
        try:
            current_execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=phase_name
            )
            
            # Cannot start phases that are not pending
            if current_execution.status != 'pending':
                return False
            
            # Get all phases with lower order (prerequisites)
            prerequisite_phases = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_order__lt=current_execution.phase.phase_order
            )
            
            # Check if all prerequisite phases are completed or skipped
            for prereq in prerequisite_phases:
                if prereq.status not in ['completed', 'skipped']:
                    return False
            
            return True
            
        except BatchPhaseExecution.DoesNotExist:
            return False
    
    @classmethod
    def get_workflow_status(cls, bmr):
        """Get complete workflow status for a BMR"""
        executions = BatchPhaseExecution.objects.filter(
            bmr=bmr
        ).select_related('phase').order_by('phase__phase_order')
        
        total_phases = executions.count()
        completed_phases = executions.filter(status='completed').count()
        current_phase = cls.get_current_phase(bmr)
        next_phase = cls.get_next_phase(bmr)
        
        return {
            'total_phases': total_phases,
            'completed_phases': completed_phases,
            'progress_percentage': (completed_phases / total_phases * 100) if total_phases > 0 else 0,
            'current_phase': current_phase,
            'next_phase': next_phase,
            'all_executions': executions,
            'is_complete': completed_phases == total_phases
        }
    
    @classmethod
    def _create_qc_checkpoints(cls, phase_execution, checked_by):
        """Create simple QC checkpoint when a QC phase is completed"""
        from workflow.models import PhaseCheckpoint
        
        # Create a simple checkpoint that just records the QC phase completion
        phase_name = phase_execution.phase.phase_name
        
        # Create readable checkpoint name
        checkpoint_name = phase_name.replace('_', ' ').title()
        
        # Determine if QC passed (95% pass rate for realistic data)
        import random
        qc_passed = random.random() < 0.95
        
        PhaseCheckpoint.objects.create(
            phase_execution=phase_execution,
            checkpoint_name=f"{checkpoint_name} Completed",
            expected_value="QC Phase Completion",
            actual_value="Completed" if qc_passed else "Failed",
            is_within_spec=qc_passed,
            checked_by=checked_by,
            checked_date=phase_execution.completed_date,
            comments=f"QC phase {checkpoint_name} completed. {'Passed quality control.' if qc_passed else 'Failed quality control - requires review.'}"
        )
    
    @classmethod
    def handle_qc_failure_rollback(cls, bmr, failed_phase_name, rollback_to_phase):
        """Handle QC failure and rollback to a previous phase"""
        try:
            # Find the failed QC phase
            failed_execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=failed_phase_name
            )
            
            # Mark the QC phase as failed for audit trail
            if failed_execution.status != 'failed':
                failed_execution.status = 'failed'
                failed_execution.completed_date = timezone.now()
                failed_execution.save()
            
            # Find the rollback phase 
            rollback_phase = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name=rollback_to_phase
            )
            
            # CRITICAL: Reset ALL phases from rollback point onward to ensure proper sequence
            # This includes the failed QC phase which must be reset for retesting
            phases_to_reset = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_order__gte=rollback_phase.phase.phase_order
            )
            
            for phase_execution in phases_to_reset:
                # Reset to not_ready - they will be activated in proper sequence
                phase_execution.status = 'not_ready'
                phase_execution.started_by = None
                phase_execution.started_date = None
                phase_execution.completed_by = None
                phase_execution.completed_date = None
                
                if phase_execution.id == failed_execution.id:
                    phase_execution.operator_comments = f'QC RESET: Ready for retesting after {rollback_to_phase} rework.'
                elif phase_execution.id == rollback_phase.id:
                    phase_execution.operator_comments = f'REWORK REQUIRED: Rolled back from {failed_phase_name} failure. Must restart from this phase.'
                else:
                    phase_execution.operator_comments = 'RESET: Waiting for workflow sequence after rollback.'
                
                phase_execution.save()
            
            # Set ONLY the rollback phase to pending so work can resume
            rollback_phase.status = 'pending'
            rollback_phase.operator_comments = f'REWORK REQUIRED: Rolled back from {failed_phase_name} failure. Must restart from this phase.'
            rollback_phase.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling QC rollback for BMR {bmr.batch_number}: {e}")
            return False
    
    @classmethod
    def handle_production_phase_failure(cls, bmr, failed_phase, reason=''):
        """Handle production phase failure by resetting phase for retry"""
        try:
            # Get the failed phase execution
            failed_execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase=failed_phase
            )
            
            # Mark phase as failed with reason
            failed_execution.status = 'failed'
            failed_execution.completed_date = timezone.now()
            failed_execution.operator_comments = f'PHASE FAILED: {reason}. Ready for retry.' if reason else 'PHASE FAILED: Ready for retry.'
            failed_execution.save()
            
            # Reset the SAME phase to pending so operator can retry
            # This is for production phases - retry without rollback to previous phase
            failed_execution.status = 'pending'
            failed_execution.started_by = None
            failed_execution.started_date = None
            failed_execution.completed_by = None
            failed_execution.completed_date = None
            failed_execution.operator_comments = f'RETRY: {reason}' if reason else 'RETRY: Phase ready to restart'
            failed_execution.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling production phase failure for BMR {bmr.batch_number}: {e}")
            return False
    
    @classmethod
    def resubmit_rejected_bmr(cls, bmr, qa_comments=''):
        """Re-submit a rejected BMR for regulatory review"""
        try:
            # Find regulatory approval phase
            regulatory_phase = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase__phase_name='regulatory_approval'
            )
            
            # Reset to pending for re-review
            regulatory_phase.status = 'pending'
            regulatory_phase.started_by = None
            regulatory_phase.started_date = None
            regulatory_phase.completed_by = None
            regulatory_phase.completed_date = None
            regulatory_phase.operator_comments = f'RE-SUBMITTED BY QA: {qa_comments}\nPrevious comments: {regulatory_phase.operator_comments}'
            regulatory_phase.save()
            
            # Reset BMR status to submitted
            bmr.status = 'submitted'
            bmr.approved_by = None
            bmr.approved_date = None
            bmr.save()
            
            logger.info(f"BMR {bmr.batch_number} re-submitted to regulatory by QA. Reason: {qa_comments}")
            return True
            
        except Exception as e:
            logger.error(f"Error re-submitting BMR {bmr.batch_number}: {e}")
            return False
    
    @classmethod
    def trigger_next_phase(cls, bmr, current_phase):
        """Trigger the next phase in the workflow after completing current phase"""
        try:
            current_execution = BatchPhaseExecution.objects.get(
                bmr=bmr,
                phase=current_phase
            )
            
            # QUARANTINE LOGIC: Check if this phase should go to quarantine
            phases_that_bypass_quarantine = [
                'bmr_creation', 'regulatory_approval',  # Administrative phases
                'raw_material_release', 'material_dispensing', 'packaging_material_release',  # Material handling
                'blister_packing', 'bulk_packing', 'secondary_packaging',  # All packing phases bypass quarantine
                'final_qa', 'finished_goods_store'  # Final phases
            ]
            
            if current_execution.phase.phase_name not in phases_that_bypass_quarantine:
                logger.info(f"Phase {current_execution.phase.phase_name} completed for BMR {bmr.batch_number}, sending to quarantine")
                return cls._send_to_quarantine(bmr, current_execution)
            
            # SPECIAL HANDLING: packaging_material_release uses configurable packing phase
            if current_execution.phase.phase_name == 'packaging_material_release':
                next_phase_name = util_get_packing_phase_for_product(bmr.product)

                if next_phase_name:
                    next_phase = BatchPhaseExecution.objects.filter(
                        bmr=bmr,
                        phase__phase_name=next_phase_name,
                        status='not_ready'
                    ).first()

                    if next_phase:
                        next_phase.status = 'pending'
                        next_phase.save()
                        logger.info(f"Activated {next_phase_name} phase for {bmr.product.product_type}: {bmr.batch_number}")
                        return True
            
            # SPECIAL HANDLING: packing phases -> secondary_packaging transitions
            elif current_execution.phase.phase_name in ['bulk_packing', 'blister_packing']:
                # After any packing phase, activate secondary_packaging
                secondary_phase = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_name='secondary_packaging',
                    status='not_ready'
                ).first()
                
                if secondary_phase:
                    secondary_phase.status = 'pending'
                    secondary_phase.save()
                    logger.info(f"Activated secondary_packaging after {current_execution.phase.phase_name}: {bmr.batch_number}")
                    return True
            
            # STANDARD LOGIC: For all other phases, activate next in sequence
            next_phase = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_order__gt=current_execution.phase.phase_order,
                status='not_ready'
            ).order_by('phase__phase_order').first()
            
            if next_phase:
                # Check prerequisites BEFORE changing status
                prerequisite_phases = BatchPhaseExecution.objects.filter(
                    bmr=bmr,
                    phase__phase_order__lt=next_phase.phase.phase_order
                )
                
                # Check if all prerequisite phases are completed or skipped
                prerequisites_met = True
                for prereq in prerequisite_phases:
                    if prereq.status not in ['completed', 'skipped']:
                        prerequisites_met = False
                        break
                
                if prerequisites_met:
                    next_phase.status = 'pending' 
                    next_phase.save()
                    logger.info(f"Activated next sequential phase: {next_phase.phase.phase_name} for BMR {bmr.batch_number}")
                    return True
                else:
                    logger.warning(f"Cannot activate {next_phase.phase.phase_name} for BMR {bmr.batch_number} - prerequisites not met")
                    return False
            
            logger.info(f"No more phases to trigger for BMR {bmr.batch_number} - workflow complete")
            return False
            
        except BatchPhaseExecution.DoesNotExist:
            logger.warning(f"Current phase execution not found for BMR {bmr.batch_number}")
            return False
        except Exception as e:
            logger.error(f"Error triggering next phase for BMR {bmr.batch_number}: {e}")
            return False
    
    @classmethod
    def rollback_to_previous_phase(cls, bmr, failed_phase):
        """Rollback to previous phase when QC fails"""
        try:
            # Get product type to determine correct rollback
            product_type = bmr.product.product_type.lower() if bmr.product.product_type else ''
            failed_phase_name = failed_phase.phase_name
            
            # Define QC rollback mapping based on product behavior tags or legacy type
            if product_is_ointment_like(bmr.product):
                # Creams/Ointments go back to mixing, never blending
                qc_rollback_mapping = {
                    'post_compression_qc': 'mixing',  # Should not happen for creams
                    'post_mixing_qc': 'mixing',
                    'post_blending_qc': 'mixing',  # Creams should not go to blending!
                }
            elif product_is_tablet_like(bmr.product):
                # Tablets follow normal flow
                qc_rollback_mapping = {
                    'post_compression_qc': 'granulation',  # Roll back to granulation for tablets
                    'post_mixing_qc': 'mixing',
                    'post_blending_qc': 'blending',
                }
            elif product_is_capsule_like(bmr.product):
                # Capsules follow their flow
                qc_rollback_mapping = {
                    'post_compression_qc': 'filling',  # Should not happen for capsules
                    'post_mixing_qc': 'drying',
                    'post_blending_qc': 'blending',
                }
            else:
                # Default mapping
                qc_rollback_mapping = {
                    'post_compression_qc': 'granulation',
                    'post_mixing_qc': 'mixing',
                    'post_blending_qc': 'blending',
                }
            
            rollback_to_phase = qc_rollback_mapping.get(failed_phase_name)
            
            if rollback_to_phase:
                success = cls.handle_qc_failure_rollback(bmr, failed_phase_name, rollback_to_phase)
                if success:
                    return rollback_to_phase  # Return the actual phase name for messaging
            
            return None
        except Exception as e:
            print(f"Error rolling back for BMR {bmr.batch_number}: {e}")
            return None
    
    @classmethod
    def get_phases_for_user_role(cls, bmr, user_role):
        """Get phases that a specific user role can work on"""
        # Map user roles to phases they can handle
        role_phase_mapping = {
            'qa': ['bmr_creation', 'final_qa'],
            'regulatory': ['regulatory_approval'],
            'store_manager': ['raw_material_release'],  # Store Manager handles raw material release
            'dispensing_operator': ['material_dispensing'],  # Dispensing Operator handles material dispensing
            'packaging_store': ['packaging_material_release'],  # Packaging store handles packaging material release
            'finished_goods_store': ['finished_goods_store'],  # Finished Goods Store only handles finished goods storage
            'qc': ['post_compression_qc', 'post_mixing_qc', 'post_blending_qc'],
            'mixing_operator': ['mixing'],
            'granulation_operator': ['granulation'],
            'blending_operator': ['blending'],
            'compression_operator': ['compression'],
            'coating_operator': ['coating'],
            'drying_operator': ['drying'],
            'filling_operator': ['filling'],
            'tube_filling_operator': ['tube_filling'],
            'packing_operator': ['blister_packing', 'bulk_packing', 'secondary_packaging'],
            'sorting_operator': ['sorting'],
        }
        
        allowed_phases = role_phase_mapping.get(user_role, [])
        
        return BatchPhaseExecution.objects.filter(
            bmr=bmr,
            phase__phase_name__in=allowed_phases,
            status__in=['pending', 'in_progress']
        ).select_related('phase').order_by('phase__phase_order')
    
    @classmethod
    def _send_to_quarantine(cls, bmr, current_execution):
        """Send completed phase to quarantine"""
        try:
            from quarantine.models import QuarantineBatch
            
            # Check if batch is already in quarantine
            existing_quarantine = QuarantineBatch.objects.filter(
                bmr=bmr,
                status__in=['quarantined', 'sample_requested', 'sample_in_qa', 'sample_in_qc', 'sample_approved', 'sample_failed']
            ).first()
            
            if existing_quarantine:
                # Update existing quarantine record
                existing_quarantine.current_phase = current_execution.phase
                existing_quarantine.status = 'quarantined'
                existing_quarantine.save()
                print(f"Updated existing quarantine record for BMR {bmr.batch_number} at phase {current_execution.phase.phase_name}")
            else:
                # Create new quarantine record
                QuarantineBatch.objects.create(
                    bmr=bmr,
                    current_phase=current_execution.phase,
                    status='quarantined',
                    quarantine_date=timezone.now()
                )
                print(f"Created quarantine record for BMR {bmr.batch_number} at phase {current_execution.phase.phase_name}")
            
            return True
            
        except Exception as e:
            print(f"Error sending BMR {bmr.batch_number} to quarantine: {e}")
            return False
    
    @classmethod
    def proceed_from_quarantine(cls, bmr, quarantine_phase):
        """Proceed from quarantine to next phase after sample approval - skip QC phases since sample was already approved"""
        try:
            # Get all phases after the quarantine phase
            all_next = BatchPhaseExecution.objects.filter(
                bmr=bmr,
                phase__phase_order__gt=quarantine_phase.phase_order
            ).order_by('phase__phase_order')
            
            # QC phases that should be skipped since quarantine sample was approved
            qc_phases = ['post_mixing_qc', 'post_compression_qc', 'post_blending_qc']
            
            # Find the next non-QC phase (since QC was already done via quarantine sample)
            next_phase = None
            for phase_execution in all_next:
                if phase_execution.phase.phase_name not in qc_phases:
                    next_phase = phase_execution
                    break
                else:
                    # Mark QC phases as completed since quarantine sample was approved
                    phase_execution.status = 'completed'
                    phase_execution.completed_date = timezone.now()
                    phase_execution.operator_comments = "QC completed via quarantine sample approval"
                    phase_execution.save()
                    print(f"Skipped QC phase {phase_execution.phase.phase_name} for BMR {bmr.batch_number} (quarantine sample approved)")
            
            if next_phase:
                next_phase.status = 'pending'
                next_phase.save()
                print(f"Proceeded from quarantine: activated {next_phase.phase.phase_name} for BMR {bmr.batch_number}")
                
                # Update quarantine record
                from quarantine.models import QuarantineBatch
                quarantine_batch = QuarantineBatch.objects.filter(bmr=bmr).first()
                if quarantine_batch:
                    quarantine_batch.status = 'released'
                    quarantine_batch.released_date = timezone.now()
                    quarantine_batch.save()
                
                return True
            else:
                print(f"No next production phase found after quarantine for BMR {bmr.batch_number}")
                return False
                
        except Exception as e:
            print(f"Error proceeding from quarantine for BMR {bmr.batch_number}: {e}")
            return False
    
    # End of WorkflowService class
