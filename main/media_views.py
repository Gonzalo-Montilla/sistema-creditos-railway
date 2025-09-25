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
        
        # Crear HTML con estilos del sistema
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Estado de Archivos Media - CREDIFLOW</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
            <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
            <style>
                body {{
                    font-family: 'Poppins', sans-serif;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    min-height: 100vh;
                }}
                .diagnostic-container {{
                    max-width: 800px;
                    margin: 2rem auto;
                    padding: 0 1rem;
                }}
                .diagnostic-card {{
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .card-header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 2rem;
                    text-align: center;
                }}
                .card-header h1 {{
                    font-size: 2rem;
                    font-weight: 700;
                    margin: 0;
                }}
                .card-header .subtitle {{
                    opacity: 0.9;
                    margin-top: 0.5rem;
                }}
                .card-body {{
                    padding: 2rem;
                }}
                .status-item {{
                    display: flex;
                    align-items: center;
                    padding: 1rem;
                    margin-bottom: 1rem;
                    background: #f8f9fa;
                    border-radius: 10px;
                    border-left: 4px solid #667eea;
                }}
                .status-item i {{
                    font-size: 1.5rem;
                    margin-right: 1rem;
                    color: #667eea;
                }}
                .status-label {{
                    font-weight: 600;
                    color: #495057;
                    min-width: 180px;
                }}
                .status-value {{
                    color: #212529;
                    font-weight: 500;
                }}
                .status-value.success {{
                    color: #28a745;
                }}
                .status-value.warning {{
                    color: #ffc107;
                }}
                .status-value.danger {{
                    color: #dc3545;
                }}
                .alert-railway {{
                    background: linear-gradient(135deg, #fff3cd, #ffeaa7);
                    border: none;
                    border-left: 4px solid #ffc107;
                    border-radius: 10px;
                    padding: 1.5rem;
                    margin: 1.5rem 0;
                }}
                .btn-back {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border: none;
                    color: white;
                    padding: 0.75rem 2rem;
                    border-radius: 25px;
                    font-weight: 600;
                    text-decoration: none;
                    display: inline-flex;
                    align-items: center;
                    transition: transform 0.2s;
                }}
                .btn-back:hover {{
                    transform: translateY(-2px);
                    color: white;
                    text-decoration: none;
                }}
                .btn-back i {{
                    margin-right: 0.5rem;
                }}
            </style>
        </head>
        <body>
            <div class="diagnostic-container">
                <div class="diagnostic-card">
                    <div class="card-header">
                        <i class="bi bi-hdd-stack" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                        <h1>Estado de Archivos Media</h1>
                        <div class="subtitle">Diagnóstico del Sistema de Almacenamiento</div>
                    </div>
                    
                    <div class="card-body">
                        <div class="status-item">
                            <i class="bi bi-folder2{''-open' if info['media_root_exists'] else ''}"></i>
                            <div class="status-label">Directorio media:</div>
                            <div class="status-value {'success' if info['media_root_exists'] else 'danger'}">
                                {'Existe' if info['media_root_exists'] else 'No existe'}
                            </div>
                        </div>
                        
                        <div class="status-item">
                            <i class="bi bi-geo-alt"></i>
                            <div class="status-label">Ruta del directorio:</div>
                            <div class="status-value">{info['media_root_path']}</div>
                        </div>
                        
                        <div class="status-item">
                            <i class="bi bi-files"></i>
                            <div class="status-label">Archivos encontrados:</div>
                            <div class="status-value {'success' if info['files_count'] > 0 else 'warning'}">
                                {info['files_count']} archivo{'s' if info['files_count'] != 1 else ''}
                            </div>
                        </div>
                        
                        <div class="status-item">
                            <i class="bi bi-hdd"></i>
                            <div class="status-label">Tamaño total:</div>
                            <div class="status-value">{info['total_size']}</div>
                        </div>
                        
                        <div class="status-item">
                            <i class="bi bi-cloud{''-check' if info['is_railway'] else '-slash'}"></i>
                            <div class="status-label">Plataforma:</div>
                            <div class="status-value {'warning' if info['is_railway'] else 'success'}">
                                {'Railway (Efímero)' if info['is_railway'] else 'Local/Persistente'}
                            </div>
                        </div>
                        
                        {'<div class="alert alert-railway"><h5><i class="bi bi-exclamation-triangle me-2"></i>Información Importante</h5><p><strong>Railway utiliza un sistema de archivos efímero.</strong> Esto significa que todos los archivos subidos (imágenes de clientes, documentos, etc.) se pierden automáticamente cada vez que se hace un nuevo deploy de la aplicación.</p><p class="mb-0"><strong>Solución implementada:</strong> El sistema ahora genera automáticamente imágenes placeholder cuando los archivos no están disponibles, garantizando que la aplicación funcione sin errores.</p></div>' if info['is_railway'] else ''}
                        
                        <div class="text-center mt-4">
                            <a href="javascript:history.back()" class="btn-back">
                                <i class="bi bi-arrow-left"></i>
                                Volver al Dashboard
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HttpResponse(html_content, content_type='text/html')
        
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)