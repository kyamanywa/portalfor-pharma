from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import CustomUser
from dashboards.models import NotificationAlert, QMSChangeControl, QMSNotificationRule


class Command(BaseCommand):
    help = 'Mark overdue Change Controls and create due-date/escalation notifications.'

    def handle(self, *args, **options):
        today = timezone.now().date()
        rules = QMSNotificationRule.objects.filter(trigger_type__in=['change_control_overdue', 'change_control_due'], is_active=True)
        default_days = max([rule.days_before for rule in rules], default=7)
        overdue = due_soon = 0
        for change in QMSChangeControl.objects.select_related('qms_action', 'owner', 'implementation_owner', 'qa_reviewer').exclude(status__in=['closed', 'cancelled', 'rejected']):
            due_date = change.planned_implementation_date or change.qms_action.due_date
            if not due_date:
                continue
            if due_date < today:
                if change.status != 'overdue':
                    change.status = 'overdue'
                    change.save(update_fields=['status', 'updated_at'])
                    change.qms_action.status = 'action_required'
                    change.qms_action.save(update_fields=['status', 'updated_at'])
                self._notify(change, 'change_control_overdue', 'Change Control overdue', f'{change.change_number} passed its planned implementation date on {due_date:%d %b %Y}.', 'high')
                overdue += 1
            elif due_date <= today + timedelta(days=default_days):
                self._notify(change, 'change_control_due', 'Change Control due soon', f'{change.change_number} is planned for {due_date:%d %b %Y}.', 'medium')
                due_soon += 1
        self.stdout.write(self.style.SUCCESS(f'Processed {overdue} overdue Change Controls and {due_soon} due-soon reminders.'))

    def _notify(self, change, notification_type, title, message, priority):
        recipients = {user.pk for user in (change.owner, change.implementation_owner, change.qa_reviewer, change.created_by) if user}
        for rule in QMSNotificationRule.objects.filter(trigger_type__in=['change_control_overdue', 'change_control_due'], is_active=True):
            recipients.update(CustomUser.objects.filter(role=rule.role_to_notify, is_active=True).values_list('pk', flat=True))
        for user_id in recipients:
            if NotificationAlert.objects.filter(recipient_id=user_id, notification_type=notification_type, title__contains=change.change_number, created_date__date=timezone.now().date()).exists():
                continue
            NotificationAlert.objects.create(recipient_id=user_id, notification_type=notification_type, priority=priority, title=f'{title}: {change.change_number}', message=message)
