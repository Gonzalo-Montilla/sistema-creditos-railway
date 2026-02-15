# Documento de renovación en Cliente + RenovacionOTP

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_credito_pagare_pagareotp'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='documento_renovacion',
            field=models.FileField(blank=True, null=True, upload_to='renovaciones/', verbose_name='Documento de renovación (PDF)'),
        ),
        migrations.AddField(
            model_name='cliente',
            name='fecha_firma_renovacion',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha firma documento de renovación'),
        ),
        migrations.AddField(
            model_name='cliente',
            name='codigo_renovacion',
            field=models.CharField(
                blank=True,
                help_text='Ej: REN-2025-000123',
                max_length=20,
                null=True,
                verbose_name='Código único documento renovación',
            ),
        ),
        migrations.CreateModel(
            name='RenovacionOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('otp_hash', models.CharField(max_length=64)),
                ('expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('credito', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='renovacion_otps', to='main.credito')),
            ],
            options={},
        ),
    ]
