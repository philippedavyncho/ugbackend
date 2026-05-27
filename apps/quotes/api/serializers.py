from decimal import Decimal

from rest_framework import serializers

from apps.quotes.models import GlassType, HoleType, Option, WorkType
from apps.quotes.services import CURRENCY, get_thickness_choices


class GlassTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlassType
        fields = ["id", "name", "price_per_m2"]


class WorkTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkType
        fields = ["id", "name", "pricing_type", "price"]


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["id", "name", "price"]


class HoleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HoleType
        fields = [
            "id",
            "code",
            "name",
            "base_price",
            "price_per_mm",
            "requires_diameter",
            "min_diameter_mm",
            "max_diameter_mm",
        ]


class ThicknessSerializer(serializers.Serializer):
    value = serializers.IntegerField()
    label = serializers.CharField()


class QuoteConfigSerializer(serializers.Serializer):
    currency = serializers.CharField()
    thicknesses = ThicknessSerializer(many=True)
    glass_types = GlassTypeSerializer(many=True)
    work_types = WorkTypeSerializer(many=True)
    options = OptionSerializer(many=True)
    hole_types = HoleTypeSerializer(many=True)


class QuoteHoleRequestSerializer(serializers.Serializer):
    hole_type = serializers.PrimaryKeyRelatedField(queryset=HoleType.objects.all())
    count = serializers.IntegerField(min_value=1, max_value=100)
    diameter_mm = serializers.IntegerField(
        min_value=1,
        max_value=300,
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        hole_type = attrs["hole_type"]
        diameter_mm = attrs.get("diameter_mm")

        if hole_type.requires_diameter and diameter_mm is None:
            raise serializers.ValidationError(
                {"diameter_mm": "Le diametre est obligatoire pour ce type de trou."}
            )

        if not hole_type.requires_diameter:
            attrs["diameter_mm"] = None
            return attrs

        min_diameter = hole_type.min_diameter_mm
        max_diameter = hole_type.max_diameter_mm

        if min_diameter is not None and diameter_mm < min_diameter:
            raise serializers.ValidationError(
                {"diameter_mm": f"Le diametre minimum est {min_diameter} mm."}
            )

        if max_diameter is not None and diameter_mm > max_diameter:
            raise serializers.ValidationError(
                {"diameter_mm": f"Le diametre maximum est {max_diameter} mm."}
            )

        return attrs


class QuoteRequestSerializer(serializers.Serializer):
    width = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=Decimal("1.00"),
        max_value=Decimal("1000.00"),
    )
    height = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        min_value=Decimal("1.00"),
        max_value=Decimal("1000.00"),
    )
    glass_type = serializers.PrimaryKeyRelatedField(queryset=GlassType.objects.all())
    thickness = serializers.IntegerField()
    work_type = serializers.PrimaryKeyRelatedField(
        queryset=WorkType.objects.all(),
        required=False,
        write_only=True,
    )
    work_types = serializers.PrimaryKeyRelatedField(
        queryset=WorkType.objects.all(),
        many=True,
        required=False,
    )
    options = serializers.PrimaryKeyRelatedField(
        queryset=Option.objects.all(),
        many=True,
        required=False,
    )
    holes = QuoteHoleRequestSerializer(many=True, required=False, default=list)

    def validate_thickness(self, value: int) -> int:
        allowed_thicknesses = {choice["value"] for choice in get_thickness_choices()}
        if value not in allowed_thicknesses:
            raise serializers.ValidationError("Epaisseur non prise en charge.")
        return value

    def validate_options(self, value):
        option_ids = [option.id for option in value]
        if len(option_ids) != len(set(option_ids)):
            raise serializers.ValidationError(
                "Chaque option doit etre selectionnee une seule fois."
            )
        return value

    def validate_work_types(self, value):
        work_type_ids = [work_type.id for work_type in value]
        if len(work_type_ids) != len(set(work_type_ids)):
            raise serializers.ValidationError(
                "Chaque prestation doit etre selectionnee une seule fois."
            )
        return value

    def validate(self, attrs):
        legacy_work_type = attrs.pop("work_type", None)
        selected_work_types = list(attrs.get("work_types") or [])

        if legacy_work_type is not None:
            selected_work_types.insert(0, legacy_work_type)

        if not selected_work_types:
            raise serializers.ValidationError(
                {"work_types": "Au moins une prestation doit etre selectionnee."}
            )

        work_type_ids = [work_type.id for work_type in selected_work_types]
        if len(work_type_ids) != len(set(work_type_ids)):
            raise serializers.ValidationError(
                {"work_types": "Chaque prestation doit etre selectionnee une seule fois."}
            )

        attrs["work_types"] = selected_work_types
        return attrs


class QuoteBreakdownItemSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class QuoteDetailsSerializer(serializers.Serializer):
    price_per_m2 = serializers.DecimalField(max_digits=12, decimal_places=2)
    breakdown = QuoteBreakdownItemSerializer(many=True)


class QuoteResponseSerializer(serializers.Serializer):
    area = serializers.DecimalField(max_digits=10, decimal_places=4)
    glass_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    work_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    options_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    holes_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(default=CURRENCY)
    details = QuoteDetailsSerializer()


class QuoteSubmissionResponseSerializer(QuoteResponseSerializer):
    reference = serializers.CharField()
