from decimal import Decimal

from django.db import migrations


def seed_requested_hole_types(apps, schema_editor):
    HoleType = apps.get_model("quotes", "HoleType")

    requested_hole_types = [
        {
            "code": "lock-hole",
            "name": "Trou de serrure",
            "base_price": Decimal("3000.00"),
            "price_per_mm": Decimal("0.00"),
            "requires_diameter": False,
            "min_diameter_mm": None,
            "max_diameter_mm": None,
        },
        {
            "code": "pivot-hole",
            "name": "Trou de pivot",
            "base_price": Decimal("0.00"),
            "price_per_mm": Decimal("0.00"),
            "requires_diameter": False,
            "min_diameter_mm": None,
            "max_diameter_mm": None,
        },
        {
            "code": "swing-hinge-hole",
            "name": "Trou de paumelle va-et-vient",
            "base_price": Decimal("0.00"),
            "price_per_mm": Decimal("0.00"),
            "requires_diameter": False,
            "min_diameter_mm": None,
            "max_diameter_mm": None,
        },
        {
            "code": "fixed-hinge-hole",
            "name": "Trou de paumelle fixe",
            "base_price": Decimal("0.00"),
            "price_per_mm": Decimal("0.00"),
            "requires_diameter": False,
            "min_diameter_mm": None,
            "max_diameter_mm": None,
        },
        {
            "code": "notch-hole",
            "name": "Encoche",
            "base_price": Decimal("4500.00"),
            "price_per_mm": Decimal("0.00"),
            "requires_diameter": False,
            "min_diameter_mm": None,
            "max_diameter_mm": None,
        },
        {
            "code": "diameter-hole",
            "name": "Trou de diametre",
            "base_price": Decimal("0.00"),
            "price_per_mm": Decimal("0.00"),
            "requires_diameter": True,
            "min_diameter_mm": 1,
            "max_diameter_mm": 300,
        },
    ]

    for definition in requested_hole_types:
        hole_type, created = HoleType.objects.get_or_create(
            code=definition["code"],
            defaults=definition,
        )

        if created:
            continue

        if hole_type.code == "lock-hole" and (
            hole_type.name == "Trou pour serrure"
            and hole_type.base_price == Decimal("3000.00")
            and hole_type.price_per_mm == Decimal("20.00")
            and hole_type.requires_diameter is True
            and hole_type.min_diameter_mm == 16
            and hole_type.max_diameter_mm == 50
        ):
            hole_type.name = definition["name"]
            hole_type.price_per_mm = definition["price_per_mm"]
            hole_type.requires_diameter = definition["requires_diameter"]
            hole_type.min_diameter_mm = definition["min_diameter_mm"]
            hole_type.max_diameter_mm = definition["max_diameter_mm"]
            hole_type.save(
                update_fields=[
                    "name",
                    "price_per_mm",
                    "requires_diameter",
                    "min_diameter_mm",
                    "max_diameter_mm",
                    "updated_at",
                ]
            )
            continue

        if hole_type.code == "notch-hole" and hole_type.name == "Trou pour encoche":
            hole_type.name = definition["name"]
            hole_type.save(update_fields=["name", "updated_at"])


def unseed_requested_hole_types(apps, schema_editor):
    HoleType = apps.get_model("quotes", "HoleType")
    HoleType.objects.filter(
        code__in=[
            "pivot-hole",
            "swing-hinge-hole",
            "fixed-hinge-hole",
            "diameter-hole",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("quotes", "0004_quote_holes_support"),
    ]

    operations = [
        migrations.RunPython(
            seed_requested_hole_types,
            unseed_requested_hole_types,
        ),
    ]
