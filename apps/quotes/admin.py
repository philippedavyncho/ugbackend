from django.contrib import admin

from .models import GlassType, HoleType, Option, Quote, WorkType


@admin.register(GlassType)
class GlassTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "price_per_m2", "created_at")
    search_fields = ("name",)


@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "pricing_type", "price", "created_at")
    list_filter = ("pricing_type",)
    search_fields = ("name",)


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "price", "created_at")
    search_fields = ("name", "code")


@admin.register(HoleType)
class HoleTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "base_price",
        "price_per_mm",
        "requires_diameter",
        "min_diameter_mm",
        "max_diameter_mm",
        "created_at",
    )
    list_filter = ("requires_diameter",)
    search_fields = ("name", "code")


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "nom",
        "telephone",
        "glass_type",
        "work_types_display",
        "width",
        "height",
        "thickness",
        "holes_cost",
        "total_price",
        "currency",
        "created_at",
    )
    list_filter = ("currency", "glass_type", "created_at")
    search_fields = (
        "reference",
        "nom",
        "telephone",
        "glass_type__name",
        "work_type__name",
        "work_types__name",
    )
    filter_horizontal = ("work_types", "options")

    @admin.display(description="Prestations")
    def work_types_display(self, obj):
        work_type_names = list(obj.work_types.values_list("name", flat=True))
        if work_type_names:
            return ", ".join(work_type_names)
        return obj.work_type.name
