from decimal import Decimal

from django.test import SimpleTestCase

from apps.quotes.models import GlassType, HoleType, Option, WorkType
from apps.quotes.services import QuoteCalculationError, calculate_quote


class QuoteServiceTests(SimpleTestCase):
    def setUp(self):
        self.glass_type = GlassType(
            name="Verre clair",
            price_per_m2=Decimal("10000.00"),
        )
        self.fixed_work = WorkType(
            name="Pose standard",
            pricing_type=WorkType.PricingType.FIXED,
            price=Decimal("5000.00"),
        )
        self.variable_work = WorkType(
            name="Pose atelier",
            pricing_type=WorkType.PricingType.VARIABLE,
            price=Decimal("7000.00"),
        )
        self.urgent_option = Option(
            code="urgent-service",
            name="Intervention urgente",
            price=Decimal("8000.00"),
        )
        self.lock_hole = HoleType(
            code="lock-hole",
            name="Trou pour serrure",
            base_price=Decimal("3000.00"),
            price_per_mm=Decimal("20.00"),
            requires_diameter=True,
            min_diameter_mm=16,
            max_diameter_mm=50,
        )
        self.notch_hole = HoleType(
            code="notch-hole",
            name="Trou pour encoche",
            base_price=Decimal("4500.00"),
            price_per_mm=Decimal("0.00"),
            requires_diameter=False,
        )

    def test_calculate_quote_applies_small_surface_and_minimum_billing_rules(self):
        result = calculate_quote(
            width=Decimal("20"),
            height=Decimal("20"),
            glass_type=self.glass_type,
            thickness=4,
            work_types=[self.variable_work],
            options=[],
        )

        self.assertEqual(result.area, Decimal("0.0400"))
        self.assertEqual(result.glass_cost, Decimal("400.00"))
        self.assertEqual(result.work_cost, Decimal("280.00"))
        self.assertEqual(result.options_cost, Decimal("0.00"))
        self.assertEqual(result.holes_cost, Decimal("0.00"))
        self.assertEqual(result.total_price, Decimal("20000.00"))
        self.assertEqual(
            result.details.breakdown[-1].amount,
            Decimal("15820.00"),
        )

    def test_calculate_quote_applies_urgency_surcharge_when_urgent_option_is_selected(self):
        result = calculate_quote(
            width=Decimal("120"),
            height=Decimal("150"),
            glass_type=self.glass_type,
            thickness=6,
            work_types=[self.fixed_work],
            options=[self.urgent_option],
        )

        self.assertEqual(result.area, Decimal("1.8000"))
        self.assertEqual(result.details.price_per_m2, Decimal("11000.00"))
        self.assertEqual(result.glass_cost, Decimal("19800.00"))
        self.assertEqual(result.work_cost, Decimal("5000.00"))
        self.assertEqual(result.options_cost, Decimal("8000.00"))
        self.assertEqual(result.holes_cost, Decimal("0.00"))
        self.assertEqual(result.details.breakdown[4].amount, Decimal("3720.00"))
        self.assertEqual(result.total_price, Decimal("36520.00"))

    def test_calculate_quote_integrates_holes_with_count_and_diameter(self):
        result = calculate_quote(
            width=Decimal("120"),
            height=Decimal("150"),
            glass_type=self.glass_type,
            thickness=6,
            work_types=[self.fixed_work],
            options=[],
            holes=[
                {
                    "hole_type": self.lock_hole,
                    "count": 2,
                    "diameter_mm": 18,
                },
                {
                    "hole_type": self.notch_hole,
                    "count": 1,
                    "diameter_mm": None,
                },
            ],
        )

        self.assertEqual(result.area, Decimal("1.8000"))
        self.assertEqual(result.holes_cost, Decimal("11220.00"))
        self.assertEqual(result.total_price, Decimal("36020.00"))
        self.assertEqual(result.details.breakdown[2].label, "Trou pour serrure x2 (18 mm)")
        self.assertEqual(result.details.breakdown[2].amount, Decimal("6720.00"))
        self.assertEqual(result.details.breakdown[3].label, "Trou pour encoche x1")
        self.assertEqual(result.details.breakdown[3].amount, Decimal("4500.00"))

    def test_calculate_quote_sums_multiple_work_types_for_the_same_glass(self):
        result = calculate_quote(
            width=Decimal("120"),
            height=Decimal("150"),
            glass_type=self.glass_type,
            thickness=6,
            work_types=[self.fixed_work, self.variable_work],
            options=[],
        )

        self.assertEqual(result.area, Decimal("1.8000"))
        self.assertEqual(result.work_cost, Decimal("17600.00"))
        self.assertEqual(result.total_price, Decimal("37400.00"))
        self.assertEqual(result.details.breakdown[1].label, "Travaux Pose standard")
        self.assertEqual(result.details.breakdown[1].amount, Decimal("5000.00"))
        self.assertEqual(result.details.breakdown[2].label, "Travaux Pose atelier")
        self.assertEqual(result.details.breakdown[2].amount, Decimal("12600.00"))

    def test_calculate_quote_rejects_unknown_thickness(self):
        with self.assertRaises(QuoteCalculationError):
            calculate_quote(
                width=Decimal("100"),
                height=Decimal("100"),
                glass_type=self.glass_type,
                thickness=5,
                work_types=[self.fixed_work],
                options=[],
            )

    def test_calculate_quote_rejects_missing_diameter_for_hole_type_that_requires_it(self):
        with self.assertRaises(QuoteCalculationError):
            calculate_quote(
                width=Decimal("100"),
                height=Decimal("100"),
                glass_type=self.glass_type,
                thickness=4,
                work_types=[self.fixed_work],
                options=[],
                holes=[
                    {
                        "hole_type": self.lock_hole,
                        "count": 1,
                    }
                ],
            )
