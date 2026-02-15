# Despliegue del sistema (fuera de Railway)

Este proyecto está preparado para desplegarse en **cualquier entorno** (VPS, otro PaaS, Docker, etc.). El archivo `railway.toml` solo se usa si desplegás en Railway.

## Variables de entorno recomendadas (producción)

| Variable | Uso |
|----------|-----|
| `SECRET_KEY` | Obligatorio en producción. Generar una clave segura. |
| `DEBUG` | `False` en producción. |
| `DATABASE_URL` | URL de conexión a la base de datos (PostgreSQL recomendado). Si no está, se usa SQLite (solo desarrollo). |
| `ALLOWED_HOSTS` | Opcional. Lista separada por comas, ej: `tu-dominio.com,www.tu-dominio.com`. Por defecto `*`. |
| `STATIC_ROOT` | Opcional. Ruta donde se recolectan estáticos (ej. `/app/staticfiles` en algunos PaaS). Por defecto `./staticfiles`. |
| `EPHEMERAL_STORAGE` | Opcional. Si el disco se borra en cada deploy, poner `true` para mostrar aviso en el sistema (archivos media). |
| `SECURE_SSL_REDIRECT` | Opcional. `true` si el servidor debe forzar HTTPS. |

Para correo (OTP, recordatorios): `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`, etc. Ver comentarios en `creditos/settings.py`.

## Arranque de la aplicación

Muchos entornos usan un **Procfile** (Heroku, Render, etc.). El del proyecto arranca así:

```bash
python manage.py migrate && python manage.py collectstatic --noinput && python manage.py crear_superusuario_auto && gunicorn creditos.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

Si tu plataforma no usa Procfile, ejecutá algo equivalente (migrate, collectstatic, gunicorn/uWSGI). La variable `PORT` la suelen definir los PaaS; en VPS podés usar un puerto fijo (ej. 8000).

## Tareas programadas (cron)

Para que los cobradores vean desde las 6:00 AM los clientes a recaudar hoy, hay que ejecutar la generación de tareas diarias. **No depende de Railway**; configuralo en tu propio entorno:

### Opción 1: Cron del sistema (Linux / VPS)

```bash
# Editar crontab: crontab -e
# Generar tareas de cobro, Lun–Vie a las 6:00
0 6 * * 1-5 cd /ruta/al/proyecto && python manage.py generar_tareas_diarias --verbose
```

Ajustá `/ruta/al/proyecto` y, si usás un venv, el path a `python`.

### Opción 2: django-crontab

Si instalás `django-crontab` y lo tenés en `INSTALLED_APPS`, en `settings.py` ya están definidos los `CRONJOBS` (6:00 tareas, 7:00 recordatorios, etc.). Después de desplegar:

```bash
python manage.py crontab add
```

### Opción 3: Scheduler del PaaS

En Render, Heroku Scheduler, AWS EventBridge, etc., programá un job que ejecute:

```bash
python manage.py generar_tareas_diarias --verbose
```

todos los días a las 6:00 (o la hora que prefieras).

## Resumen

- **Railway:** opcional; si no usás Railway, ignorá `railway.toml` y configurá según este documento.
- **Base de datos:** definir `DATABASE_URL` en producción.
- **Cron:** configurar en tu servidor o PaaS la ejecución de `generar_tareas_diarias` a las 6:00 para la programación diaria de cobranza.
