# Pagaré electrónico: documento, firma, OTP

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_habeas_data_codigo'),
    ]

    operations = [
        migrations.AddField(
            model_name='credito',
            name='documento_pagare',
            field=models.FileField(blank=True, null=True, upload_to='pagares/', verbose_name='Pagaré firmado (PDF)'),
        ),
        migrations.AddField(
            model_name='credito',
            name='fecha_firma_pagare',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha firma del pagaré'),
        ),
        migrations.AddField(
            model_name='credito',
            name='codigo_pagare',
            field=models.CharField(
                blank=True,
                help_text='Ej: PG-2025-000001',
                max_length=20,
                null=True,
                verbose_name='Código único documento pagaré',
            ),
        ),
        migrations.AddField(
            model_name='credito',
            name='pagare_firmado_cliente',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha OTP validado - Cliente'),
        ),
        migrations.AddField(
            model_name='credito',
            name='pagare_firmado_codeudor',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha OTP validado - Codeudor'),
        ),
        migrations.CreateModel(
            name='PagareOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_firmante', models.CharField(choices=[('cliente', 'Cliente'), ('codeudor', 'Codeudor')], max_length=10)),
                ('otp_hash', models.CharField(max_length=64)),
                ('expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('credito', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pagare_otps', to='main.credito')),
            ],
            options={},
        ),
    ]
