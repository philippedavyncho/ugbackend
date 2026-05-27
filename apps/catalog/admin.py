from django.contrib import admin

from .models import TypeVitre


@admin.register(TypeVitre)
class TypeVitreAdmin(admin.ModelAdmin):
    list_display = ("nom", "prix_m2", "created_at")
    search_fields = ("nom",)
