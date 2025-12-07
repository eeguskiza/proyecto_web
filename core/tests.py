import os
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from .models import Character, Species


class LoadDataCommandTests(TestCase):
    def test_load_data_json_only_is_idempotent(self):
        """El comando carga datos desde JSON y no duplica registros en sucesivas ejecuciones."""
        with patch.dict(os.environ, {"LOAD_SWAPI_ENABLED": "false"}):
            call_command("load_data", "--skip-planets", "--skip-swapi")

        first_counts = (Character.objects.count(), Species.objects.count())
        self.assertGreater(first_counts[0], 0)
        self.assertGreater(first_counts[1], 0)

        with patch.dict(os.environ, {"LOAD_SWAPI_ENABLED": "false"}):
            call_command("load_data", "--skip-planets", "--skip-swapi")

        second_counts = (Character.objects.count(), Species.objects.count())
        self.assertEqual(first_counts, second_counts)
