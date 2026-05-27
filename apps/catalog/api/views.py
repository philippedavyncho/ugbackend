from rest_framework.generics import ListAPIView

from apps.catalog.api.serializers import TypeVitreSerializer
from apps.catalog.selectors import list_types_vitres


class TypeVitreListView(ListAPIView):
    serializer_class = TypeVitreSerializer

    def get_queryset(self):
        return list_types_vitres()
