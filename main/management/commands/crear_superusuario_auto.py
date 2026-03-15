from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError
import os

class Command(BaseCommand):
    help = 'Crea un superusuario automáticamente si no existe'

    def handle(self, *args, **options):
        User = get_user_model()
        
        username = 'admin'
        email = 'admin@test.com'
        password = 'admin123'
        
        try:
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Superusuario "{username}" creado exitosamente')
                )
                self.stdout.write(f'Email: {email}')
                self.stdout.write(f'Password: {password}')
            else:
                self.stdout.write(
                    self.style.WARNING(f'El superusuario "{username}" ya existe')
                )
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Error al crear superusuario: {e}')
            )
        
        # Mostrar estadísticas de usuarios
        total_users = User.objects.count()
        superusers = User.objects.filter(is_superuser=True).count()
        
        self.stdout.write(f'\nEstadisticas de usuarios:')
        self.stdout.write(f'   Total usuarios: {total_users}')
        self.stdout.write(f'   Superusuarios: {superusers}')
        
        # Listar todos los usuarios
        users = User.objects.all()
        if users.exists():
            self.stdout.write(f'\nLista de usuarios:')
            for user in users:
                role = 'Superusuario' if user.is_superuser else 'Usuario normal'
                self.stdout.write(f'   - {user.username} ({role})')