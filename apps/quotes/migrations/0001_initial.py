import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models

import apps.quotes.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Devis",
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
                        default=apps.quotes.models.generer_reference_devis,
                        max_length=32,
                        unique=True,
                    ),
                ),
                ("nom", models.CharField(max_length=150)),
                ("email", models.EmailField(max_length=254)),
                (
                    "telephone",
                    models.CharField(
                        max_length=20,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Le numero de telephone est invalide.",
                                regex="^[0-9+\\s().-]{8,20}$",
                            )
                        ],
                    ),
                ),
                ("adresse", models.CharField(blank=True, max_length=255)),
                ("localisation", models.CharField(max_length=120)),
                (
                    "largeur_cm",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(10000),
                        ]
                    ),
                ),
                (
                    "hauteur_cm",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(10000),
                        ]
                    ),
                ),
                (
                    "quantite",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(1000),
                        ]
                    ),
                ),
                (
                    "urgence",
                    models.CharField(
                        choices=[("normal", "Normal"), ("urgent", "Urgent")],
                        default="normal",
                        max_length=20,
                    ),
                ),
                (
                    "surface_m2",
                    models.DecimalField(
                        decimal_places=4,
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.0001"))],
                    ),
                ),
                (
                    "prix_m2_applique",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.01"))],
                    ),
                ),
                (
                    "prix_base",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                    ),
                ),
                (
                    "supplement_urgence",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                    ),
                ),
                (
                    "frais_deplacement",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                    ),
                ),
                (
                    "total",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.01"))],
                    ),
                ),
                (
                    "type_vitre",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="devis",
                        to="catalog.typevitre",
                    ),
                ),
            ],
            options={
                "verbose_name": "Devis",
                "verbose_name_plural": "Devis",
                "ordering": ["-created_at"],
            },
        ),
    ]
