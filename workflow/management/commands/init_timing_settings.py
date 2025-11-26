from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'This command has been disabled. All timing settings must be configured manually by administrators through Django Admin interface.'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                '⚠️  TIMING INITIALIZATION DISABLED\n\n'
                'This command no longer sets default timing values.\n'
                'System administrators must configure all timing settings\n'
                'through the Django Admin interface.\n\n'
                'To configure timing settings:\n'
                '1. Login to Django Admin\n'
                '2. Go to Workflow > Phase Timing Settings\n'
                '3. Add timing for each phase\n'
                '4. Or use Workflow > Product-Machine Timing Settings\n'
                '   for product-specific timing\n\n'
                'No hard-coded defaults will be applied.'
            )
        )
                created_count += 1
                self.stdout.write(f'✅ Created: {setting_name} = {default_value}')
            else:
                updated_count += 1
                self.stdout.write(f'📋 Exists: {setting_name} = {setting_obj.setting_value}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎯 Timing settings initialized!\n'
                f'Created: {created_count}, Existing: {updated_count}\n'
                f'Configure these settings in Django Admin -> System Timing Settings'
            )
        )

    def _get_description(self, setting_name):
        descriptions = {
            'default_phase_duration_hours': 'Default duration for phases without specific timing settings',
            'warning_threshold_percentage': 'Percentage of expected time to show warning (e.g., 80 = warn at 80%)',
            'overrun_threshold_percentage': 'Percentage of expected time to mark as overrun (e.g., 120 = overrun at 120%)',
            'critical_overrun_hours': 'Hours of overrun to trigger critical alerts',
            'major_overrun_hours': 'Hours of overrun to trigger major alerts',
            'minor_overrun_hours': 'Hours of overrun to trigger minor alerts',
            'warning_time_minutes': 'Minutes remaining to show warning status',
            'urgent_sample_hours': 'Hours after which quality samples become urgent',
            'session_timeout_hours': 'Hours of inactivity before user session timeout',
            'max_breakdown_duration_hours': 'Maximum allowed breakdown duration',
            'max_changeover_duration_hours': 'Maximum allowed changeover duration',
        }
        return descriptions.get(setting_name, f'System setting: {setting_name}')

    def _get_unit(self, setting_name):
        if 'hours' in setting_name:
            return 'hours'
        elif 'minutes' in setting_name:
            return 'minutes'
        elif 'percentage' in setting_name:
            return 'percentage'
        else:
            return 'value'