
import json
from django.core.management.base import BaseCommand
from api.models import Ingredient  
from django.core.exceptions import ValidationError

class Command(BaseCommand):
    help = 'Imports data from a JSON file into the database'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file to be imported')

    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']
        with open(json_file, 'r') as file:
            data = json.load(file)
            for item in data:
                try:
                    product = Ingredient(**item)
                    product.full_clean()  # Проверка на валидность данных
                    product.save()
                except ValidationError as e:
                    self.stdout.write(self.style.ERROR(f"Error importing item {item}: {e.message_dict}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Unexpected error importing item {item}: {str(e)}"))
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))