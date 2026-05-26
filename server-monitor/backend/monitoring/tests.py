from django.test import TestCase

from monitoring.serializers import normalize_custom_ports


class CustomPortValidationTests(TestCase):
    def test_normalizes_ports(self):
        self.assertEqual(normalize_custom_ports("22, 80,80, 443"), "22, 80, 443")
