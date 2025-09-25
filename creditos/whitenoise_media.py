"""
Configuración personalizada de WhiteNoise para servir archivos media en Railway
"""

from whitenoise import WhiteNoise
from django.conf import settings
import os


class MediaWhiteNoise(WhiteNoise):
    """
    Extensión de WhiteNoise para servir archivos media además de archivos estáticos
    """
    
    def __init__(self, application, **kwargs):
        super().__init__(application, **kwargs)
        
        # Añadir directorio de archivos media si existe
        if hasattr(settings, 'MEDIA_ROOT') and hasattr(settings, 'MEDIA_URL'):
            media_root = str(settings.MEDIA_ROOT)
            media_url = settings.MEDIA_URL.rstrip('/')
            
            if os.path.exists(media_root):
                self.add_files(media_root, prefix=media_url)
    
    def add_media_files(self):
        """
        Añade archivos media al WhiteNoise
        """
        if hasattr(settings, 'MEDIA_ROOT') and hasattr(settings, 'MEDIA_URL'):
            media_root = str(settings.MEDIA_ROOT)
            media_url = settings.MEDIA_URL.rstrip('/')
            
            if os.path.exists(media_root):
                # Recorrer todos los archivos en MEDIA_ROOT
                for root, dirs, files in os.walk(media_root):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Calcular la URL relativa
                        relative_path = os.path.relpath(file_path, media_root)
                        url_path = f"{media_url}/{relative_path.replace(os.sep, '/')}"
                        
                        # Añadir archivo a WhiteNoise
                        try:
                            with open(file_path, 'rb') as f:
                                self.files[url_path] = self.file_wrapper(
                                    f.read(),
                                    content_type=self.get_content_type(file_path)
                                )
                        except (OSError, IOError):
                            # Continuar si hay error leyendo el archivo
                            continue
    
    def get_content_type(self, file_path):
        """
        Determina el content-type basado en la extensión del archivo
        """
        import mimetypes
        content_type, _ = mimetypes.guess_type(file_path)
        return content_type or 'application/octet-stream'