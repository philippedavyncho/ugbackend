from decimal import Decimal

from django.db import migrations


def add_additional_work_types(apps, schema_editor):
    WorkType = apps.get_model("quotes", "WorkType")

    work_types = [
        ("Decoupe", "fixed", Decimal("0.00")),
        ("Rabotage / faconnage des bords", "fixed", Decimal("0.00")),
        ("Percage (nombre de trous)", "fixed", Decimal("0.00")),
        ("Trempe (si applicable)", "variable", Decimal("0.00")),
        ("Feuilletage", "variable", Decimal("0.00")),
        ("Polissage des bords", "fixed", Decimal("0.00")),
        ("Traitement anti-UV", "variable", Decimal("0.00")),
        ("Sablage", "variable", Decimal("0.00")),
    ]

    for name, pricing_type, price in work_types:
        WorkType.objects.get_or_create(
            name=name,
            defaults={
                "pricing_type": pricing_type,
                "price": price,
            },
        )


def remove_additional_work_types(apps, schema_editor):
    WorkType = apps.get_model("quotes", "WorkType")
    WorkType.objects.filter(
        name__in=[
            "Decoupe",
            "Rabotage / faconnage des bords",
            "Percage (nombre de trous)",
            "Trempe (si applicable)",
            "Feuilletage",
            "Polissage des bords",
            "Traitement anti-UV",
            "Sablage",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("quotes", "0002_quote_domain_refactor"),
    ]

    operations = [
        migrations.RunPython(
            add_additional_work_types,
            remove_additional_work_types,
        ),
    ]
