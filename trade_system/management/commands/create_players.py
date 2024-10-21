from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from trade_system.models import AllowedEmail, Player,generate_user_code

class Command(BaseCommand):
    help = 'Create Player entries for allowed emails'

    def handle(self, *args, **kwargs):
        allowed_emails = AllowedEmail.objects.all()

        for allowed_email in allowed_emails:
            # Check if a Player already exists for this AllowedEmail
            if not Player.objects.filter(user=allowed_email).exists():
                # Generate a user code and create the Player
                user_code = generate_user_code(allowed_email.name)
                Player.objects.create(user=allowed_email, user_code=user_code)
                self.stdout.write(self.style.SUCCESS(f"Player created for {allowed_email.email}"))
            else:
                self.stdout.write(self.style.WARNING(f"Player already exists for {allowed_email.email}"))