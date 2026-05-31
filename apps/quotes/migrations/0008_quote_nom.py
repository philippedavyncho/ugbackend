from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("quotes", "0007_quote_telephone"),
    ]

    operations = [
        migrations.AddField(
            model_name="quote",
            name="nom",
            field=models.CharField(
                blank=True,
                null=True,
                max_length=150,
            ),
        ),
    ]
