#!/usr/bin/env python
"""
Script para crear un superusuario en el primer despliegue (o local).
"""
import os
import sys
import django

# Configurar Django
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'creditos.settings')
    django.setup()
    
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    username = 'admin'
    email = 'admin@test.com'
    password = 'admin123'
    
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"✅ Superusuario '{username}' creado exitosamente")
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
    else:
        print(f"ℹ️ El usuario '{username}' ya existe")
        
    # Mostrar todos los usuarios para confirmar
    users = User.objects.all()
    print(f"\n👥 Total de usuarios en el sistema: {users.count()}")
    for user in users:
        print(f"   - {user.username} ({'superuser' if user.is_superuser else 'usuario normal'})")