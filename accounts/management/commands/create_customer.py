from getpass import getpass
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email


class Command(BaseCommand):
    help = "Create an existing customer account with a securely prompted password."

    def add_arguments(self, parser):
        parser.add_argument("email")

    def handle(self, *args, **options):
        User = get_user_model()
        email = User.objects.normalize_email(options["email"])
        try:
            validate_email(email)
        except ValidationError as error:
            raise CommandError("Enter a valid email address.") from error
        if User.objects.filter(email=email).exists():
            raise CommandError("An account with that email already exists.")
        password = getpass("Password: ")
        if password != getpass("Password (again): "):
            raise CommandError("Passwords do not match.")
        try:
            validate_password(password, User(email=email))
        except ValidationError as error:
            raise CommandError("; ".join(error.messages)) from error
        User.objects.create_user(email=email, password=password)
        self.stdout.write(self.style.SUCCESS("Customer account created."))
