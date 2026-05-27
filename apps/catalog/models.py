from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TimeStampedModel


class TypeVitre(TimeStampedModel):
    nom = models.CharField(max_length=120, unique=True)
    prix_m2 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    class Meta:
        ordering = ["nom"]
        verbose_name = "Type de vitre"
        verbose_name_plural = "Types de vitre"

    def __str__(self) -> str:
        return self.nom
