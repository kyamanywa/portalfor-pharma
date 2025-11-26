from django.core.management.base import BaseCommand
from dashboards.models import DashboardPermission

class Command(BaseCommand):
    help = 'Initialize default dashboard permissions'

    def handle(self, *args, **options):
        """Create default dashboard permissions"""
        
        permissions_config = [
            {
                'name': 'admin_dashboard',
                'description': 'Main administrative dashboard with system overview',
                'requires_staff': True,  # Keep staff access for operational oversight
                'allowed_roles': ['admin']
            },
            {
                'name': 'system_logs',
                'description': 'System log viewer for monitoring and troubleshooting',
                'requires_superuser': True,  # Changed from requires_staff
                'allowed_roles': []  # Removed 'admin' role
            },
            {
                'name': 'user_management',
                'description': 'User account and role management',
                'requires_superuser': True,
                'allowed_roles': []
            },
            {
                'name': 'machine_management',
                'description': 'Production equipment configuration and management',
                'requires_superuser': True,
                'allowed_roles': []
            },
            {
                'name': 'inventory',
                'description': 'Raw materials and stock management',
                'requires_superuser': True,
                'allowed_roles': []
            },
            {
                'name': 'quality_control',
                'description': 'QC standards and procedure management',
                'requires_superuser': True,
                'allowed_roles': []
            },
            {
                'name': 'system_health',
                'description': 'Server performance and system health monitoring',
                'requires_superuser': True,
                'allowed_roles': []
            },
            {
                'name': 'qa_dashboard',
                'description': 'Quality assurance dashboard and BMR management',
                'requires_staff': False,
                'allowed_roles': ['qa', 'admin']
            },
            {
                'name': 'production_manager',
                'description': 'Production planning and oversight dashboard',
                'requires_staff': False,
                'allowed_roles': ['production_manager', 'admin']
            },
            {
                'name': 'store_dashboard',
                'description': 'Store management and raw material release',
                'requires_staff': False,
                'allowed_roles': ['store_manager', 'admin']
            },
            {
                'name': 'qc_dashboard',
                'description': 'Quality control testing and approvals',
                'requires_staff': False,
                'allowed_roles': ['qc', 'admin']
            },
            {
                'name': 'regulatory_dashboard',
                'description': 'Regulatory compliance and BMR approvals',
                'requires_staff': False,
                'allowed_roles': ['regulatory', 'admin']
            },
            {
                'name': 'operator_dashboard',
                'description': 'Production operator task management',
                'requires_staff': False,
                'allowed_roles': [
                    'mixing_operator', 'tube_filling_operator', 'granulation_operator',
                    'blending_operator', 'compression_operator', 'coating_operator',
                    'drying_operator', 'filling_operator', 'sorting_operator',
                    'packing_operator', 'dispensing_operator', 'equipment_operator',
                    'cleaning_operator', 'admin'
                ]
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for config in permissions_config:
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
                if permission.description != config['description']:
                    permission.description = config['description']
                    updated = True
                if permission.requires_staff != config.get('requires_staff', False):
                    permission.requires_staff = config.get('requires_staff', False)
                    updated = True
                if permission.requires_superuser != config.get('requires_superuser', False):
                    permission.requires_superuser = config.get('requires_superuser', False)
                    updated = True
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
                f'\nPermission initialization complete!\n'
                f'Created: {created_count} permissions\n'
                f'Updated: {updated_count} permissions\n'
                f'\nYou can now manage dashboard permissions from Django Admin:\n'
                f'Admin → Dashboard Permissions'
            )
        )