from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from django.db import transaction

from apps.quotes.models import GlassType, HoleType, Option, Quote, WorkType

AREA_QUANTIZER = Decimal("0.0001")
MONEY_QUANTIZER = Decimal("0.01")
CURRENCY = "XOF"
MINIMUM_BILLING = Decimal("20000.00")
SMALL_SURFACE_THRESHOLD = Decimal("1.00")
SMALL_SURFACE_SURCHARGE = Decimal("3500.00")
URGENCY_SURCHARGE_RATE = Decimal("0.15")
URGENT_OPTION_CODE = "urgent-service"
THICKNESS_MULTIPLIERS = {
    4: Decimal("1.00"),
    6: Decimal("1.10"),
    8: Decimal("1.22"),
    10: Decimal("1.35"),
    12: Decimal("1.48"),
}


class QuoteCalculationError(ValueError):
    pass


@dataclass(frozen=True)
class QuoteBreakdownItem:
    code: str
    label: str
    amount: Decimal

    def as_payload(self) -> dict[str, Decimal | str]:
        return {
            "code": self.code,
            "label": self.label,
            "amount": self.amount,
        }


@dataclass(frozen=True)
class QuoteDetails:
    price_per_m2: Decimal
    breakdown: tuple[QuoteBreakdownItem, ...]

    def as_payload(self) -> dict[str, Decimal | list[dict[str, Decimal | str]]]:
        return {
            "price_per_m2": self.price_per_m2,
            "breakdown": [item.as_payload() for item in self.breakdown],
        }


@dataclass(frozen=True)
class QuoteCalculation:
    area: Decimal
    glass_cost: Decimal
    work_cost: Decimal
    options_cost: Decimal
    holes_cost: Decimal
    total_price: Decimal
    currency: str
    details: QuoteDetails

    def as_payload(self) -> dict[str, Decimal | str | dict]:
        return {
            "area": self.area,
            "glass_cost": self.glass_cost,
            "work_cost": self.work_cost,
            "options_cost": self.options_cost,
            "holes_cost": self.holes_cost,
            "total_price": self.total_price,
            "currency": self.currency,
            "details": self.details.as_payload(),
        }


@dataclass(frozen=True)
class HoleSelection:
    hole_type: HoleType
    count: int
    diameter_mm: int | None = None


def quantize_area(value: Decimal) -> Decimal:
    return value.quantize(AREA_QUANTIZER, rounding=ROUND_HALF_UP)


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)


def get_thickness_choices() -> list[dict[str, int | str]]:
    return [
        {
            "value": thickness,
            "label": f"{thickness} mm",
        }
        for thickness in THICKNESS_MULTIPLIERS
    ]


def _resolve_adjusted_price_per_m2(glass_type: GlassType, thickness: int) -> Decimal:
    try:
        multiplier = THICKNESS_MULTIPLIERS[thickness]
    except KeyError as exc:
        raise QuoteCalculationError("Epaisseur non prise en charge.") from exc

    return quantize_money(Decimal(glass_type.price_per_m2) * multiplier)


def _resolve_work_cost(area: Decimal, work_type: WorkType) -> Decimal:
    unit_price = Decimal(work_type.price)

    if work_type.pricing_type == WorkType.PricingType.FIXED:
        return quantize_money(unit_price)

    if work_type.pricing_type == WorkType.PricingType.VARIABLE:
        return quantize_money(area * unit_price)

    raise QuoteCalculationError("Type de tarification des travaux invalide.")


def _normalize_work_types(
    *,
    work_type: WorkType | None = None,
    work_types: Sequence[WorkType] | None = None,
) -> tuple[WorkType, ...]:
    selected_work_types = tuple(work_types or ())
    if work_type is not None:
        selected_work_types = (work_type, *selected_work_types)

    if not selected_work_types:
        raise QuoteCalculationError("Au moins une prestation doit etre selectionnee.")

    seen_identifiers: set[int] = set()
    normalized_work_types: list[WorkType] = []
    for selected_work_type in selected_work_types:
        identifier = selected_work_type.pk or id(selected_work_type)
        if identifier in seen_identifiers:
            raise QuoteCalculationError(
                "Chaque prestation doit etre selectionnee une seule fois."
            )

        seen_identifiers.add(identifier)
        normalized_work_types.append(selected_work_type)

    return tuple(normalized_work_types)


