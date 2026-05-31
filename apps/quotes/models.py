from decimal import Decimal
import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import TimeStampedModel
from apps.quotes.validators import PHONE_NUMBER_VALIDATOR


def generate_quote_reference() -> str:
    return f"Q-{uuid.uuid4().hex[:10].upper()}"


def generer_reference_devis() -> str:
    return generate_quote_reference()


class GlassType(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    price_per_m2 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Type de verre"
        verbose_name_plural = "Types de verre"

    def __str__(self) -> str:
        return self.name


class WorkType(TimeStampedModel):
    class PricingType(models.TextChoices):
        FIXED = "fixed", "Fixe"
        VARIABLE = "variable", "Variable"

    name = models.CharField(max_length=120, unique=True)
    pricing_type = models.CharField(
        max_length=16,
        choices=PricingType.choices,
        default=PricingType.FIXED,
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Type de travaux"
        verbose_name_plural = "Types de travaux"

    def __str__(self) -> str:
        return self.name


class HoleType(TimeStampedModel):
    code = models.SlugField(max_length=60, unique=True)
    name = models.CharField(max_length=150, unique=True)
    base_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    price_per_mm = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    requires_diameter = models.BooleanField(default=True)
    min_diameter_mm = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(300)],
    )
    max_diameter_mm = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(300)],
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Type de trou"
        verbose_name_plural = "Types de trous"

    def __str__(self) -> str:
        return self.name


class Option(TimeStampedModel):
    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=120, unique=True)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Option"
        verbose_name_plural = "Options"

    def __str__(self) -> str:
        return self.name


class Quote(TimeStampedModel):
    reference = models.CharField(max_length=32, unique=True, default=generate_quote_reference)
    nom = models.CharField(
        max_length=150,
        blank=True,
        null=True,
    )
    telephone = models.CharField(
        max_length=20,
        validators=[PHONE_NUMBER_VALIDATOR],
        blank=True,
        null=True,
    )
    width = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("1.00")),
            MaxValueValidator(Decimal("1000.00")),
        ],
    )
    height = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("1.00")),
            MaxValueValidator(Decimal("1000.00")),
        ],
    )
    thickness = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(40)]
    )
    glass_type = models.ForeignKey(
        GlassType,
        on_delete=models.PROTECT,
        related_name="quotes",
    )
    work_type = models.ForeignKey(
        WorkType,
        on_delete=models.PROTECT,
        related_name="quotes",
    )
    work_types = models.ManyToManyField(
        WorkType,
        related_name="selected_quotes",
        blank=True,
    )
    options = models.ManyToManyField(
        Option,
        related_name="quotes",
        blank=True,
    )
    area = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
    )
    glass_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    work_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    options_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    holes_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    currency = models.CharField(max_length=3, default="XOF")
    holes = models.JSONField(default=list, blank=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Devis"
        verbose_name_plural = "Devis"

    def __str__(self) -> str:
        return self.reference
