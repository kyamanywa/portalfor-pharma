from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import CustomUser
from dashboards.models import NotificationAlert, QMSCalibrationRecord, QMSNotificationRule


class Command(BaseCommand):
    help = 'Synchronize calibration due status and create calibration reminders.'

    def handle(self, *args, **options):
        today = timezone.now().date()
        default_days = max((rule.days_before for rule in QMSNotificationRule.objects.filter(trigger_type='calibration_due', is_active=True)), default=30)
        overdue = due = 0
        for record in QMSCalibrationRecord.objects.select_related('owner', 'created_by', 'verified_by').exclude(status='out_of_service'):
            if record.next_due_date and record.next_due_date < today:
                new_status = 'overdue'
                overdue += 1
                self._notify(record, 'calibration_overdue', 'Calibration overdue', f'{record.equipment_id} passed its calibration due date on {record.next_due_date:%d %b %Y}.', 'high')
            elif record.next_due_date and record.next_due_date <= today + timedelta(days=default_days):
                new_status = 'due'
                due += 1
                self._notify(record, 'calibration_due', 'Calibration due soon', f'{record.equipment_id} is due for calibration on {record.next_due_date:%d %b %Y}.', 'medium')
            else:
                new_status = 'in_service'
            if record.status != new_status:
                record.status = new_status
                record.save(update_fields=['status', 'updated_at'])
        self.stdout.write(self.style.SUCCESS(f'Processed {overdue} overdue and {due} due-soon calibration records.'))

    def _notify(self, record, notification_type, title, message, priority):
        recipients = {user.pk for user in (record.owner, record.created_by, record.verified_by) if user}
        for rule in QMSNotificationRule.objects.filter(trigger_type='calibration_due', is_active=True):
            recipients.update(CustomUser.objects.filter(role=rule.role_to_notify, is_active=True).values_list('pk', flat=True))
        for user_id in recipients:
            if NotificationAlert.objects.filter(recipient_id=user_id, notification_type=notification_type, title__contains=record.equipment_id, created_date__date=timezone.now().date()).exists():
                continue
            NotificationAlert.objects.create(recipient_id=user_id, notification_type=notification_type, priority=priority, title=f'{title}: {record.equipment_id}', message=message)
