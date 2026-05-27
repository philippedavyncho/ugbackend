from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.quotes.models import GlassType, HoleType, Option, Quote, WorkType


class QuoteApiTests(APITestCase):
    def setUp(self):
        self.glass_type = GlassType.objects.create(
            name="Double vitrage test",
            price_per_m2=Decimal("25000.00"),
        )
        self.work_type = WorkType.objects.create(
            name="Pose standard test",
            pricing_type=WorkType.PricingType.FIXED,
            price=Decimal("12000.00"),
        )
        self.secondary_work_type = WorkType.objects.create(
            name="Finition atelier test",
            pricing_type=WorkType.PricingType.VARIABLE,
            price=Decimal("2000.00"),
        )
        self.polish_option = Option.objects.create(
            code="polished-edges-test",
            name="Bords polis test",
            price=Decimal("4500.00"),
        )
        self.urgent_option = Option.objects.get(code="urgent-service")
        self.lock_hole = HoleType.objects.create(
            code="lock-hole-test",
            name="Trou pour serrure test",
            base_price=Decimal("3000.00"),
            price_per_mm=Decimal("20.00"),
            requires_diameter=True,
            min_diameter_mm=16,
            max_diameter_mm=50,
        )
        self.notch_hole = HoleType.objects.create(
            code="notch-hole-test",
            name="Trou pour encoche test",
            base_price=Decimal("4500.00"),
            price_per_mm=Decimal("0.00"),
            requires_diameter=False,
        )

    def _build_payload(self):
        return {
            "width": "120",
            "height": "150",
            "glass_type": self.glass_type.id,
            "thickness": 6,
            "work_types": [self.work_type.id, self.secondary_work_type.id],
            "options": [self.polish_option.id, self.urgent_option.id],
            "holes": [
                {
                    "hole_type": self.lock_hole.id,
                    "count": 2,
                    "diameter_mm": 18,
                },
                {
                    "hole_type": self.notch_hole.id,
                    "count": 1,
                },
            ],
        }

    def test_get_config_returns_all_frontend_dependencies(self):
        response = self.client.get(reverse("quote-config"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["currency"], "XOF")
        glass_type_names = {glass_type["name"] for glass_type in response.data["glass_types"]}
        work_type_names = {work_type["name"] for work_type in response.data["work_types"]}
        option_names = {option["name"] for option in response.data["options"]}
        hole_type_names = {hole_type["name"] for hole_type in response.data["hole_types"]}

        self.assertIn("Double vitrage test", glass_type_names)
        self.assertIn("Pose standard test", work_type_names)
        self.assertIn("Bords polis test", option_names)
        self.assertIn("Trou pour serrure test", hole_type_names)
        self.assertIn("thicknesses", response.data)

    def test_post_quote_returns_live_calculation_without_persisting_history(self):
        payload = self._build_payload()

        response = self.client.post(reverse("quote-calculate"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Quote.objects.count(), 0)
        self.assertEqual(response.data["area"], "1.8000")
        self.assertEqual(response.data["glass_cost"], "49500.00")
        self.assertEqual(response.data["work_cost"], "15600.00")
        self.assertEqual(response.data["options_cost"], "12500.00")
        self.assertEqual(response.data["holes_cost"], "11220.00")
        self.assertEqual(response.data["total_price"], "100268.00")
        self.assertEqual(response.data["details"]["price_per_m2"], "27500.00")
        self.assertEqual(len(response.data["details"]["breakdown"]), 9)
        self.assertEqual(response.data["details"]["breakdown"][2]["label"], "Travaux Finition atelier test")
        self.assertEqual(response.data["details"]["breakdown"][3]["label"], "Trou pour serrure test x2 (18 mm)")

    def test_post_quote_request_persists_quote_and_returns_reference(self):
        payload = self._build_payload()

        response = self.client.post(reverse("quote-submit"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Quote.objects.count(), 1)
        self.assertIn("reference", response.data)
        self.assertEqual(response.data["total_price"], "100268.00")

        quote = Quote.objects.get()
        self.assertEqual(quote.reference, response.data["reference"])
        self.assertEqual(quote.area, Decimal("1.8000"))
        self.assertEqual(quote.total_price, Decimal("100268.00"))
        self.assertEqual(quote.work_type, self.work_type)
        self.assertEqual(quote.work_types.count(), 2)
        self.assertEqual(quote.options.count(), 2)
        self.assertEqual(quote.holes[0]["hole_type_id"], self.lock_hole.id)
        self.assertEqual(quote.holes[0]["count"], 2)
        self.assertEqual(quote.holes[0]["diameter_mm"], 18)
        self.assertEqual(quote.details["price_per_m2"], "27500.00")

    def test_post_quote_rejects_duplicate_options(self):
        payload = {
            "width": "120",
            "height": "150",
            "glass_type": self.glass_type.id,
            "thickness": 4,
            "work_types": [self.work_type.id],
            "options": [self.polish_option.id, self.polish_option.id],
        }

        response = self.client.post(reverse("quote-calculate"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("options", response.data)

    def test_post_quote_rejects_duplicate_work_types(self):
        payload = {
            "width": "120",
            "height": "150",
            "glass_type": self.glass_type.id,
            "thickness": 4,
            "work_types": [self.work_type.id, self.work_type.id],
            "options": [],
        }

        response = self.client.post(reverse("quote-calculate"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("work_types", response.data)

    def test_post_quote_rejects_unsupported_thickness(self):
        payload = {
            "width": "120",
            "height": "150",
            "glass_type": self.glass_type.id,
            "thickness": 5,
            "work_types": [self.work_type.id],
            "options": [],
        }

        response = self.client.post(reverse("quote-calculate"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("thickness", response.data)

    def test_post_quote_rejects_hole_without_required_diameter(self):
        payload = {
            "width": "120",
            "height": "150",
            "glass_type": self.glass_type.id,
            "thickness": 6,
            "work_types": [self.work_type.id],
            "options": [],
            "holes": [
                {
                    "hole_type": self.lock_hole.id,
                    "count": 1,
                }
            ],
        }

        response = self.client.post(reverse("quote-calculate"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("holes", response.data)
