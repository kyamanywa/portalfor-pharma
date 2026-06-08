"""
Management command to populate BMR Issuance Logs from existing BMRs
Creates product-based logs with batch entries
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count
from bmr.models import BMR, BMRIssuanceLog, BMRIssuanceLogEntry
from accounts.models import CustomUser
from products.models import Product


class Command(BaseCommand):
    help = 'Populate BMR Issuance Logs from existing BMRs (product-based with batch entries)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Delete existing logs and recreate',
        )

    def handle(self, *args, **options):
        overwrite = options['overwrite']
        
        if overwrite:
            # Delete all existing logs and entries
            BMRIssuanceLogEntry.objects.all().delete()
            BMRIssuanceLog.objects.all().delete()
            self.stdout.write(self.style.WARNING('Deleted all existing issuance logs and entries'))
        
        # Get all BMRs grouped by product
        bmrs = BMR.objects.select_related('product', 'created_by').all().order_by('product', 'created_date')
        
        # Get QA users for signing
        qa_users = CustomUser.objects.filter(role='qa', is_active=True)
        if not qa_users.exists():
            self.stdout.write(self.style.WARNING('No QA users found. Using BMR creator as default signer.'))
        
        self.stdout.write(f'\nProcessing {bmrs.count()} BMRs...\n')
        
        logs_created = 0
        entries_created = 0
        errors = 0
        
        # Group BMRs by product
        from collections import defaultdict
        bmrs_by_product = defaultdict(list)
        for bmr in bmrs:
            bmrs_by_product[bmr.product].append(bmr)
        
        self.stdout.write(f'Found {len(bmrs_by_product)} products with BMRs\n')
        
        # Process each product
        for product, product_bmrs in bmrs_by_product.items():
            try:
                # Get or create product-level issuance log
                log, created = BMRIssuanceLog.objects.get_or_create(
                    product=product
                )
                
                if created:
                    logs_created += 1
                    self.stdout.write(f'\n📦 Created log for: {product.product_name}')
                else:
                    self.stdout.write(f'\n📦 Found existing log for: {product.product_name}')
                
                # Create entries for each batch
                for bmr in product_bmrs:
                    try:
                        # Check if entry already exists
                        if BMRIssuanceLogEntry.objects.filter(bmr=bmr).exists():
                            self.stdout.write(f'  ⏭️  Skipped batch {bmr.batch_number} (entry exists)')
                            continue
                        
                        # Determine issue date
                        issue_date = bmr.approved_date.date() if bmr.approved_date else bmr.created_date.date()
                        
                        # Determine QA user
                        issued_by = bmr.approved_by or bmr.created_by
                        if not issued_by or issued_by.role != 'qa':
                            issued_by = qa_users.first() if qa_users.exists() else bmr.created_by
                        
                        # Create entry
                        entry = BMRIssuanceLogEntry.objects.create(
                            issuance_log=log,
                            bmr=bmr,
                            issue_date=issue_date,
                            issued_by=issued_by,
                            issued_by_signature=issued_by.get_full_name() if issued_by else 'System',
                            issued_by_date=bmr.approved_date or bmr.created_date
                        )
                        
                        # Populate active ingredients
                        entry.populate_active_ingredients()
                        entry.save()
                        
                        entries_created += 1
                        self.stdout.write(f'  ✅ Entry #{entry.entry_number}: Batch {bmr.batch_number}')
                        
                    except Exception as e:
                        errors += 1
                        self.stdout.write(self.style.ERROR(f'  ❌ Error creating entry for {bmr.batch_number}: {str(e)}'))
                
            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(f'❌ Error processing product {product.product_name}: {str(e)}'))
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✅ Product Logs Created: {logs_created}'))
        self.stdout.write(self.style.SUCCESS(f'✅ Batch Entries Created: {entries_created}'))
        if errors > 0:
            self.stdout.write(self.style.ERROR(f'❌ Errors: {errors}'))
        self.stdout.write('='*60)
        
        self.stdout.write(self.style.SUCCESS(f'\n🎉 BMR Issuance Logs populated successfully!'))
        self.stdout.write(f'   View them at: /bmr/issuance-logs/')

