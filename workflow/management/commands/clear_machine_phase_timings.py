from django.core.management.base import BaseCommand
from workflow.models import PhaseTimingSetting, ProductionPhase


class Command(BaseCommand):
    help = 'Clear PhaseTimingSetting entries for phases that require machines (keep non-machine phases)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show which PhaseTimingSetting entries would be removed without deleting',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Actually perform deletions',
        )

    def handle(self, *args, **options):
        machine_required = [
            'granulation', 'blending', 'compression',
            'coating', 'blister_packing', 'filling', 'mixing', 'tube_filling'
        ]

        self.stdout.write(self.style.SUCCESS('=== Clear PhaseTimingSetting for machine phases ==='))
        dry_run = options['dry_run']
        do_confirm = options['confirm']

        to_delete = []
        for phase_name in machine_required:
            phase = ProductionPhase.objects.filter(phase_name=phase_name).first()
            if not phase:
                continue
            try:
                pts = PhaseTimingSetting.objects.filter(phase=phase).first()
                if pts:
                    to_delete.append((phase, pts))
            except Exception:
                continue

        if not to_delete:
            self.stdout.write('No PhaseTimingSetting entries found for machine phases.')
            return

        self.stdout.write('\nFound PhaseTimingSetting entries for the following machine phases:')
        for phase, pts in to_delete:
            self.stdout.write(f"  - Phase: {phase.phase_name} ({phase.get_phase_name_display()}) -> Setting: {pts.expected_duration_hours}h (id={pts.id})")

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN: No changes will be made. Use --confirm to delete these settings.'))
            return

        if not do_confirm:
            self.stdout.write('\nNo action taken. Re-run with --confirm to delete the above settings, or --dry-run to preview.')
            return

        # Perform deletions
        deleted = 0
        for phase, pts in to_delete:
            try:
                pts.delete()
                deleted += 1
                self.stdout.write(self.style.SUCCESS(f'Deleted PhaseTimingSetting for phase {phase.phase_name} (id={pts.id})'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to delete setting for phase {phase.phase_name}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\nCompleted. Deleted {deleted} PhaseTimingSetting entries.'))
        self.stdout.write(self.style.WARNING('Note: Non-machine phases were left intact.'))
