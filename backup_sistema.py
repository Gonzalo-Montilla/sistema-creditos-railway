#!/usr/bin/env python
"""
Script para crear backup completo del sistema antes de pruebas
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'creditos.settings')
django.setup()


def crear_backup():
    """
    Crea un backup completo de la base de datos
    """
    try:
        # Crear nombre del archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_backup = f"backup_sistema_{timestamp}.json"
        
        print("📦 Creando backup del sistema...")
        print(f"📄 Archivo: {archivo_backup}")
        
        # Ejecutar dumpdata
        comando = f"python manage.py dumpdata --indent 2 > {archivo_backup}"
        resultado = os.system(comando)
        
        if resultado == 0:
            print("✅ Backup creado exitosamente!")
            
            # Mostrar información del archivo
            if os.path.exists(archivo_backup):
                tamaño = os.path.getsize(archivo_backup)
                print(f"📊 Tamaño del archivo: {tamaño:,} bytes")
                print(f"📁 Ubicación: {os.path.abspath(archivo_backup)}")
            
            return archivo_backup
        else:
            print("❌ Error al crear el backup")
            return None
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        return None


def verificar_backup(archivo):
    """
    Verifica que el backup se creó correctamente
    """
    if not archivo or not os.path.exists(archivo):
        return False
    
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
            
        # Verificaciones básicas
        if len(contenido) < 100:
            print("⚠️ El archivo de backup parece muy pequeño")
            return False
        
        if not contenido.strip().startswith('['):
            print("⚠️ El formato del backup no parece correcto")
            return False
        
        print("✅ Backup verificado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando backup: {str(e)}")
        return False


if __name__ == '__main__':
    print("🔄 SISTEMA DE BACKUP")
    print("=" * 30)
    
    archivo = crear_backup()
    
    if archivo and verificar_backup(archivo):
        print(f"\n🎉 Backup completado: {archivo}")
        print("\n💡 Para restaurar (si es necesario):")
        print(f"python manage.py flush --noinput")
        print(f"python manage.py loaddata {archivo}")
    else:
        print("\n❌ Falló el proceso de backup")
        sys.exit(1)