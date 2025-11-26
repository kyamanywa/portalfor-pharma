from django.core.management.base import BaseCommand
from workflow.models import ProductionPhase, PhaseTimingSetting
from products.models import Product

class Command(BaseCommand):
    help = 'Guide administrators to configure phase timing settings through Django admin'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🕐 PHASE TIMING CONFIGURATION GUIDE'))
        self.stdout.write('=' * 60)
        
        # Count phases without timing configuration
        phases_without_timing = ProductionPhase.objects.filter(
            timing_setting__isnull=True
        ).count()
        
        total_phases = ProductionPhase.objects.count()
        configured_phases = total_phases - phases_without_timing
        
        self.stdout.write(f'📊 Configuration Status:')
        self.stdout.write(f'  • Total Phases: {total_phases}')
        self.stdout.write(f'  • Configured: {configured_phases}')
        self.stdout.write(f'  • Needs Configuration: {phases_without_timing}')
        
        if phases_without_timing > 0:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('⚠️  PHASES NEEDING TIMING CONFIGURATION:'))
            self.stdout.write('')
            
            unconfigured_phases = ProductionPhase.objects.filter(
                timing_setting__isnull=True
            ).order_by('product_type', 'phase_order')
            
            for phase in unconfigured_phases:
                self.stdout.write(
                    f'  • {phase.get_product_type_display()} - '
                    f'{phase.get_phase_name_display()} (Order: {phase.phase_order})'
                )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('📋 HOW TO CONFIGURE TIMING SETTINGS:'))
        self.stdout.write('')
        self.stdout.write('1. Login to Django Admin Panel:')
        self.stdout.write('   http://your-server:8000/admin/')
        self.stdout.write('')
        self.stdout.write('2. Navigate to "Workflow" section')
        self.stdout.write('')
        self.stdout.write('3. Choose one of these options:')
        self.stdout.write('')
        self.stdout.write('   🎯 OPTION A: Basic Phase Timing')
        self.stdout.write('   • Click "Phase Timing Settings"')
        self.stdout.write('   • Click "Add Phase Timing Setting"')
        self.stdout.write('   • Select Phase')
        self.stdout.write('   • Set Expected Duration (hours)')
        self.stdout.write('   • Set Warning Threshold (percentage)')
        self.stdout.write('   • Save')
        self.stdout.write('')
        self.stdout.write('   🎯 OPTION B: Advanced Product-Machine Timing')
        self.stdout.write('   • Click "Product-Machine Timing Settings"')
        self.stdout.write('   • Click "Add Product-Machine Timing Setting"')
        self.stdout.write('   • Select Product + Machine + Phase combination')
        self.stdout.write('   • Set Expected Duration (hours)')
        self.stdout.write('   • Set Warning Threshold (percentage)')
        self.stdout.write('   • Save')
        self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('🔧 EXAMPLE TIMING CONFIGURATIONS:'))
        self.stdout.write('')
        self.stdout.write('Typical pharmaceutical phase durations:')
        self.stdout.write('  • BMR Creation: 0.5 hours')
        self.stdout.write('  • Regulatory Approval: 24-48 hours')
        self.stdout.write('  • Material Dispensing: 1-2 hours')
        self.stdout.write('  • Mixing: 2-4 hours')
        self.stdout.write('  • Granulation: 4-6 hours')
        self.stdout.write('  • Blending: 2-3 hours')
        self.stdout.write('  • Compression: 4-8 hours')
        self.stdout.write('  • Coating: 6-8 hours')
        self.stdout.write('  • QC Testing: 2-4 hours')
        self.stdout.write('  • Packaging: 2-4 hours')
        self.stdout.write('')
        self.stdout.write('⚠️  WARNING THRESHOLDS:')
        self.stdout.write('  • Typical: 80% (warning at 80% of expected time)')
        self.stdout.write('  • Critical phases: 90% (late warning)')
        self.stdout.write('  • Fast phases: 70% (early warning)')
        self.stdout.write('')
        
        if phases_without_timing == 0:
            self.stdout.write(self.style.SUCCESS('✅ ALL PHASES HAVE TIMING CONFIGURATION!'))
        else:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ {phases_without_timing} phases still need timing configuration.'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    '   System will not work properly until all phases have timing settings.'
                )
            )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🎯 QUICK SETUP COMMANDS:'))
        self.stdout.write('')
        self.stdout.write('To see phases needing configuration:')
        self.stdout.write('  python manage.py configure_timing_guide')
        self.stdout.write('')
        self.stdout.write('To clear any existing hard-coded timing:')
        self.stdout.write('  python manage.py clear_machine_phase_timings')
        self.stdout.write('')
        self.stdout.write('=' * 60)