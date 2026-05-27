from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.catalog.models import TypeVitre


class TypeVitreApiTests(APITestCase):
    def test_get_types_vitres_retourne_la_liste(self):
        TypeVitre.objects.create(nom="Double vitrage", prix_m2=Decimal("120.00"))
        TypeVitre.objects.create(nom="Verre securite", prix_m2=Decimal("180.00"))

        response = self.client.get(reverse("types-vitres-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["nom"], "Double vitrage")
