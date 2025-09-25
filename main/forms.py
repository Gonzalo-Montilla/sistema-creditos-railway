from django import forms
from django.core.exceptions import ValidationError
from .models import Cliente, Credito, Pago, Codeudor, CronogramaPago, Cobrador, Ruta

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            # Información personal básica
            'nombres', 'apellidos', 'cedula',
            # Información de contacto
            'celular', 'telefono_fijo', 'email', 'direccion', 'barrio',
            # Referencias familiares
            'referencia1_nombre', 'referencia1_telefono', 
            'referencia2_nombre', 'referencia2_telefono',
            # Documentos y fotos
            'foto_rostro', 'foto_cedula_frontal', 'foto_cedula_trasera', 'foto_recibo_servicio',
            # Estado
            'activo'
        ]
        widgets = {
            # Información personal
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres del cliente'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos del cliente'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de cédula (5-10 dígitos)'}),
            
            # Contacto
            'celular': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Celular (obligatorio)'}),
            'telefono_fijo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono fijo (opcional)'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico (opcional)'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Dirección completa'}),
            'barrio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barrio o sector'}),
            
            # Referencias familiares
            'referencia1_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo de la primera referencia'}),
            'referencia1_telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono de la primera referencia'}),
            'referencia2_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo de la segunda referencia'}),
            'referencia2_telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono de la segunda referencia'}),
            
            # Documentos
            'foto_rostro': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'foto_cedula_frontal': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'foto_cedula_trasera': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'foto_recibo_servicio': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            
            # Estado
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CodeudorForm(forms.ModelForm):
    class Meta:
        model = Codeudor
        fields = ['nombres', 'apellidos', 'cedula', 'celular', 'direccion', 'barrio', 
                 'foto_rostro', 'foto_cedula_frontal', 'foto_cedula_trasera']
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres del codeudor'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos del codeudor'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cédula del codeudor (5-10 dígitos)'}),
            'celular': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Celular del codeudor'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Dirección completa'}),
            'barrio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barrio'}),
            'foto_rostro': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'foto_cedula_frontal': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'foto_cedula_trasera': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

class CreditoForm(forms.ModelForm):
    # Campo para búsqueda por cédula (no se guarda en el modelo)
    cedula_cliente = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese la cédula del cliente (5-10 dígitos)',
            'id': 'cedula_cliente',
            'autocomplete': 'off'
        }),
        label='Cédula del Cliente'
    )
    
    # Campo oculto para el cliente encontrado
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        widget=forms.HiddenInput(),
        required=False  # Se asignará en el método clean
    )
    
    class Meta:
        model = Credito
        fields = ['cliente', 'monto', 'tasa_interes', 'tipo_plazo', 'cantidad_cuotas', 'cobrador', 'estado']
        widgets = {
            'monto': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': 'Monto del crédito',
                'id': 'monto'
            }),
            'tasa_interes': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': 'Tasa de interés mensual (%) - Ej: 20',
                'id': 'tasa_interes'
            }),
            'tipo_plazo': forms.Select(attrs={
                'class': 'form-select',
                'id': 'tipo_plazo'
            }),
            'cantidad_cuotas': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Cantidad de cuotas',
                'id': 'cantidad_cuotas',
                'min': '1'
            }),
            'cobrador': forms.Select(attrs={
                'class': 'form-select',
                'id': 'cobrador'
            }),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar el campo cobrador para mostrar solo cobradores activos
        self.fields['cobrador'].queryset = Cobrador.objects.filter(activo=True)
        self.fields['cobrador'].empty_label = "Seleccionar cobrador (opcional)"
        
        # Si estamos editando, llenar la cédula del cliente
        if self.instance and self.instance.pk and hasattr(self.instance, 'cliente') and self.instance.cliente:
            self.fields['cedula_cliente'].initial = self.instance.cliente.cedula
    
    def clean_cedula_cliente(self):
        cedula = self.cleaned_data.get('cedula_cliente')
        if not cedula:
            raise ValidationError('La cédula del cliente es requerida.')
        
        try:
            cliente = Cliente.objects.get(cedula=cedula, activo=True)
            return cedula
        except Cliente.DoesNotExist:
            raise ValidationError(
                f'No se encontró ningún cliente activo con la cédula "{cedula}". '
                'Verifique que el cliente esté registrado y activo en el sistema.'
            )
    
    def clean(self):
        cleaned_data = super().clean()
        cedula = cleaned_data.get('cedula_cliente')
        monto = cleaned_data.get('monto')
        tasa_interes = cleaned_data.get('tasa_interes')
        cantidad_cuotas = cleaned_data.get('cantidad_cuotas')
        
        # Asignar el cliente al campo oculto
        if cedula:
            try:
                cliente = Cliente.objects.get(cedula=cedula, activo=True)
                cleaned_data['cliente'] = cliente
            except Cliente.DoesNotExist:
                # El error ya se manejó en clean_cedula_cliente
                pass
        
        # Validaciones adicionales
        if monto and monto <= 0:
            raise ValidationError({'monto': 'El monto debe ser mayor a cero.'})
        
        if tasa_interes and tasa_interes < 0:
            raise ValidationError({'tasa_interes': 'La tasa de interés no puede ser negativa.'})
        
        if cantidad_cuotas and cantidad_cuotas <= 0:
            raise ValidationError({'cantidad_cuotas': 'La cantidad de cuotas debe ser mayor a cero.'})
        
        return cleaned_data

