from django.core.management.base import BaseCommand
from workflow.models import WorkflowTemplate, ProductionPhase, BatchPhaseExecution
from bmr.models import BMR

class Command(BaseCommand):
    help = 'Apply workflow templates to fix existing workflow issues and update BMRs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-type',
            type=str,
            help='Apply template only for specific product type (ointment, tablet, capsule)',
        )
        parser.add_argument(
            '--apply-to-bmrs',
            action='store_true',
            help='Also update existing BMRs with new workflow phases',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        product_type = options['product_type']
        apply_to_bmrs = options['apply_to_bmrs']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get templates to apply
        templates = WorkflowTemplate.objects.filter(is_default=True, is_active=True)
        if product_type:
            templates = templates.filter(product_type=product_type)
        
        if not templates.exists():
            self.stdout.write(self.style.ERROR('No default active templates found'))
            return
        
        for template in templates:
            self.stdout.write(f'\n=== Processing {template.name} ===')
            
            # Show current vs template phases
            current_phases = ProductionPhase.objects.filter(
                product_type=template.product_type
            ).order_by('phase_order')
            template_phases = template.phases.order_by('phase_order')
            
            self.stdout.write(f'Current phases ({current_phases.count()}):')
            for phase in current_phases:
                self.stdout.write(f'  {phase.phase_order}. {phase.phase_name}')
            
            self.stdout.write(f'Template phases ({template_phases.count()}):')
            for phase in template_phases:
                rollback = f' → {phase.rollback_target_order}' if phase.rollback_target_order else ''
                self.stdout.write(f'  {phase.phase_order}. {phase.phase_name}{rollback}')
            
            if not dry_run:
                # Apply template
                try:
                    created_count = template.apply_to_production_phases()
                    self.stdout.write(
                        self.style.SUCCESS(f'Applied template: {created_count} phases created')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error applying template: {e}')
                    )
                    continue
            
            # Handle existing BMRs
            if apply_to_bmrs and not dry_run:
                bmrs = BMR.objects.filter(
                    product__product_type=template.product_type,
                    status='in_production'
                )
                
                self.stdout.write(f'Updating {bmrs.count()} active BMRs...')
                
                for bmr in bmrs:
                    try:
                        self.update_bmr_workflow(bmr, template)
                        self.stdout.write(f'  Updated BMR {bmr.batch_number}')
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  Error updating BMR {bmr.batch_number}: {e}')
                        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN COMPLETE - No changes were made'))
            self.stdout.write('Run without --dry-run to apply changes')
        else:
            self.stdout.write(self.style.SUCCESS('\nWorkflow templates applied successfully!'))
    
    def update_bmr_workflow(self, bmr, template):
        """Update existing BMR with new workflow phases"""
        from workflow.services import WorkflowService
        
        # Get current phase executions
        current_executions = list(BatchPhaseExecution.objects.filter(bmr=bmr))
        
        # Create mapping of completed/in-progress phases
        completed_phases = {
            exec.phase.phase_name: exec.status 
            for exec in current_executions 
            if exec.status in ['completed', 'in_progress', 'failed']
        }
        
        # Delete all phase executions for this BMR
        BatchPhaseExecution.objects.filter(bmr=bmr).delete()
        
        # Reinitialize workflow with new template
        WorkflowService.initialize_workflow_for_bmr(bmr)
        
        # Update status of phases that were already completed
        new_executions = BatchPhaseExecution.objects.filter(bmr=bmr)
        for execution in new_executions:
            phase_name = execution.phase.phase_name
            if phase_name in completed_phases:
                execution.status = completed_phases[phase_name]
                if completed_phases[phase_name] == 'completed':
                    execution.completed_date = timezone.now()
                execution.save()
        
        return new_executions.count()