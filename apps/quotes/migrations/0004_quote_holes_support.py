from decimal import Decimal

import django.core.validators
from django.db import migrations, models


def seed_hole_types(apps, schema_editor):
    HoleType = apps.get_model("quotes", "HoleType")

    hole_types = [
        {
            "code": "lock-hole",
            "name": "Trou pour serrure",
            "base_price": Decimal("3000.00"),
            "price_per_mm": Decimal("20.00"),
            "requires_diameter": True,
            "min_diameter_mm": 16,
            "max_diameter_mm": 50,
        },
        {
            "code": "notch-hole",
            "name": "Trou pour encoche",
            "base_price": Decimal("4500.00"),
            "price_per_mm": Decimal("0.00"),
            "requires_diameter": False,
            "min_diameter_mm": None,
            "max_diameter_mm": None,
        },
    ]

    for hole_type in hole_types:
        HoleType.objects.get_or_create(
            code=hole_type["code"],
            defaults=hole_type,
        )


def unseed_hole_types(apps, schema_editor):
    HoleType = apps.get_model("quotes", "HoleType")
    HoleType.objects.filter(code__in=["lock-hole", "notch-hole"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("quotes", "0003_add_more_work_types"),
    ]

    operations = [
        migrations.CreateModel(
            name="HoleType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.SlugField(max_length=60, unique=True)),
                ("name", models.CharField(max_length=150, unique=True)),
                (
                    "base_price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                    ),
                ),
                (
                    "price_per_mm",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                    ),
                ),
                ("requires_diameter", models.BooleanField(default=True)),
                (
                    "min_diameter_mm",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(300),
                        ],
                    ),
                ),
                (
                    "max_diameter_mm",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(300),
                        ],
                    ),
                ),
            ],
            options={
                "verbose_name": "Type de trou",
                "verbose_name_plural": "Types de trous",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="quote",
            name="holes_cost",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
            ),
        ),
        migrations.AddField(
            model_name="quote",
            name="holes",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.RunPython(
            seed_hole_types,
            unseed_hole_types,
        ),
    ]
