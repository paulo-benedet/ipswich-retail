from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create the public, unprivileged PoC demo account without overwriting existing accounts."

    def handle(self, *args, **options):
        if not settings.DEMO_ENABLED:
            self.stdout.write("Demo account disabled; no changes made.")
            return
        User = get_user_model()
        user = User.objects.filter(email=settings.DEMO_EMAIL).first()
        if user:
            if (user.is_staff or user.is_superuser or not user.is_active
                    or not user.check_password(settings.DEMO_PASSWORD)):
                raise CommandError("Reserved demo account conflicts with an existing account; no changes made.")
            self.stdout.write("Demo account already available.")
            return
        User.objects.create_user(settings.DEMO_EMAIL, settings.DEMO_PASSWORD)
        self.stdout.write("Public demo account created.")
