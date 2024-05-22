import os

from api.models import CustomUser
from django.core.management.base import BaseCommand
from dotenv import load_dotenv

load_dotenv()


class Command(BaseCommand):
    help = 'Creates a superuser from environment'
    ' variables if no superuser exists.'

    def handle(self, *args, **options):
        if not CustomUser.objects.filter(is_superuser=True).exists():
            CustomUser.objects.create_superuser(
                username=os.getenv('DJANGO_SUPERUSER_USERNAME'),
                email=os.getenv('DJANGO_SUPERUSER_EMAIL'),
                password=os.getenv('DJANGO_SUPERUSER_PASSWORD'),
                first_name=os.getenv('DJANGO_SUPERUSER_FIRST_NAME'),
                last_name=os.getenv('DJANGO_SUPERUSER_LAST_NAME'))
            self.stdout.write(self.style.SUCCESS('Successfully created'
                                                 ' a new superuser'))
        else:
            self.stdout.write(self.style.WARNING('A superuser already exists'))
