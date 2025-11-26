from django.core.management.base import BaseCommand
from dashboards.models import DashboardPermission

class Command(BaseCommand):
    help = 'Add additional dashboard permissions for admin dashboard sections'

    def handle(self, *args, **options):
        """Create additional dashboard permissions for sidebar sections"""
        
        additional_permissions = [
            {
                'name': 'quarantine_tracking',
                'description': 'Quarantine tracking and management',
                'requires_staff': False,
                'allowed_roles': ['qc', 'quarantine', 'admin']
            },
            {
                'name': 'phase_notifications',
                'description': 'Phase timing alerts and notifications',
                'requires_staff': False,
                'allowed_roles': ['production_manager', 'qc', 'admin'] + [
                    'mixing_operator', 'tube_filling_operator', 'granulation_operator',
                    'blending_operator', 'compression_operator', 'coating_operator',
                    'drying_operator', 'filling_operator', 'sorting_operator',
                    'packing_operator', 'dispensing_operator', 'equipment_operator',
                    'cleaning_operator'
                ]
            },
            {
                'name': 'inventory_management',
                'description': 'Inventory and finished goods store management',
                'requires_staff': False,
                'allowed_roles': ['store_manager', 'finished_goods_store', 'admin']
            },
            {
                'name': 'bmr_tracking',
                'description': 'BMR timeline and tracking dashboard',
                'requires_staff': False,
                'allowed_roles': ['qa', 'production_manager', 'admin']
            },
            {
                'name': 'live_tracking',
                'description': 'Live BMR tracking and monitoring',
                'requires_staff': False,
                'allowed_roles': ['qa', 'production_manager', 'admin']
            },
            {
                'name': 'analytics_metrics',
                'description': 'Production analytics and metrics dashboard',
                'requires_staff': False,
                'allowed_roles': ['production_manager', 'qa', 'admin']
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for config in additional_permissions:
            permission, created = DashboardPermission.objects.get_or_create(
                name=config['name'],
                defaults={
                    'description': config['description'],
                    'requires_staff': config.get('requires_staff', False),
                    'requires_superuser': config.get('requires_superuser', False),
                    'allowed_roles': config['allowed_roles'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created permission: {permission.name}')
                )
            else:
                # Update existing permission if config has changed
                updated = False
                if permission.allowed_roles != config['allowed_roles']:
                    permission.allowed_roles = config['allowed_roles']
                    updated = True
                
                if updated:
                    permission.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated permission: {permission.name}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nAdditional permissions setup complete!\n'
                f'Created: {created_count} permissions\n'
                f'Updated: {updated_count} permissions\n'
            )
        )