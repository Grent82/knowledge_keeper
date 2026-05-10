from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User, UserRole


class Command(BaseCommand):
    help = "Create an initial owner account for local development."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--password", required=True)
        parser.add_argument("--email", default="")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        email = options["email"]

        if User.objects.filter(username=username).exists():
            raise CommandError(f"User '{username}' already exists.")

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            role=UserRole.OWNER,
            is_staff=True,
            is_superuser=True,
        )
        self.stdout.write(self.style.SUCCESS(f"Created owner account '{user.username}'"))