class PagoForm(forms.ModelForm):
    # Campo para búsqueda por cédula (no se guarda en el modelo)
    cedula_cliente = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese la cédula del cliente para buscar sus créditos (5-10 dígitos)',
            'id': 'cedula_cliente_pago',
            'autocomplete': 'off'
        }),
        label='Cédula del Cliente'
    )
    
    # Campo oculto para el cliente encontrado
    cliente_encontrado = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        widget=forms.HiddenInput(),
        required=False
    )
    
    class Meta:
        model = Pago
        fields = ['credito', 'monto', 'numero_cuota', 'observaciones']
        widgets = {
            'credito': forms.Select(attrs={
                'class': 'form-select', 
                'id': 'credito_select',
                'disabled': True  # Se habilitará cuando se encuentre un cliente
            }),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Monto del pago'}),
            'numero_cuota': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Número de cuota'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observaciones (opcional)'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicialmente vacío hasta que se busque un cliente
        self.fields['credito'].queryset = Credito.objects.none()
        
        # Si estamos editando, llenar la cédula del cliente
        if self.instance and self.instance.pk and hasattr(self.instance, 'credito') and self.instance.credito:
            self.fields['cedula_cliente'].initial = self.instance.credito.cliente.cedula
            # Mostrar créditos del cliente actual
            self.fields['credito'].queryset = Credito.objects.filter(
                cliente=self.instance.credito.cliente,
                estado__in=['APROBADO', 'DESEMBOLSADO']
            ).exclude(estado='PAGADO')
            self.fields['credito'].widget.attrs.pop('disabled', None)
    
    def clean_cedula_cliente(self):
        cedula = self.cleaned_data.get('cedula_cliente')
        if not cedula:
            raise ValidationError('La cédula del cliente es requerida.')
        
        try:
            cliente = Cliente.objects.get(cedula=cedula, activo=True)
            return cedula
        except Cliente.DoesNotExist:
            raise ValidationError(
                f'No se encontró ningún cliente activo con la cédula "{cedula}".'
            )
    
    def clean(self):
        cleaned_data = super().clean()
        credito = cleaned_data.get('credito')
        monto = cleaned_data.get('monto')
        numero_cuota = cleaned_data.get('numero_cuota')
        
        # Validar que se haya seleccionado un crédito
        if not credito:
            raise ValidationError({
                'credito': 'Debe seleccionar un crédito para aplicar el pago.'
            })
        
        # Validar monto con validaciones específicas para pesos colombianos
        if not monto or monto <= 0:
            raise ValidationError({
                'monto': 'El monto debe ser mayor a cero.'
            })
        
        # Validaciones específicas para pesos colombianos
        # Permitir desde $50 para casos excepcionales (pagos parciales, etc.)
        if monto < 50:
            raise ValidationError({
                'monto': f'El monto ${monto:,.0f} parece muy bajo para un pago en pesos colombianos.'
            })
        
        if monto > 50000000:  # 50 millones COP
            raise ValidationError({
                'monto': f'El monto ${monto:,.0f} parece excesivo. Verifique el valor ingresado.'
            })
        
        # Validar número de cuota
        if not numero_cuota or numero_cuota <= 0:
            raise ValidationError({
                'numero_cuota': 'El número de cuota debe ser mayor a cero.'
            })
        
        if credito and monto:
            try:
                # Verificar si el crédito puede recibir pagos
                if not credito.puede_recibir_pagos():
                    raise ValidationError({
                        'credito': f'El crédito #{credito.id} no puede recibir pagos en su estado actual.'
                    })
                
                # Verificar si el monto no excede el saldo pendiente
                saldo_pendiente = credito.saldo_pendiente()
                if monto > saldo_pendiente:
                    raise ValidationError({
                        'monto': f'El monto (${monto:,.2f}) excede el saldo pendiente (${saldo_pendiente:,.2f}).'
                    })
                
                # Validar que la cuota no exceda el total de cuotas
                if numero_cuota > credito.cantidad_cuotas:
                    raise ValidationError({
                        'numero_cuota': f'El número de cuota no puede ser mayor a {credito.cantidad_cuotas}.'
                    })
                    
            except Exception as e:
                raise ValidationError(
                    f'Error al validar el crédito: {str(e)}'
                )
        
        return cleaned_data

# ========================================
# FORMULARIOS PARA COBRADORES Y RUTAS
# ========================================

class CobradorForm(forms.ModelForm):
    class Meta:
        model = Cobrador
        fields = [
            'nombres', 'apellidos', 'tipo_documento', 'numero_documento',
            'celular', 'email', 'direccion',
            'rutas', 'fecha_ingreso', 'activo',
            'comision_porcentaje', 'meta_diaria'
        ]
        widgets = {
            'nombres': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nombres del cobrador'
            }),
            'apellidos': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Apellidos del cobrador'
            }),
            'tipo_documento': forms.Select(attrs={
                'class': 'form-select'
            }),
            'numero_documento': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Número de documento'
            }),
            'celular': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Número de celular (ej: 3001234567)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Correo electrónico (opcional)'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Dirección de residencia completa'
            }),
            'rutas': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'fecha_ingreso': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'comision_porcentaje': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'placeholder': 'Porcentaje de comisión (ej: 5.00)'
            }),
            'meta_diaria': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01',
                'placeholder': 'Meta diaria de cobros en pesos'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que las rutas se muestren mejor
        self.fields['rutas'].queryset = Ruta.objects.filter(activa=True)
        self.fields['rutas'].widget.attrs.update({'class': 'form-check-input'})
    
    def clean_numero_documento(self):
        numero = self.cleaned_data.get('numero_documento')
        if not numero:
            raise ValidationError('El número de documento es requerido.')
        
        # Verificar que no exista otro cobrador con el mismo documento
        if self.instance.pk:
            # Editando - excluir el actual
            existe = Cobrador.objects.filter(
                numero_documento=numero
            ).exclude(pk=self.instance.pk).exists()
        else:
            # Creando nuevo
            existe = Cobrador.objects.filter(numero_documento=numero).exists()
        
        if existe:
            raise ValidationError(
                f'Ya existe un cobrador registrado con el documento "{numero}"'
            )
        
        return numero
    
    def clean_comision_porcentaje(self):
        comision = self.cleaned_data.get('comision_porcentaje')
        if comision and (comision < 0 or comision > 100):
            raise ValidationError(
                'La comisión debe estar entre 0% y 100%'
            )
        return comision
    
    def clean_meta_diaria(self):
        meta = self.cleaned_data.get('meta_diaria')
        if meta and meta < 0:
            raise ValidationError(
                'La meta diaria no puede ser negativa'
            )
        return meta

