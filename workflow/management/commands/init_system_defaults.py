from django.core.management.base import BaseCommand
from workflow.models import SystemTimingSettings

class Command(BaseCommand):
    help = 'Initialize all default system settings for admin management'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing settings with new values',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Initializing System Default Settings ==='))

        # Define all default settings found throughout the system
        default_settings = [
            # Phase Duration Settings
            {
                'setting_name': 'default_machine_phase_duration_hours',
                'setting_value': 4.0,
                'description': 'Default duration for machine-based phases (granulation, blending, compression, etc.)',
                'unit': 'hours'
            },
            {
                'setting_name': 'default_non_machine_phase_duration_hours', 
                'setting_value': 0.17,
                'description': 'Default duration for non-machine phases (10 minutes for packaging, material release, etc.)',
                'unit': 'hours'
            },
            {
                'setting_name': 'system_error_fallback_hours',
                'setting_value': 8.0,
                'description': 'Fallback duration when timing system encounters errors',
                'unit': 'hours'
            },
            
            # Warning and Alert Thresholds
            {
                'setting_name': 'default_warning_threshold_percent',
                'setting_value': 20,
                'description': 'Default warning threshold percentage for phase duration alerts',
                'unit': 'percentage'
            },
            {
                'setting_name': 'warning_threshold_percentage',
                'setting_value': 80.0,
                'description': 'System warning threshold percentage (warn at 80% of expected time)',
                'unit': 'percentage'
            },
            {
                'setting_name': 'overrun_threshold_percentage',
                'setting_value': 120.0,
                'description': 'System overrun threshold percentage (overrun at 120% of expected time)',
                'unit': 'percentage'
            },
            {
                'setting_name': 'critical_overrun_percentage',
                'setting_value': 150.0,
                'description': 'Critical overrun threshold percentage (critical alert at 150% of expected time)',
                'unit': 'percentage'
            },
            
            # Time-based Alerts
            {
                'setting_name': 'warning_time_minutes',
                'setting_value': 30.0,
                'description': 'Minutes remaining before showing warning status',
                'unit': 'minutes'
            },
            {
                'setting_name': 'critical_warning_minutes',
                'setting_value': 10.0,
                'description': 'Minutes remaining before showing critical warning',
                'unit': 'minutes'
            },
            
            # Quality and Sample Management
            {
                'setting_name': 'urgent_sample_hours',
                'setting_value': 24.0,
                'description': 'Hours after which quality samples become urgent',
                'unit': 'hours'
            },
            {
                'setting_name': 'sample_retention_days',
                'setting_value': 30,
                'description': 'Days to retain quality samples',
                'unit': 'days'
            },
            
            # Session and System Settings  
            {
                'setting_name': 'session_timeout_hours',
                'setting_value': 8.0,
                'description': 'Hours of inactivity before user session timeout',
                'unit': 'hours'
            },
            {
                'setting_name': 'session_warning_minutes',
                'setting_value': 15.0,
                'description': 'Minutes before session timeout to show warning',
                'unit': 'minutes'
            },
            
            # Machine and Breakdown Settings
            {
                'setting_name': 'max_breakdown_duration_hours',
                'setting_value': 4.0,
                'description': 'Maximum allowed breakdown duration before escalation',
                'unit': 'hours'
            },
            {
                'setting_name': 'max_changeover_duration_hours',
                'setting_value': 2.0,
                'description': 'Maximum allowed changeover duration before alert',
                'unit': 'hours'
            },
            {
                'setting_name': 'machine_maintenance_interval_days',
                'setting_value': 30,
                'description': 'Days between scheduled machine maintenance',
                'unit': 'days'
            },
            
            # Dashboard and Notification Settings
            {
                'setting_name': 'dashboard_refresh_seconds',
                'setting_value': 30,
                'description': 'Seconds between automatic dashboard refreshes',
                'unit': 'seconds'
            },
            {
                'setting_name': 'notification_batch_size',
                'setting_value': 50,
                'description': 'Maximum notifications to show per page',
                'unit': 'count'
            },
            {
                'setting_name': 'recent_activity_days',
                'setting_value': 7,
                'description': 'Days to show in recent activity feeds',
                'unit': 'days'
            },
            
            # Audit and Compliance Settings
            {
                'setting_name': 'audit_trail_retention_days',
                'setting_value': 2555,
                'description': 'Days to retain audit trail records (7 years for pharmaceutical compliance)',
                'unit': 'days'
            },
            {
                'setting_name': 'batch_record_retention_years',
                'setting_value': 7,
                'description': 'Years to retain batch manufacturing records',
                'unit': 'years'
            },
            
            # Production Planning Settings
            {
                'setting_name': 'max_concurrent_batches',
                'setting_value': 10,
                'description': 'Maximum number of concurrent batches in production',
                'unit': 'count'
            },
            {
                'setting_name': 'production_planning_horizon_days',
                'setting_value': 30,
                'description': 'Days ahead to plan production schedules',
                'unit': 'days'
            }
        ]

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for setting_data in default_settings:
            setting_name = setting_data['setting_name']
            
            try:
                setting_obj, created = SystemTimingSettings.objects.get_or_create(
                    setting_name=setting_name,
                    defaults={
                        'setting_value': setting_data['setting_value'],
                        'description': setting_data['description'],
                        'unit': setting_data['unit']
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Created: {setting_name} = {setting_data["setting_value"]} {setting_data["unit"]}')
                    )
                elif options['update_existing']:
                    setting_obj.setting_value = setting_data['setting_value']
                    setting_obj.description = setting_data['description']
                    setting_obj.unit = setting_data['unit']
                    setting_obj.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'🔄 Updated: {setting_name} = {setting_data["setting_value"]} {setting_data["unit"]}')
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.HTTP_INFO(f'📋 Exists: {setting_name} = {setting_obj.setting_value} {setting_obj.unit}')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error with {setting_name}: {str(e)}')
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Summary ==='))
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Updated: {updated_count}')
        self.stdout.write(f'Skipped: {skipped_count}')
        self.stdout.write('')
        
        if created_count > 0 or updated_count > 0:
            self.stdout.write(self.style.SUCCESS('✅ System settings initialized successfully!'))
            self.stdout.write('')
            self.stdout.write('🔧 To manage these settings:')
            self.stdout.write('1. Login to Django Admin')
            self.stdout.write('2. Go to "Workflow" → "System Timing Settings"')
            self.stdout.write('3. Edit any setting values as needed')
            self.stdout.write('4. Changes take effect immediately')
        else:
            self.stdout.write(self.style.HTTP_INFO('ℹ️  All settings already exist. Use --update-existing to force update.'))