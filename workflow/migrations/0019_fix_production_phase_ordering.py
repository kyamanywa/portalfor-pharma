# Migration to fix ProductionPhase ordering based on WorkflowTemplate definitions

from django.db import migrations

def fix_production_phase_ordering(apps, schema_editor):
    """Fix ProductionPhase ordering to match WorkflowTemplate definitions"""
    ProductionPhase = apps.get_model('workflow', 'ProductionPhase')
    WorkflowTemplate = apps.get_model('workflow', 'WorkflowTemplate')
    
    # Delete all existing ProductionPhase records to avoid conflicts
    ProductionPhase.objects.all().delete()
    print("✓ Cleared all existing ProductionPhase records")
    
    # Recreate ProductionPhases from WorkflowTemplates
    for template in WorkflowTemplate.objects.filter(is_active=True):
        print(f"\nProcessing template: {template.name} ({template.product_type})")
        
        for template_phase in template.phases.all().order_by('phase_order'):
            production_phase, created = ProductionPhase.objects.get_or_create(
                product_type=template.product_type,
                phase_name=template_phase.phase_name,
                defaults={
                    'phase_order': template_phase.phase_order,
                    'description': template_phase.description,
                    'is_mandatory': template_phase.is_mandatory,
                    'requires_approval': template_phase.requires_approval,
                    'estimated_duration_hours': template_phase.estimated_duration_hours
                }
            )
            
            if created:
                print(f"  ✓ Created {template_phase.phase_order:2d}. {template_phase.phase_name}")
            else:
                print(f"  - Exists {template_phase.phase_order:2d}. {template_phase.phase_name}")
    
    print("\n✓ ProductionPhase ordering fixed based on templates")

def reverse_fix_production_phase_ordering(apps, schema_editor):
    """Reverse operation - just delete all ProductionPhases"""
    ProductionPhase = apps.get_model('workflow', 'ProductionPhase')
    ProductionPhase.objects.all().delete()
    print("✓ Reversed: Deleted all ProductionPhase records")

class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0018_productionphase_description_and_more'),
    ]

    operations = [
        migrations.RunPython(
            fix_production_phase_ordering,
            reverse_fix_production_phase_ordering,
        ),
    ]