class RutaForm(forms.ModelForm):
    class Meta:
        model = Ruta
        fields = ['nombre', 'descripcion', 'barrios', 'zona', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nombre descriptivo de la ruta (ej: Ruta Norte)'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Descripción detallada de la ruta y su cobertura'
            }),
            'barrios': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Lista de barrios separados por comas (ej: Centro, La Esperanza, San José)'
            }),
            'zona': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Zona o sector general (ej: Norte, Sur, Centro)'
            }),
            'activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_barrios(self):
        barrios = self.cleaned_data.get('barrios', '')
        if not barrios or not barrios.strip():
            raise ValidationError(
                'Debe especificar al menos un barrio para la ruta'
            )
        
        # Limpiar y validar la lista de barrios
        lista_barrios = [barrio.strip() for barrio in barrios.split(',') if barrio.strip()]
        
        if not lista_barrios:
            raise ValidationError(
                'Debe especificar al menos un barrio válido'
            )
        
        if len(lista_barrios) > 50:
            raise ValidationError(
                'No se pueden especificar más de 50 barrios por ruta'
            )
        
        # Verificar longitud de nombres
        barrios_largos = [b for b in lista_barrios if len(b) > 100]
        if barrios_largos:
            raise ValidationError(
                f'Los siguientes barrios tienen nombres demasiado largos: {", ".join(barrios_largos[:3])}'
            )
        
        # Retornar los barrios limpios
        return ', '.join(lista_barrios)
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if not nombre:
            raise ValidationError('El nombre de la ruta es requerido')
        
        # Verificar que no exista otra ruta con el mismo nombre
        if self.instance.pk:
            # Editando - excluir la actual
            existe = Ruta.objects.filter(
                nombre__iexact=nombre
            ).exclude(pk=self.instance.pk).exists()
        else:
            # Creando nueva
            existe = Ruta.objects.filter(nombre__iexact=nombre).exists()
        
        if existe:
            raise ValidationError(
                f'Ya existe una ruta con el nombre "{nombre}"'
            )
        
        return nombre