def _resolve_work_costs(
    area: Decimal,
    work_types: Sequence[WorkType],
) -> tuple[Decimal, tuple[QuoteBreakdownItem, ...]]:
    total = Decimal("0.00")
    breakdown_items: list[QuoteBreakdownItem] = []

    for index, work_type in enumerate(work_types, start=1):
        line_total = _resolve_work_cost(area, work_type)
        total += line_total
        breakdown_items.append(
            QuoteBreakdownItem(
                code=f"work-{index}",
                label=f"Travaux {work_type.name}",
                amount=line_total,
            )
        )

    return quantize_money(total), tuple(breakdown_items)


def _resolve_options_cost(options: Sequence[Option]) -> Decimal:
    return quantize_money(
        sum((Decimal(option.price) for option in options), Decimal("0.00"))
    )


def _has_urgent_option(options: Sequence[Option]) -> bool:
    return any(option.code == URGENT_OPTION_CODE for option in options)


def _normalize_hole_selection(selection: HoleSelection | dict) -> HoleSelection:
    if isinstance(selection, HoleSelection):
        return selection

    return HoleSelection(
        hole_type=selection["hole_type"],
        count=int(selection["count"]),
        diameter_mm=selection.get("diameter_mm"),
    )


def _validate_hole_selection(selection: HoleSelection) -> HoleSelection:
    if selection.count <= 0:
        raise QuoteCalculationError(
            f"Le nombre de trous pour '{selection.hole_type.name}' doit etre superieur a zero."
        )

    if selection.hole_type.requires_diameter and selection.diameter_mm is None:
        raise QuoteCalculationError(
            f"Le diametre est obligatoire pour '{selection.hole_type.name}'."
        )

    if not selection.hole_type.requires_diameter:
        return HoleSelection(
            hole_type=selection.hole_type,
            count=selection.count,
            diameter_mm=None,
        )

    diameter_mm = selection.diameter_mm
    if diameter_mm is None or diameter_mm <= 0:
        raise QuoteCalculationError(
            f"Le diametre pour '{selection.hole_type.name}' doit etre superieur a zero."
        )

    min_diameter = selection.hole_type.min_diameter_mm
    max_diameter = selection.hole_type.max_diameter_mm

    if min_diameter is not None and diameter_mm < min_diameter:
        raise QuoteCalculationError(
            f"Le diametre minimum pour '{selection.hole_type.name}' est {min_diameter} mm."
        )

    if max_diameter is not None and diameter_mm > max_diameter:
        raise QuoteCalculationError(
            f"Le diametre maximum pour '{selection.hole_type.name}' est {max_diameter} mm."
        )

    return selection


def _resolve_holes_cost(
    holes: Sequence[HoleSelection | dict],
) -> tuple[Decimal, tuple[QuoteBreakdownItem, ...]]:
    total = Decimal("0.00")
    breakdown_items: list[QuoteBreakdownItem] = []

    for index, raw_selection in enumerate(holes, start=1):
        selection = _validate_hole_selection(_normalize_hole_selection(raw_selection))
        diameter_mm = selection.diameter_mm or 0
        unit_price = quantize_money(
            Decimal(selection.hole_type.base_price)
            + (Decimal(diameter_mm) * Decimal(selection.hole_type.price_per_mm))
        )
        line_total = quantize_money(unit_price * Decimal(selection.count))
        total += line_total

        label = f"{selection.hole_type.name} x{selection.count}"
        if selection.diameter_mm is not None:
            label = f"{label} ({selection.diameter_mm} mm)"

        breakdown_items.append(
            QuoteBreakdownItem(
                code=f"hole-{index}",
                label=label,
                amount=line_total,
            )
        )

    return quantize_money(total), tuple(breakdown_items)


