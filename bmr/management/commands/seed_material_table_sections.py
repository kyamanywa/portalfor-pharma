"""
Management command: seed_material_table_sections
Adds 'raw_material_release' and 'material_dispensing' material_table sections
to all seeded BMR templates (ointment, capsule, tablet).

Run with:
    python manage.py seed_material_table_sections
"""
from django.core.management.base import BaseCommand
from bmr.models import BMRTemplate
from bmr.template_models import BMRTemplateSection


TEMPLATES = [
    # (product_type, expected_pk_hint) — pk is just informational
    ('ointment', 4),
    ('capsule',  5),
    ('tablet',   7),
]

PHASE_SECTIONS = [
    {
        'phase_name':    'raw_material_release',
        'title':         'Raw Material Store Release',
        'section_type':  'material_table',
        'config':        {'mode': 'store_release'},
        'order':         1,
        'page_number':   1,
        'is_required':   True,
    },
    {
        'phase_name':    'material_dispensing',
        'title':         'Material Dispensing Record',
        'section_type':  'material_table',
        'config':        {'mode': 'dispensing'},
        'order':         1,
        'page_number':   1,
        'is_required':   True,
    },
    {
        'phase_name':    'packaging_material_release',
        'title':         'Packaging Material Store Release',
        'section_type':  'material_table',
        'config':        {'mode': 'store_release'},
        'order':         1,
        'page_number':   1,
        'is_required':   True,
    },
]


class Command(BaseCommand):
    help = 'Seed material_table sections for raw_material_release and material_dispensing phases'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be created without actually saving.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        created_total = 0
        skipped_total = 0

        for product_type, pk_hint in TEMPLATES:
            tpl = BMRTemplate.objects.filter(product_type=product_type).first()
            if not tpl:
                self.stdout.write(
                    self.style.WARNING(
                        f'  [SKIP] No BMRTemplate found for product_type="{product_type}" (expected pk≈{pk_hint})'
                    )
                )
                continue

            self.stdout.write(
                self.style.HTTP_INFO(
                    f'\nTemplate pk={tpl.pk}  product_type="{product_type}"  name="{tpl.name}"'
                )
            )

            for section_def in PHASE_SECTIONS:
                phase_name = section_def['phase_name']
                exists = BMRTemplateSection.objects.filter(
                    template=tpl,
                    phase_name=phase_name,
                    section_type='material_table',
                ).exists()

                if exists:
                    self.stdout.write(f'    [EXISTS] {phase_name} material_table section — skipping')
                    skipped_total += 1
                    continue

                if dry_run:
                    self.stdout.write(
                        f'    [DRY-RUN] Would create: {phase_name} — {section_def["title"]}'
                    )
                    continue

                BMRTemplateSection.objects.create(
                    template=tpl,
                    title=section_def['title'],
                    section_type=section_def['section_type'],
                    phase_name=section_def['phase_name'],
                    config=section_def['config'],
                    order=section_def['order'],
                    page_number=section_def['page_number'],
                    is_required=section_def['is_required'],
                    is_visible=True,
                    description='',
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'    [CREATED] {phase_name} → section_type=material_table  mode={section_def["config"]["mode"]}'
                    )
                )
                created_total += 1

        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run complete — no changes saved.'))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Done. Created {created_total} section(s), skipped {skipped_total} existing.'
                )
            )
