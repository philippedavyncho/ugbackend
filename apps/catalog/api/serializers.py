from rest_framework import serializers

from apps.catalog.models import TypeVitre


class TypeVitreSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeVitre
        fields = ["id", "nom", "prix_m2"]