def calculate_quote(
    *,
    width: Decimal,
    height: Decimal,
    glass_type: GlassType,
    thickness: int,
    work_type: WorkType | None = None,
    work_types: Sequence[WorkType] | None = None,
    options: Sequence[Option] | None = None,
    holes: Sequence[HoleSelection | dict] | None = None,
) -> QuoteCalculation:
    if Decimal(width) <= 0 or Decimal(height) <= 0:
        raise QuoteCalculationError("Les dimensions doivent etre strictement positives.")

    selected_work_types = _normalize_work_types(
        work_type=work_type,
        work_types=work_types,
    )
    selected_options = tuple(options or ())
    area = quantize_area(Decimal(width) * Decimal(height) / Decimal("10000"))
    adjusted_price_per_m2 = _resolve_adjusted_price_per_m2(glass_type, thickness)
    glass_cost = quantize_money(area * adjusted_price_per_m2)
    work_cost, work_breakdown = _resolve_work_costs(area, selected_work_types)
    options_cost = _resolve_options_cost(selected_options)
    holes_cost, hole_breakdown = _resolve_holes_cost(tuple(holes or ()))

    small_surface_surcharge = (
        SMALL_SURFACE_SURCHARGE
        if area < SMALL_SURFACE_THRESHOLD
        else Decimal("0.00")
    )
    urgency_surcharge = (
        quantize_money(
            (glass_cost + work_cost + holes_cost + small_surface_surcharge)
            * URGENCY_SURCHARGE_RATE
        )
        if _has_urgent_option(selected_options)
        else Decimal("0.00")
    )

    subtotal = quantize_money(
        glass_cost
        + work_cost
        + options_cost
        + holes_cost
        + small_surface_surcharge
        + urgency_surcharge
    )
    minimum_billing_adjustment = (
        quantize_money(MINIMUM_BILLING - subtotal)
        if subtotal < MINIMUM_BILLING
        else Decimal("0.00")
    )
    total_price = quantize_money(subtotal + minimum_billing_adjustment)

    breakdown = (
        QuoteBreakdownItem(
            code="glass",
            label=f"Verre {glass_type.name} {thickness} mm",
            amount=glass_cost,
        ),
        *work_breakdown,
        *hole_breakdown,
        QuoteBreakdownItem(
            code="options",
            label="Options selectionnees",
            amount=options_cost,
        ),
        QuoteBreakdownItem(
            code="small-surface",
            label="Majoration petite surface",
            amount=small_surface_surcharge,
        ),
        QuoteBreakdownItem(
            code="urgency",
            label="Majoration urgence",
            amount=urgency_surcharge,
        ),
        QuoteBreakdownItem(
            code="minimum-billing",
            label="Ajustement minimum de facturation",
            amount=minimum_billing_adjustment,
        ),
    )

    return QuoteCalculation(
        area=area,
        glass_cost=glass_cost,
        work_cost=work_cost,
        options_cost=options_cost,
        holes_cost=holes_cost,
        total_price=total_price,
        currency=CURRENCY,
        details=QuoteDetails(
            price_per_m2=adjusted_price_per_m2,
            breakdown=breakdown,
        ),
    )


def _serialize_holes(
    holes: Sequence[HoleSelection | dict] | None,
) -> list[dict[str, Any]]:
    serialized_holes: list[dict[str, Any]] = []

    for raw_selection in holes or ():
        selection = _normalize_hole_selection(raw_selection)
        serialized_holes.append(
            {
                "hole_type_id": selection.hole_type.id,
                "hole_type_code": selection.hole_type.code,
                "hole_type_name": selection.hole_type.name,
                "count": selection.count,
                "diameter_mm": selection.diameter_mm,
            }
        )

    return serialized_holes


@transaction.atomic
def create_quote(
    *,
    width: Decimal,
    height: Decimal,
    glass_type: GlassType,
    thickness: int,
    work_type: WorkType | None = None,
    work_types: Sequence[WorkType] | None = None,
    options: Sequence[Option] | None = None,
    holes: Sequence[HoleSelection | dict] | None = None,
    details: dict[str, Any],
    calculation: QuoteCalculation | None = None,
) -> tuple[Quote, QuoteCalculation]:
    selected_work_types = _normalize_work_types(
        work_type=work_type,
        work_types=work_types,
    )
    calculation = calculation or calculate_quote(
        width=width,
        height=height,
        glass_type=glass_type,
        thickness=thickness,
        work_types=selected_work_types,
        options=options,
        holes=holes,
    )
    selected_options = tuple(options or ())
    quote = Quote.objects.create(
        width=width,
        height=height,
        glass_type=glass_type,
        thickness=thickness,
        work_type=selected_work_types[0],
        area=calculation.area,
        glass_cost=calculation.glass_cost,
        work_cost=calculation.work_cost,
        options_cost=calculation.options_cost,
        holes_cost=calculation.holes_cost,
        total_price=calculation.total_price,
        currency=calculation.currency,
        holes=_serialize_holes(holes),
        details=details,
    )

    if selected_options:
        quote.options.set(selected_options)

    quote.work_types.set(selected_work_types)

    return quote, calculation
