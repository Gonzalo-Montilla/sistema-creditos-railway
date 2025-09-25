"""
Middleware personalizado para servir archivos media en producción
"""
import os
from django.http import Http404, FileResponse
from django.conf import settings
from django.utils.http import http_date
from django.core.files.storage import default_storage


class MediaFilesMiddleware:
    """
    Middleware que sirve archivos media en producción
    Similar a lo que hace django.contrib.staticfiles para archivos estáticos
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo procesar rutas que empiecen con MEDIA_URL
        if request.path.startswith(settings.MEDIA_URL):
            return self.serve_media(request)
        
        response = self.get_response(request)
        return response

    def serve_media(self, request):
        """
        Sirve archivos media de forma segura
        """
        try:
            # Extraer la ruta del archivo de la URL
            media_path = request.path[len(settings.MEDIA_URL):]
            
            # Construir la ruta completa
            full_path = os.path.join(settings.MEDIA_ROOT, media_path)
            
            # Verificar que el archivo existe y es seguro
            if not os.path.exists(full_path):
                raise Http404("Archivo media no encontrado")
            
            # Verificar que el archivo esté dentro del directorio MEDIA_ROOT
            if not os.path.abspath(full_path).startswith(os.path.abspath(settings.MEDIA_ROOT)):
                raise Http404("Acceso denegado")
            
            # Devolver el archivo
            return FileResponse(
                open(full_path, 'rb'),
                as_attachment=False,
                filename=os.path.basename(full_path)
            )
            
        except (OSError, ValueError):
            raise Http404("Error al servir archivo media")