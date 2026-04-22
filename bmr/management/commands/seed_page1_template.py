from django.core.management.base import BaseCommand
from django.db import transaction
from bmr.models import BMRTemplate
from bmr.template_models import BMRTemplateSection, BMRTemplateTable, BMRTemplateTableColumn


class Command(BaseCommand):
    help = "Seed Page 1 raw material table, totals row, and signature row into the active BMR template."

    def add_arguments(self, parser):
        parser.add_argument(
            "--slug",
            dest="slug",
            default=None,
            help="Template slug to update (defaults to active template).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        slug = options.get("slug")
        if slug:
            template = BMRTemplate.objects.filter(slug=slug).first()
        else:
            template = BMRTemplate.get_active_template()

        if not template:
            self.stderr.write(self.style.ERROR("No active template found."))
            return

        self.stdout.write(self.style.SUCCESS(f"Using template: {template.name}"))

        # Section 1: Raw Material Table
        raw_section, _ = BMRTemplateSection.objects.get_or_create(
            template=template,
            title="RAW MATERIAL REQUISITION/DISPENSING SHEETS",
            defaults={
                "section_type": "table",
                "page_number": 1,
                "order": 10,
                "columns": 1,
                "is_visible": True,
            },
        )
        raw_section.section_type = "table"
        raw_section.page_number = 1
        raw_section.order = 10
        raw_section.columns = 1
        raw_section.is_visible = True
        raw_section.save()

        raw_table, _ = BMRTemplateTable.objects.get_or_create(
            section=raw_section,
            title="Raw Material Table",
            defaults={
                "data_source": "ingredient_table",
                "is_editable": False,
                "show_row_numbers": True,
            },
        )
        raw_table.data_source = "ingredient_table"
        raw_table.is_editable = False
        raw_table.show_row_numbers = True
        raw_table.save()
        raw_table.columns.all().delete()

        raw_columns = [
            ("Sr. No.", "sr_no"),
            ("Description", "description"),
            ("A.R. No.***", "lots.ar_number"),
            ("Unit Quantity (mg/tablet)", "unit_quantity"),
            ("Overage (mg/tablet)", "overage"),
            ("Total Quantity (mg/tablet)", "total_quantity"),
            ("Total Batch Quantity (Kg)", "total_batch_quantity"),
            ("Lot", "lots.lot_number"),
            ("Quantity Per Lot", "lots.quantity_per_lot"),
            ("Tare Weight (Kg/g)", "lots.tare_weight"),
            ("Gross Weight (Kg/g)", "lots.gross_weight"),
            ("Net Weight (Kg/g)", "lots.net_weight"),
            ("Scale ID.", "lots.scale_id"),
            ("Weighed by***", "lots.weighed_by"),
            ("Checked by***", "lots.checked_by"),
            ("Received by", "lots.received_by"),
        ]
        for idx, (header, source) in enumerate(raw_columns, start=1):
            BMRTemplateTableColumn.objects.create(
                table=raw_table,
                header=header,
                data_source=source,
                order=idx,
                width_percentage=6,
            )

        # Section 2: Totals Row
        totals_section, _ = BMRTemplateSection.objects.get_or_create(
            template=template,
            title="Raw Material Totals",
            defaults={
                "section_type": "table",
                "page_number": 1,
                "order": 20,
                "columns": 1,
                "is_visible": True,
            },
        )
        totals_section.section_type = "table"
        totals_section.page_number = 1
        totals_section.order = 20
        totals_section.columns = 1
        totals_section.is_visible = True
        totals_section.save()

        totals_table, _ = BMRTemplateTable.objects.get_or_create(
            section=totals_section,
            title="Totals",
            defaults={
                "data_source": "ingredient_table_totals_rows",
                "is_editable": False,
                "show_row_numbers": False,
            },
        )
        totals_table.data_source = "ingredient_table_totals_rows"
        totals_table.is_editable = False
        totals_table.show_row_numbers = False
        totals_table.save()
        totals_table.columns.all().delete()

        totals_columns = [
            ("Label", "label"),
            ("Total Unit Quantity", "total_unit_quantity"),
            ("Total Quantity", "total_quantity"),
            ("Total Batch Quantity", "total_batch_quantity"),
        ]
        for idx, (header, source) in enumerate(totals_columns, start=1):
            BMRTemplateTableColumn.objects.create(
                table=totals_table,
                header=header,
                data_source=source,
                order=idx,
                width_percentage=10,
            )

        # Section 3: Signatures Row
        sig_section, _ = BMRTemplateSection.objects.get_or_create(
            template=template,
            title="Signatures",
            defaults={
                "section_type": "table",
                "page_number": 1,
                "order": 30,
                "columns": 1,
                "is_visible": True,
            },
        )
        sig_section.section_type = "table"
        sig_section.page_number = 1
        sig_section.order = 30
        sig_section.columns = 1
        sig_section.is_visible = True
        sig_section.save()

        sig_table, _ = BMRTemplateTable.objects.get_or_create(
            section=sig_section,
            title="Signature Row",
            defaults={
                "data_source": "signature_rows",
                "is_editable": False,
                "show_row_numbers": False,
            },
        )
        sig_table.data_source = "signature_rows"
        sig_table.is_editable = False
        sig_table.show_row_numbers = False
        sig_table.save()
        sig_table.columns.all().delete()

        sig_columns = [
            ("Store In-charge", "store_in_charge"),
            ("Dispensing Supervisor", "dispensing_supervisor"),
            ("QA Officer", "qa_officer"),
        ]
        for idx, (header, source) in enumerate(sig_columns, start=1):
            BMRTemplateTableColumn.objects.create(
                table=sig_table,
                header=header,
                data_source=source,
                order=idx,
                width_percentage=10,
            )

        self.stdout.write(self.style.SUCCESS("Page 1 sections seeded successfully."))
