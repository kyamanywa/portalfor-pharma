from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import CustomUser
from dashboards.models import NotificationAlert, QMSCAPA, QMSNotificationRule


class Command(BaseCommand):
    help = 'Mark overdue CAPAs and create due-date/escalation notifications.'

    def handle(self, *args, **options):
        today = timezone.now().date()
        rules = list(QMSNotificationRule.objects.filter(trigger_type__in=['capa_overdue'], is_active=True))
        default_days = max([rule.days_before for rule in rules], default=7)
        overdue = 0
        reminders = 0

        capas = QMSCAPA.objects.select_related('qms_action', 'action_owner', 'qa_reviewer').exclude(status__in=['closed', 'cancelled'])
        for capa in capas:
            if capa.target_completion_date and capa.target_completion_date < today:
                if capa.status != 'overdue':
                    capa.status = 'overdue'
                    capa.save(update_fields=['status', 'updated_at'])
                    capa.qms_action.status = 'action_required'
                    capa.qms_action.save(update_fields=['status', 'updated_at'])
                overdue += 1
                self._notify(capa, 'capa_overdue', 'CAPA overdue', f'{capa.capa_number} passed its target date on {capa.target_completion_date:%d %b %Y}.', 'high')
            elif capa.target_completion_date and capa.target_completion_date <= today + timedelta(days=default_days):
                self._notify(capa, 'capa_review_due', 'CAPA due soon', f'{capa.capa_number} is due on {capa.target_completion_date:%d %b %Y}.', 'medium')
                reminders += 1

        self.stdout.write(self.style.SUCCESS(f'Processed {overdue} overdue CAPAs and {reminders} due-soon CAPA reminders.'))

    def _notify(self, capa, notification_type, title, message, priority):
        recipients = set()
        for user in (capa.action_owner, capa.qa_reviewer, capa.created_by):
            if user:
                recipients.add(user.pk)
        for rule in QMSNotificationRule.objects.filter(trigger_type='capa_overdue', is_active=True):
            recipients.update(CustomUser.objects.filter(role=rule.role_to_notify, is_active=True).values_list('pk', flat=True))
        for user_id in recipients:
            if NotificationAlert.objects.filter(recipient_id=user_id, notification_type=notification_type, title__contains=capa.capa_number, created_date__date=timezone.now().date()).exists():
                continue
            NotificationAlert.objects.create(
                recipient_id=user_id,
                notification_type=notification_type,
                priority=priority,
                title=f'{title}: {capa.capa_number}',
                message=message,
            )
