from django.core.management.base import BaseCommand
from workflow.models import WorkflowTemplate, WorkflowTemplatePhase

class Command(BaseCommand):
    help = 'Initialize default workflow templates for all product types'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing templates',
        )

    def handle(self, *args, **options):
        overwrite = options['overwrite']
        
        # Define standard workflow templates
        templates = {
            'ointment': {
                'name': 'Standard Ointment Workflow',
                'description': 'Standard workflow for ointment production',
                'phases': [
                    (1, 'bmr_creation', 'BMR Creation', True, False, 1.0),
                    (2, 'regulatory_approval', 'Regulatory Approval', True, True, 24.0),
                    (3, 'raw_material_release', 'Raw Material Release', True, False, 2.0),
                    (4, 'material_dispensing', 'Material Dispensing', True, False, 3.0),
                    (5, 'mixing', 'Mixing', True, False, 6.0),
                    (6, 'post_mixing_qc', 'Post-Mixing QC', True, True, 2.0, 5),  # Rollback to mixing
                    (7, 'tube_filling', 'Tube Filling', True, False, 8.0),
                    (8, 'packaging_material_release', 'Packaging Material Release', True, False, 1.0),
                    (9, 'secondary_packaging', 'Secondary Packaging', True, False, 4.0),
                    (10, 'final_qa', 'Final QA', True, True, 3.0, None, 9),  # QC rollback: None, QA rollback: secondary_packaging (9)
                    (11, 'finished_goods_store', 'Finished Goods Store', True, False, 1.0),
                ]
            },
            'tablet': {
                'name': 'Standard Tablet Workflow',
                'description': 'Standard workflow for tablet production (normal)',
                'phases': [
                    (1, 'bmr_creation', 'BMR Creation', True, False, 1.0),
                    (2, 'regulatory_approval', 'Regulatory Approval', True, True, 24.0),
                    (3, 'raw_material_release', 'Raw Material Release', True, False, 2.0),
                    (4, 'material_dispensing', 'Material Dispensing', True, False, 3.0),
                    (5, 'granulation', 'Granulation', True, False, 8.0),
                    (6, 'blending', 'Blending', True, False, 6.0),
                    (7, 'compression', 'Compression', True, False, 10.0),
                    (8, 'post_compression_qc', 'Post-Compression QC', True, True, 2.0, 6),  # Rollback to blending
                    (9, 'sorting', 'Sorting', True, False, 4.0),
                    (10, 'coating', 'Coating', False, False, 8.0),  # Optional phase
                    (11, 'packaging_material_release', 'Packaging Material Release', True, False, 1.0),
                    (12, 'blister_packing', 'Blister Packing', True, False, 6.0),
                    (13, 'secondary_packaging', 'Secondary Packaging', True, False, 4.0),
                    (14, 'final_qa', 'Final QA', True, True, 3.0, None, 13),  # QC rollback: None, QA rollback: secondary_packaging (13)
                    (15, 'finished_goods_store', 'Finished Goods Store', True, False, 1.0),
                ]
            },
            'tablet_type_2': {
                'name': 'Tablet Type 2 Workflow',
                'description': 'Workflow for tablet type 2 (bulk packing, no blister)',
                'phases': [
                    (1, 'bmr_creation', 'BMR Creation', True, False, 1.0),
                    (2, 'regulatory_approval', 'Regulatory Approval', True, True, 24.0),
                    (3, 'raw_material_release', 'Raw Material Release', True, False, 2.0),
                    (4, 'material_dispensing', 'Material Dispensing', True, False, 3.0),
                    (5, 'granulation', 'Granulation', True, False, 8.0),
                    (6, 'blending', 'Blending', True, False, 6.0),
                    (7, 'compression', 'Compression', True, False, 10.0),
                    (8, 'post_compression_qc', 'Post-Compression QC', True, True, 2.0, 6),  # Rollback to blending
                    (9, 'sorting', 'Sorting', True, False, 4.0),
                    (10, 'coating', 'Coating', False, False, 8.0),  # Optional phase
                    (11, 'packaging_material_release', 'Packaging Material Release', True, False, 1.0),
                    (12, 'bulk_packing', 'Bulk Packing', True, False, 4.0),
                    (13, 'secondary_packaging', 'Secondary Packaging', True, False, 4.0),
                    (14, 'final_qa', 'Final QA', True, True, 3.0, None, 13),  # QC rollback: None, QA rollback: secondary_packaging (13)
                    (15, 'finished_goods_store', 'Finished Goods Store', True, False, 1.0),
                ]
            },
            'capsule': {
                'name': 'Standard Capsule Workflow', 
                'description': 'Standard workflow for capsule production',
                'phases': [
                    (1, 'bmr_creation', 'BMR Creation', True, False, 1.0),
                    (2, 'regulatory_approval', 'Regulatory Approval', True, True, 24.0),
                    (3, 'raw_material_release', 'Raw Material Release', True, False, 2.0),
                    (4, 'material_dispensing', 'Material Dispensing', True, False, 3.0),
                    (5, 'drying', 'Drying', True, False, 12.0),
                    (6, 'blending', 'Blending', True, False, 6.0),
                    (7, 'post_blending_qc', 'Post-Blending QC', True, True, 2.0, 6),  # Rollback to blending
                    (8, 'filling', 'Filling', True, False, 8.0),
                    (9, 'sorting', 'Sorting', True, False, 4.0),
                    (10, 'packaging_material_release', 'Packaging Material Release', True, False, 1.0),
                    (11, 'blister_packing', 'Blister Packing', True, False, 6.0),
                    (12, 'secondary_packaging', 'Secondary Packaging', True, False, 4.0),
                    (13, 'final_qa', 'Final QA', True, True, 3.0, None, 12),  # QC rollback: None, QA rollback: secondary_packaging (12)
                    (14, 'finished_goods_store', 'Finished Goods Store', True, False, 1.0),
                ]
            }
        }
        
        created_count = 0
        updated_count = 0
        
        for product_type, template_data in templates.items():
            # Check if template exists
            template, created = WorkflowTemplate.objects.get_or_create(
                product_type=product_type,
                name=template_data['name'],
                defaults={
                    'description': template_data['description'],
                    'is_active': True,
                    'is_default': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template.name}')
                )
            elif overwrite:
                template.description = template_data['description']
                template.is_active = True
                template.is_default = True
                template.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated template: {template.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Template already exists: {template.name} (use --overwrite to update)')
                )
                continue
            
            # Clear existing phases if overwriting
            if overwrite or created:
                template.phases.all().delete()
            
            # Create phases
            phases_created = 0
            for phase_data in template_data['phases']:
                # Default values
                qc_rollback = None
                qa_rollback = None
                duration = 0
                
                if len(phase_data) >= 8:
                    # Format: order, name, description, mandatory, approval, duration, qc_rollback, qa_rollback
                    order, name, description, mandatory, approval, duration, qc_rollback, qa_rollback = phase_data[:8]
                elif len(phase_data) == 7:
                    # Format: order, name, description, mandatory, approval, duration, qc_rollback
                    order, name, description, mandatory, approval, duration, qc_rollback = phase_data[:7]
                elif len(phase_data) == 6:
                    # Format: order, name, description, mandatory, approval, qc_rollback
                    order, name, description, mandatory, approval, qc_rollback = phase_data[:6]
                else:
                    # Format: order, name, description, mandatory, approval
                    order, name, description, mandatory, approval = phase_data[:5]
                
                WorkflowTemplatePhase.objects.create(
                    template=template,
                    phase_order=order,
                    phase_name=name,
                    description=description,
                    is_mandatory=mandatory,
                    requires_approval=approval,
                    estimated_duration_hours=duration,
                    rollback_target_order=qc_rollback,
                    qa_rollback_target_order=qa_rollback
                )
                phases_created += 1
            
            self.stdout.write(f'  → Created {phases_created} phases')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {created_count} templates created, {updated_count} templates updated'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                'Templates are ready! Go to Django Admin → Workflow → Workflow Templates to manage them.'
            )
        )