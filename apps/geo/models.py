from django.db import models

from apps.common.models import TimeStampedModel


class ServiceZone(TimeStampedModel):
    name = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=20)
    travel_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self) -> str:
        return f"{self.name} ({self.postal_code})"
