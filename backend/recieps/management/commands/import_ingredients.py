import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from recieps.models import Ingredient


class Command(BaseCommand):
    help = 'Imports data from a JSON file into the database'

    def handle(self, *args, **kwargs):
        json_file = 'data/ingredients.json'
        with open(json_file, 'r') as file:
            data = json.load(file)
            for item in data:
                try:
                    product = Ingredient(**item)
                    product.full_clean()
                    product.save()
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f'Error import {item}: '
                                                       f'{e.message_dict}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error import {item}'
                                                       f': {str(e)}'))
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))
