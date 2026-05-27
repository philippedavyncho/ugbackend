import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models

import apps.quotes.models


def copy_catalog_glass_types(apps, schema_editor):
    CatalogGlassType = apps.get_model("catalog", "TypeVitre")
    GlassType = apps.get_model("quotes", "GlassType")

    for catalog_glass_type in CatalogGlassType.objects.all():
        GlassType.objects.get_or_create(
            name=catalog_glass_type.nom,
            defaults={"price_per_m2": catalog_glass_type.prix_m2},
        )


def seed_quote_catalog(apps, schema_editor):
    GlassType = apps.get_model("quotes", "GlassType")
    WorkType = apps.get_model("quotes", "WorkType")
    Option = apps.get_model("quotes", "Option")

    glass_types = [
        ("Verre clair", Decimal("25000.00")),
        ("Verre teinte", Decimal("32000.00")),
        ("Double vitrage", Decimal("48000.00")),
    ]
    for name, price_per_m2 in glass_types:
        GlassType.objects.get_or_create(
            name=name,
            defaults={"price_per_m2": price_per_m2},
        )

    work_types = [
        ("Pose standard", "fixed", Decimal("12000.00")),
        ("Remplacement sur chassis existant", "variable", Decimal("8500.00")),
        ("Finition atelier", "fixed", Decimal("7000.00")),
    ]
    for name, pricing_type, price in work_types:
        WorkType.objects.get_or_create(
            name=name,
            defaults={
                "pricing_type": pricing_type,
                "price": price,
            },
        )

    options = [
        ("polished-edges", "Bords polis", Decimal("4500.00")),
        ("security-film", "Film securite", Decimal("6500.00")),
        ("urgent-service", "Intervention urgente", Decimal("8000.00")),
    ]
    for code, name, price in options:
        Option.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "price": price,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("quotes", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(
                    name="Devis",
                ),
            ],
        ),
        migrations.CreateModel(
            name="GlassType",
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
                ("name", models.CharField(max_length=120, unique=True)),
                (
                    "price_per_m2",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.01"))],
                    ),
                ),
            ],
            options={
                "verbose_name": "Type de verre",
                "verbose_name_plural": "Types de verre",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Option",
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
                ("code", models.SlugField(max_length=50, unique=True)),
                ("name", models.CharField(max_length=120, unique=True)),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                    ),
                ),
            ],
            options={
                "verbose_name": "Option",
                "verbose_name_plural": "Options",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="WorkType",
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
                ("name", models.CharField(max_length=120, unique=True)),
                (
                    "pricing_type",
                    models.CharField(
                        choices=[("fixed", "Fixe"), ("variable", "Variable")],
                        default="fixed",
                        max_length=16,
                    ),
                ),
                (
                    "price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                    ),
                ),
            ],
            options={
                "verbose_name": "Type de travaux",
                "verbose_name_plural": "Types de travaux",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Quote",
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
                (
                    "reference",
                    models.CharField(
                        default=apps.quotes.models.generate_quote_reference,
                        max_length=32,
                        unique=True,
                    ),
                ),
                (
                    "width",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=8,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("1.00")),
                            django.core.validators.MaxValueValidator(Decimal("1000.00")),
                        ],
                    ),
                ),
                (
                    "height",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=8,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("1.00")),
                            django.core.validators.MaxValueValidator(Decimal("1000.00")),
                        ],
                    ),
                ),
                (
                    "thickness",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(40),
                        ]
                    ),
                ),
                (
                    "area",
                    models.DecimalField(
                        decimal_places=4,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.0001"))],
                    ),
                ),
                (
                    "glass_cost",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                    ),
                ),
                (
                    "work_cost",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                    ),
                ),
                (
                    "options_cost",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                    ),
                ),
                (
                    "total_price",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.01"))],
                    ),
                ),
                ("currency", models.CharField(default="XOF", max_length=3)),
                ("details", models.JSONField(blank=True, default=dict)),
                (
                    "glass_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="quotes",
                        to="quotes.glasstype",
                    ),
                ),
                (
                    "options",
                    models.ManyToManyField(blank=True, related_name="quotes", to="quotes.option"),
                ),
                (
                    "work_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="quotes",
                        to="quotes.worktype",
                    ),
                ),
            ],
            options={
                "verbose_name": "Devis",
                "verbose_name_plural": "Devis",
                "ordering": ["-created_at"],
            },
        ),
        migrations.RunPython(copy_catalog_glass_types, migrations.RunPython.noop),
        migrations.RunPython(seed_quote_catalog, migrations.RunPython.noop),
    ]
