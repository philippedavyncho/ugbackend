from django.urls import path

from .views import QuoteConfigView, QuoteSubmissionView, QuoteView

urlpatterns = [
    path("config/", QuoteConfigView.as_view(), name="quote-config"),
    path("quote/", QuoteView.as_view(), name="quote-calculate"),
    path("quote-request/", QuoteSubmissionView.as_view(), name="quote-submit"),
]
