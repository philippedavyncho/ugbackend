from django.urls import path

from .views import TypeVitreListView

urlpatterns = [
    path("", TypeVitreListView.as_view(), name="types-vitres-list"),
]
