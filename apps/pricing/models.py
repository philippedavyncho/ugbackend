from django.db import models

from apps.common.models import TimeStampedModel


class PricingRule(TimeStampedModel):
    code = models.SlugField(unique=True)
    label = models.CharField(max_length=120)
    coefficient = models.DecimalField(max_digits=8, decimal_places=3)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.label
