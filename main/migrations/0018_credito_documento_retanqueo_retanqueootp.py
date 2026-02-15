# Documento de retanqueo en Credito + RetanqueoOTP

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0017_credito_es_renovacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='credito',
            name='documento_retanqueo',
            field=models.FileField(blank=True, null=True, upload_to='retanqueos/', verbose_name='Documento de retanqueo firmado (PDF)'),
        ),
        migrations.AddField(
            model_name='credito',
            name='fecha_firma_retanqueo',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha firma documento retanqueo'),
        ),
        migrations.AddField(
            model_name='credito',
            name='codigo_retanqueo',
            field=models.CharField(blank=True, max_length=32, null=True, verbose_name='Código documento retanqueo'),
        ),
        migrations.CreateModel(
            name='RetanqueoOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('otp_hash', models.CharField(max_length=64)),
                ('expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('credito', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='retanqueo_otps', to='main.credito')),
            ],
            options={},
        ),
    ]
