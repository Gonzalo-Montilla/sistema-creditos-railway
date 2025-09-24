from django.contrib import admin
from .models import Cliente, Credito, Pago, Codeudor

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'cedula', 'celular', 'activo', 'fecha_registro']
    list_filter = ['activo', 'fecha_registro']
    search_fields = ['nombres', 'apellidos', 'cedula', 'celular']
    readonly_fields = ['fecha_registro']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombres', 'apellidos', 'cedula')
        }),
        ('Contacto', {
            'fields': ('celular', 'telefono_fijo', 'email', 'direccion', 'barrio')
        }),
        ('Referencias', {
            'fields': ('referencia1_nombre', 'referencia1_telefono', 'referencia2_nombre', 'referencia2_telefono')
        }),
        ('Documentos', {
            'fields': ('foto_rostro', 'foto_cedula_frontal', 'foto_cedula_trasera', 'foto_recibo_servicio')
        }),
        ('Estado', {
            'fields': ('activo', 'fecha_registro')
        }),
    )

@admin.register(Codeudor)
class CodeudorAdmin(admin.ModelAdmin):
    list_display = ['nombre_completo', 'cedula', 'celular', 'cliente', 'fecha_registro']
    list_filter = ['fecha_registro']
    search_fields = ['nombres', 'apellidos', 'cedula', 'celular', 'cliente__nombres', 'cliente__apellidos']
    readonly_fields = ['fecha_registro']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('cliente', 'nombres', 'apellidos', 'cedula')
        }),
        ('Contacto', {
            'fields': ('celular', 'direccion', 'barrio')
        }),
        ('Documentos', {
            'fields': ('foto_rostro', 'foto_cedula_frontal', 'foto_cedula_trasera')
        }),
        ('Metadatos', {
            'fields': ('fecha_registro',)
        }),
    )

@admin.register(Credito)
class CreditoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'monto', 'tasa_interes', 'plazo_meses', 'estado', 'fecha_solicitud']
    list_filter = ['estado', 'fecha_solicitud', 'fecha_aprobacion']
    search_fields = ['cliente__nombres', 'cliente__apellidos', 'cliente__cedula']
    readonly_fields = ['fecha_solicitud', 'fecha_aprobacion']

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['credito', 'monto', 'numero_cuota', 'fecha_pago']
    list_filter = ['fecha_pago']
    search_fields = ['credito__cliente__nombres', 'credito__cliente__apellidos']
    readonly_fields = ['fecha_pago']
