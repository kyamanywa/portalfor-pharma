from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.core.management import call_command

@receiver(post_migrate)
def load_defaults_after_migrate(sender, **kwargs):
    # Only run for the main app to avoid duplicate calls
    if sender.name == 'workflow':
        try:
            call_command('setup_workflow_templates', verbosity=0)
        except Exception:
            pass
        try:
            call_command('init_system_defaults', verbosity=0)
        except Exception:
            pass
