"""
Seed bmr_creation and regulatory_approval sections for all product templates.
These phases currently have zero sections → "No sections configured" message.

Run:
    python manage.py seed_admin_phase_sections
    python manage.py seed_admin_phase_sections --dry-run
"""
from django.core.management.base import BaseCommand
from bmr.models import BMRTemplate
from bmr.template_models import BMRTemplateSection

PRODUCT_TYPES = ['ointment', 'capsule', 'tablet']

# Sections to add for bmr_creation phase
BMR_CREATION_SECTIONS = [
    {
        'title': 'BMR Header Information',
        'section_type': 'info',
        'config': {
            'fields': [
                {'label': 'Product Name',        'key': 'product_name',       'type': 'text',   'readonly': True},
                {'label': 'Batch Number',         'key': 'batch_number',       'type': 'text',   'readonly': True},
                {'label': 'Batch Size',           'key': 'batch_size',         'type': 'text',   'readonly': True},
                {'label': 'Manufacturing Date',   'key': 'mfg_date',           'type': 'date',   'readonly': True},
                {'label': 'Expiry Date',          'key': 'exp_date',           'type': 'date',   'readonly': True},
                {'label': 'BMR Revision No.',     'key': 'bmr_revision',       'type': 'text',   'readonly': True},
                {'label': 'MFR Number',           'key': 'mfr_number',         'type': 'text',   'readonly': True},
            ]
        },
        'order': 1,
        'page_number': 1,
    },
    {
        'title': 'QA Sign-Off',
        'section_type': 'signature',
        'config': {
            'fields': [
                {'label': 'Prepared By (QA)',     'key': 'prepared_by',        'type': 'text'},
                {'label': 'Date',                 'key': 'prepared_date',      'type': 'date'},
                {'label': 'Checked By',           'key': 'checked_by',         'type': 'text'},
                {'label': 'Check Date',           'key': 'checked_date',       'type': 'date'},
                {'label': 'Remarks',              'key': 'remarks',            'type': 'textarea'},
            ]
        },
        'order': 2,
        'page_number': 1,
    },
]

# Sections to add for regulatory_approval phase
REGULATORY_APPROVAL_SECTIONS = [
    {
        'title': 'BMR Review Checklist',
        'section_type': 'form',
        'config': {
            'fields': [
                {'label': 'Product specifications reviewed',   'key': 'chk_specs',   'type': 'checkbox'},
                {'label': 'Raw material list verified',        'key': 'chk_rm',      'type': 'checkbox'},
                {'label': 'Manufacturing procedure reviewed',  'key': 'chk_proc',    'type': 'checkbox'},
                {'label': 'In-process controls reviewed',      'key': 'chk_ipc',     'type': 'checkbox'},
                {'label': 'Packaging requirements reviewed',   'key': 'chk_pkg',     'type': 'checkbox'},
                {'label': 'Review Comments',                   'key': 'review_comments', 'type': 'textarea'},
            ]
        },
        'order': 1,
        'page_number': 1,
    },
    {
        'title': 'Regulatory Approval Sign-Off',
        'section_type': 'signature',
        'config': {
            'fields': [
                {'label': 'Reviewed By (Regulatory)',  'key': 'reviewed_by',    'type': 'text'},
                {'label': 'Review Date',               'key': 'review_date',    'type': 'date'},
                {'label': 'Decision',                  'key': 'decision',       'type': 'select',
                 'options': ['Approved', 'Approved with Comments', 'Rejected']},
                {'label': 'Approval Comments',         'key': 'approval_comments', 'type': 'textarea'},
                {'label': 'Signature',                 'key': 'signature',      'type': 'text'},
                {'label': 'Date',                      'key': 'signature_date', 'type': 'date'},
            ]
        },
        'order': 2,
        'page_number': 1,
    },
]

PHASES_TO_SEED = [
    ('bmr_creation',       BMR_CREATION_SECTIONS),
    ('regulatory_approval', REGULATORY_APPROVAL_SECTIONS),
]


class Command(BaseCommand):
    help = 'Seed bmr_creation and regulatory_approval sections for all product templates'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        created = 0
        skipped = 0

        for product_type in PRODUCT_TYPES:
            tpl = BMRTemplate.objects.filter(product_type=product_type).first()
            if not tpl:
                self.stdout.write(self.style.WARNING(f'  No template for product_type="{product_type}" — skipping'))
                continue

            self.stdout.write(self.style.HTTP_INFO(f'\nTemplate: {tpl.name} (pk={tpl.pk})'))

            for phase_name, section_defs in PHASES_TO_SEED:
                exists_count = BMRTemplateSection.objects.filter(
                    template=tpl, phase_name=phase_name
                ).count()
                if exists_count > 0:
                    self.stdout.write(f'  [EXISTS] {phase_name} already has {exists_count} section(s) — skipping')
                    skipped += exists_count
                    continue

                for sdef in section_defs:
                    if dry_run:
                        self.stdout.write(f'  [DRY-RUN] Would create: {phase_name} / {sdef["title"]}')
                        continue
                    BMRTemplateSection.objects.create(
                        template=tpl,
                        title=sdef['title'],
                        section_type=sdef['section_type'],
                        phase_name=phase_name,
                        config=sdef['config'],
                        order=sdef['order'],
                        page_number=sdef['page_number'],
                        is_required=True,
                        is_visible=True,
                        description='',
                    )
                    self.stdout.write(self.style.SUCCESS(f'  [CREATED] {phase_name} / {sdef["title"]}'))
                    created += 1

        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run — no changes saved.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Done. Created {created} section(s), skipped {skipped}.'))
