import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quotes", "0006_quote_work_types_selection"),
    ]

    operations = [
        migrations.AddField(
            model_name="quote",
            name="telephone",
            field=models.CharField(
                blank=True,
                null=True,
                max_length=20,
                validators=[
                    django.core.validators.RegexValidator(
                        message="Le numero de telephone est invalide.",
                        regex="^[0-9+\\s().-]{8,20}$",
                    )
                ],
            ),
        ),
    ]
