from django.core.validators import RegexValidator
from rest_framework import serializers


PHONE_NUMBER_REGEX = r"^[0-9+\s().-]{8,20}$"
PHONE_NUMBER_VALIDATOR = RegexValidator(
    regex=PHONE_NUMBER_REGEX,
    message="Le numero de telephone est invalide.",
)


def validate_supported_thickness(thickness: int) -> int:
    from apps.quotes.services import get_thickness_choices

    allowed_thicknesses = {choice["value"] for choice in get_thickness_choices()}

    if thickness not in allowed_thicknesses:
        raise serializers.ValidationError("Epaisseur non prise en charge.")

    return thickness


def raise_calculation_validation_error(exc: Exception) -> None:
    raise serializers.ValidationError(str(exc)) from exc
