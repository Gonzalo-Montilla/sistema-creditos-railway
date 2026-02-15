# Generated manually - código único documento Habeas Data

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0012_habeas_data_cliente_codeudor_otp'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='codigo_habeas_data',
            field=models.CharField(
                blank=True,
                help_text='Ej: HD-2025-C000123 (para verificación del documento)',
                max_length=20,
                null=True,
                verbose_name='Código único documento Habeas Data',
            ),
        ),
        migrations.AddField(
            model_name='codeudor',
            name='codigo_habeas_data',
            field=models.CharField(
                blank=True,
                help_text='Ej: HD-2025-D000045 (para verificación del documento)',
                max_length=20,
                null=True,
                verbose_name='Código único documento Habeas Data',
            ),
        ),
    ]
