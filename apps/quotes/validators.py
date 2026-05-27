from rest_framework import serializers

from apps.quotes.services import QuoteCalculationError, get_thickness_choices


def validate_supported_thickness(thickness: int) -> int:
    allowed_thicknesses = {choice["value"] for choice in get_thickness_choices()}

    if thickness not in allowed_thicknesses:
        raise serializers.ValidationError("Epaisseur non prise en charge.")

    return thickness


def raise_calculation_validation_error(exc: QuoteCalculationError) -> None:
    raise serializers.ValidationError(str(exc)) from exc
