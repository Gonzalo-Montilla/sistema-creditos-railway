"""
Vistas para servir archivos media en producción
"""

import os
import mimetypes
from django.http import HttpResponse, Http404, FileResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.utils.decorators import method_decorator
from django.views.generic import View
from PIL import Image
from io import BytesIO


@login_required
@cache_control(max_age=3600, private=True)  # Cachear por 1 hora
def serve_media_file(request, path):
    """
    Sirve archivos media de forma segura en producción
    """
    try:
        # Construir ruta completa del archivo
        file_path = os.path.join(settings.MEDIA_ROOT, path)
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            # Si no existe, crear imagen placeholder
            return create_placeholder_image(request, path)
        
        # Verificar que está dentro de MEDIA_ROOT (seguridad)
        if not os.path.abspath(file_path).startswith(os.path.abspath(settings.MEDIA_ROOT)):
            raise Http404("Acceso denegado")
        
        # Determinar tipo de contenido
        content_type, _ = mimetypes.guess_type(file_path)
        
        # Si es una imagen, optimizarla
        if content_type and content_type.startswith('image/'):
            return serve_optimized_image(file_path, content_type)
        
        # Para otros archivos, servir directamente
        return FileResponse(
            open(file_path, 'rb'),
            content_type=content_type,
            as_attachment=False
        )
        
    except Exception as e:
        # Log del error en desarrollo
        if settings.DEBUG:
            print(f"Error sirviendo media: {str(e)}")
        
        # Crear imagen placeholder
        return create_placeholder_image(request, path)


def serve_optimized_image(file_path, content_type):
    """
    Sirve imagen optimizada
    """
    try:
        # Abrir y optimizar imagen
        with Image.open(file_path) as img:
            # Convertir RGBA a RGB si es necesario
            if img.mode in ('RGBA', 'LA', 'P'):
                # Crear fondo blanco
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Redimensionar si es muy grande
            max_size = (800, 600)  # Máximo 800x600 para optimizar carga
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                try:
                    # Usar el nuevo enum de Pillow 10+
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                except AttributeError:
                    # Fallback para versiones más antiguas de Pillow
                    img.thumbnail(max_size, Image.LANCZOS)
            
            # Guardar en buffer
            buffer = BytesIO()
            format_name = 'JPEG' if content_type == 'image/jpeg' else 'PNG'
            img.save(buffer, format=format_name, quality=85, optimize=True)
            buffer.seek(0)
            
            response = HttpResponse(buffer.getvalue(), content_type=content_type)
            response['Cache-Control'] = 'private, max-age=3600'  # Cache 1 hora
            return response
            
    except Exception:
        # Si falla la optimización, servir archivo original
        return FileResponse(
            open(file_path, 'rb'),
            content_type=content_type,
            as_attachment=False
        )


def create_placeholder_image(request, path):
    """
    Crea imagen placeholder cuando no se encuentra el archivo
    """
    try:
        # Crear imagen placeholder
        img = Image.new('RGB', (300, 200), color=(240, 240, 240))
        
        # Añadir texto si PIL tiene fuentes disponibles
        try:
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            
            # Texto del placeholder
            if 'rostro' in path.lower():
                text = "Sin foto\nde rostro"
            elif 'cedula' in path.lower():
                text = "Sin foto\nde cédula"
            elif 'servicio' in path.lower():
                text = "Sin recibo\nde servicio"
            else:
                text = "Imagen\nno disponible"
            
            # Centrar texto
            bbox = draw.textbbox((0, 0), text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (300 - text_width) // 2
            y = (200 - text_height) // 2
            
            draw.text((x, y), text, fill=(120, 120, 120), align="center")
            
        except ImportError:
            # Si no hay fuentes disponibles, crear imagen simple
            pass
        
        # Convertir a bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        response = HttpResponse(buffer.getvalue(), content_type='image/png')
        response['Cache-Control'] = 'private, max-age=86400'  # Cache 24 horas
        return response
        
    except Exception:
        # Fallback: devolver respuesta 404
        raise Http404("Imagen no disponible")


@login_required
def media_status(request):
    """
    Vista para mostrar el estado de los archivos media
    """
    try:
        media_exists = os.path.exists(settings.MEDIA_ROOT)
        files_count = 0
        total_size = 0
        
        if media_exists:
            for root, dirs, files in os.walk(settings.MEDIA_ROOT):
                files_count += len(files)
                for file in files:
                    try:
                        total_size += os.path.getsize(os.path.join(root, file))
                    except OSError:
                        pass
        
        # Formatear tamaño
        if total_size < 1024:
            size_str = f"{total_size} bytes"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.1f} KB"
        else:
            size_str = f"{total_size / (1024 * 1024):.1f} MB"
        
        info = {
            'media_root_exists': media_exists,
            'media_root_path': str(settings.MEDIA_ROOT),
            'files_count': files_count,
            'total_size': size_str,
            'is_railway': bool(os.getenv('RAILWAY_ENVIRONMENT')),
        }
        
        return HttpResponse(f"""
        <h2>Estado de Archivos Media</h2>
        <ul>
            <li>Directorio media existe: {info['media_root_exists']}</li>
            <li>Ruta: {info['media_root_path']}</li>
            <li>Archivos encontrados: {info['files_count']}</li>
            <li>Tamaño total: {info['total_size']}</li>
            <li>En Railway: {info['is_railway']}</li>
        </ul>
        
        {'<p><strong>⚠️ NOTA:</strong> Railway tiene sistema de archivos efímero. Los archivos se pierden en cada deploy.</p>' if info['is_railway'] else ''}
        
        <a href="javascript:history.back()">← Volver</a>
        """, content_type='text/html')
        
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)