from django.db import migrations, models


def copy_existing_work_type_to_work_types(apps, schema_editor):
    Quote = apps.get_model("quotes", "Quote")

    for quote in Quote.objects.all().iterator():
        if quote.work_type_id:
            quote.work_types.add(quote.work_type_id)


class Migration(migrations.Migration):
    dependencies = [
        ("quotes", "0005_seed_requested_hole_types"),
    ]

    operations = [
        migrations.AddField(
            model_name="quote",
            name="work_types",
            field=models.ManyToManyField(
                blank=True,
                related_name="selected_quotes",
                to="quotes.worktype",
            ),
        ),
        migrations.RunPython(
            copy_existing_work_type_to_work_types,
            migrations.RunPython.noop,
        ),
    ]
