from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.quotes.api.serializers import (
    QuoteConfigSerializer,
    QuoteRequestSerializer,
    QuoteResponseSerializer,
    QuoteSubmissionResponseSerializer,
)
from apps.quotes.models import GlassType, HoleType, Option, WorkType
from apps.quotes.services import (
    CURRENCY,
    calculate_quote,
    create_quote,
    get_thickness_choices,
)


@method_decorator(cache_page(60 * 5), name="dispatch")
class QuoteConfigView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "config"

    def get(self, request):
        payload = {
            "currency": CURRENCY,
            "thicknesses": get_thickness_choices(),
            "glass_types": GlassType.objects.all(),
            "work_types": WorkType.objects.all(),
            "options": Option.objects.all(),
            "hole_types": HoleType.objects.all(),
        }
        serializer = QuoteConfigSerializer(payload)
        return Response(serializer.data)


class QuoteView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "quote"

    def post(self, request):
        serializer = QuoteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quote_payload = dict(serializer.validated_data)
        quote_payload.pop("nom", None)
        quote_payload.pop("telephone", None)
        result = calculate_quote(**quote_payload)
        response_serializer = QuoteResponseSerializer(result.as_payload())
        return Response(response_serializer.data)


class QuoteSubmissionView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "quote"

    def post(self, request):
        serializer = QuoteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quote_payload = dict(serializer.validated_data)
        nom = quote_payload.pop("nom", None)
        telephone = quote_payload.pop("telephone", None)
        calculation = calculate_quote(**quote_payload)
        response_data = QuoteResponseSerializer(calculation.as_payload()).data
        quote, _ = create_quote(
            **quote_payload,
            nom=nom,
            telephone=telephone,
            details=response_data["details"],
            calculation=calculation,
        )

        submission_serializer = QuoteSubmissionResponseSerializer(
            {
                **response_data,
                "reference": quote.reference,
            }
        )
        return Response(submission_serializer.data, status=status.HTTP_201_CREATED)
