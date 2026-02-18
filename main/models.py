from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# Validadores personalizados
cedula_validator = RegexValidator(
    regex=r'^\d{5,10}$',
    message="La cédula debe tener entre 5 y 10 dígitos numéricos"
)

celular_validator = RegexValidator(
    regex=r'^3[0-9]{9}$',
    message="El celular debe tener 10 dígitos y empezar con 3 (ej: 3001234567)"
)

telefono_fijo_validator = RegexValidator(
    regex=r'^[2-8][0-9]{6,7}$',
    message="El teléfono fijo debe tener 7-8 dígitos (ej: 6012345)"
)

class Cliente(models.Model):
    # Información personal básica
    nombres = models.CharField(max_length=100, verbose_name="Nombres", default="")
    apellidos = models.CharField(max_length=100, verbose_name="Apellidos", default="")
    cedula = models.CharField(
        max_length=20, 
        unique=True, 
        validators=[cedula_validator],
        verbose_name="Cédula",
        help_text="Entre 5 y 10 dígitos numéricos"
    )
    
    # Información de contacto
    celular = models.CharField(
        max_length=15, 
        validators=[celular_validator],
        verbose_name="Celular",
        default="",
        help_text="10 dígitos empezando con 3 (ej: 3001234567)"
    )
    telefono_fijo = models.CharField(
        max_length=15, 
        validators=[telefono_fijo_validator],
        verbose_name="Teléfono fijo", 
        blank=True, 
        null=True,
        help_text="7-8 dígitos (ej: 6012345)"
    )
    email = models.EmailField(verbose_name="Correo electrónico", blank=True, null=True)
    direccion = models.TextField(verbose_name="Dirección completa", default="")
    barrio = models.CharField(max_length=100, verbose_name="Barrio", default="")
    # Referencias familiares (2 referencias)
    referencia1_nombre = models.CharField(max_length=100, verbose_name="Referencia 1 - Nombre", blank=True, null=True)
    referencia1_telefono = models.CharField(
        max_length=15, 
        validators=[celular_validator],
        verbose_name="Referencia 1 - Teléfono", 
        blank=True, 
        null=True,
        help_text="Celular 10 dígitos (3xxxxxxxxx)"
    )
    referencia2_nombre = models.CharField(max_length=100, verbose_name="Referencia 2 - Nombre", blank=True, null=True)
    referencia2_telefono = models.CharField(
        max_length=15, 
        validators=[celular_validator],
        verbose_name="Referencia 2 - Teléfono", 
        blank=True, 
        null=True,
        help_text="Celular 10 dígitos (3xxxxxxxxx)"
    )
    
    # Documentos y fotos
    foto_rostro = models.ImageField(upload_to='clientes/rostros/', verbose_name="Foto del rostro", blank=True, null=True)
    foto_cedula_frontal = models.ImageField(upload_to='clientes/cedulas/', verbose_name="Cédula - Frente", blank=True, null=True)
    foto_cedula_trasera = models.ImageField(upload_to='clientes/cedulas/', verbose_name="Cédula - Atrás", blank=True, null=True)
    foto_recibo_servicio = models.ImageField(upload_to='clientes/servicios/', verbose_name="Recibo de servicio público", blank=True, null=True)
    
    # Metadatos
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    # Habeas Data (Ley 1581 de 2012) - autorización de tratamiento de datos
    documento_habeas_data = models.FileField(
        upload_to='habeas_data/clientes/',
        verbose_name='Autorización Habeas Data (PDF)',
        blank=True,
        null=True
    )
    fecha_autorizacion_habeas_data = models.DateTimeField(
        verbose_name='Fecha autorización Habeas Data',
        null=True,
        blank=True
    )
    codigo_habeas_data = models.CharField(
        max_length=20,
        verbose_name='Código único documento Habeas Data',
        blank=True,
        null=True,
        help_text='Ej: HD-2025-C000123 (para verificación del documento)'
    )

    # Documento de renovación de crédito (último firmado por OTP)
    documento_renovacion = models.FileField(
        upload_to='renovaciones/',
        verbose_name='Documento de renovación (PDF)',
        blank=True,
        null=True,
    )
    fecha_firma_renovacion = models.DateTimeField(
        verbose_name='Fecha firma documento de renovación',
        null=True,
        blank=True,
    )
    codigo_renovacion = models.CharField(
        max_length=20,
        verbose_name='Código único documento renovación',
        blank=True,
        null=True,
        help_text='Ej: REN-2025-000123',
    )
    
    # Campos de compatibilidad (para no romper el código existente)
    @property
    def nombre(self):
        return f"{self.nombres} {self.apellidos}"
    
    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
    
    @property
    def telefono(self):
        return self.celular

    def tiene_habeas_data_firmado(self):
        """True si el cliente tiene autorización Habeas Data firmada (OTP validado)."""
        return bool(self.fecha_autorizacion_habeas_data and self.documento_habeas_data)

    def tiene_documento_renovacion(self):
        """True si el cliente tiene al menos un documento de renovación firmado (se muestra el último)."""
        return bool(self.fecha_firma_renovacion and self.documento_renovacion)

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.cedula}"

class Codeudor(models.Model):
    # Relación con el cliente
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name='codeudor')
    
    # Información personal básica
    nombres = models.CharField(max_length=100, verbose_name="Nombres")
    apellidos = models.CharField(max_length=100, verbose_name="Apellidos")
    cedula = models.CharField(
        max_length=20, 
        unique=True,  # 🔥 CORRECCIÓN: Evitar duplicados
        validators=[cedula_validator],
        verbose_name="Cédula",
        help_text="Entre 5 y 10 dígitos numéricos (no puede repetirse)"
    )
    
    # Información de contacto
    celular = models.CharField(
        max_length=15, 
        validators=[celular_validator],
        verbose_name="Celular",
        help_text="10 dígitos empezando con 3 (ej: 3001234567)"
    )
    direccion = models.TextField(verbose_name="Dirección completa")
    barrio = models.CharField(max_length=100, verbose_name="Barrio")
    
    email = models.EmailField(verbose_name="Correo electrónico", blank=True, null=True)
    
    # Documentos y fotos
    foto_rostro = models.ImageField(upload_to='codeudores/rostros/', verbose_name="Foto del rostro", blank=True, null=True)
    foto_cedula_frontal = models.ImageField(upload_to='codeudores/cedulas/', verbose_name="Cédula - Frente", blank=True, null=True)
    foto_cedula_trasera = models.ImageField(upload_to='codeudores/cedulas/', verbose_name="Cédula - Atrás", blank=True, null=True)
    
    # Habeas Data (Ley 1581 de 2012)
    documento_habeas_data = models.FileField(
        upload_to='habeas_data/codeudores/',
        verbose_name='Autorización Habeas Data (PDF)',
        blank=True,
        null=True
    )
    fecha_autorizacion_habeas_data = models.DateTimeField(
        verbose_name='Fecha autorización Habeas Data',
        null=True,
        blank=True
    )
    codigo_habeas_data = models.CharField(
        max_length=20,
        verbose_name='Código único documento Habeas Data',
        blank=True,
        null=True,
        help_text='Ej: HD-2025-D000045 (para verificación del documento)'
    )
    
    # Metadatos
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True, verbose_name="Codeudor activo")
    
    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
    
    def tiene_habeas_data_firmado(self):
        """True si el codeudor tiene autorización Habeas Data firmada."""
        return bool(self.fecha_autorizacion_habeas_data and self.documento_habeas_data)

    def __str__(self):
        return f"Codeudor: {self.nombres} {self.apellidos} - {self.cedula}"


class HabeasDataOTP(models.Model):
    """OTP pendiente para firma digital de autorización Habeas Data (Ley 1581/2012)."""
    TIPO_CHOICES = [('cliente', 'Cliente'), ('codeudor', 'Codeudor')]
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    objeto_id = models.PositiveIntegerField(help_text='ID del Cliente o Codeudor')
    otp_hash = models.CharField(max_length=64)  # SHA-256 del OTP
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['tipo', 'objeto_id']),
            models.Index(fields=['expires_at']),
        ]


class Credito(models.Model):
    ESTADOS = [
        ('SOLICITADO', 'Solicitado'),
        ('APROBADO', 'Aprobado'),
        ('DESEMBOLSADO', 'Desembolsado'),
        ('PAGADO', 'Pagado'),
        ('RECHAZADO', 'Rechazado'),
        ('VENCIDO', 'Vencido'),
    ]
    
    TIPOS_PLAZO = [
        ('DIARIO', 'Diario'),
        ('SEMANAL', 'Semanal'),
        ('QUINCENAL', 'Quincenal'),
        ('MENSUAL', 'Mensual'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    cobrador = models.ForeignKey('Cobrador', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Cobrador asignado")
    monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto del crédito")
    tasa_interes = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Tasa de interés (%)")
    
    # Nuevos campos de plazo
    tipo_plazo = models.CharField(max_length=10, choices=TIPOS_PLAZO, default='MENSUAL', verbose_name="Tipo de plazo")
    cantidad_cuotas = models.IntegerField(default=1, verbose_name="Cantidad de cuotas")
    plazo_meses = models.IntegerField(null=True, blank=True, verbose_name="Plazo en meses (calculado)")  # Campo calculado para compatibilidad
    
    # Información del cronograma de pagos
    valor_cuota = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valor de cada cuota")
    total_interes = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total interés a pagar")
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Monto total a pagar")
    descripcion_pago = models.TextField(blank=True, default='', verbose_name="Descripción del pago")
    
    # Estados y fechas
    estado = models.CharField(max_length=15, choices=ESTADOS, default='SOLICITADO')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    fecha_desembolso = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de desembolso")

    # Pagaré electrónico (firma OTP antes del desembolso)
    documento_pagare = models.FileField(
        upload_to='pagares/',
        verbose_name='Pagaré firmado (PDF)',
        blank=True,
        null=True,
    )
    fecha_firma_pagare = models.DateTimeField(
        verbose_name='Fecha firma del pagaré',
        null=True,
        blank=True,
    )
    codigo_pagare = models.CharField(
        max_length=20,
        verbose_name='Código único documento pagaré',
        blank=True,
        null=True,
        help_text='Ej: PG-2025-000001',
    )
    pagare_firmado_cliente = models.DateTimeField(
        verbose_name='Fecha OTP validado - Cliente',
        null=True,
        blank=True,
    )
    pagare_firmado_codeudor = models.DateTimeField(
        verbose_name='Fecha OTP validado - Codeudor',
        null=True,
        blank=True,
    )
    
    # Gestión de mora y cartera
    fecha_vencimiento = models.DateField(null=True, blank=True, verbose_name="Fecha de vencimiento calculada")
    dias_mora = models.IntegerField(default=0, verbose_name="Días de mora")
    estado_mora = models.CharField(max_length=20, default='AL_DIA', verbose_name="Estado de mora",
                                   choices=[
                                       ('AL_DIA', 'Al día'),
                                       ('MORA_TEMPRANA', 'Mora temprana (1-30 días)'),
                                       ('MORA_ALTA', 'Mora alta (31-90 días)'),
                                       ('MORA_CRITICA', 'Mora crítica (+90 días)')
                                   ])
    interes_moratorio = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Interés moratorio acumulado")
    tasa_mora = models.DecimalField(max_digits=5, decimal_places=2, default=2.0, verbose_name="Tasa de mora diaria (%)")

    # Retanqueo: trazabilidad cuando este crédito reemplaza a otro
    credito_retanqueado = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credito_nuevo_por_retanqueo',
        verbose_name='Crédito anterior (retanqueo)',
    )
    monto_aplicado_credito_anterior = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Monto aplicado al crédito anterior en retanqueo',
    )
    es_renovacion = models.BooleanField(
        default=False,
        verbose_name='Crédito por renovación (no requiere pagaré, sí doc. renovación)',
    )
    # Documento de retanqueo firmado con OTP (solo para créditos creados por retanqueo)
    documento_retanqueo = models.FileField(
        upload_to='retanqueos/',
        verbose_name='Documento de retanqueo firmado (PDF)',
        blank=True,
        null=True,
    )
    fecha_firma_retanqueo = models.DateTimeField(
        verbose_name='Fecha firma documento retanqueo',
        null=True,
        blank=True,
    )
    codigo_retanqueo = models.CharField(
        max_length=32,
        verbose_name='Código documento retanqueo',
        blank=True,
        null=True,
    )
    # Documento de renovación firmado con OTP (solo para créditos marcados como renovación)
    documento_renovacion = models.FileField(
        upload_to='renovaciones/creditos/',
        verbose_name='Documento de renovación firmado (PDF)',
        blank=True,
        null=True,
    )
    fecha_firma_renovacion = models.DateTimeField(
        verbose_name='Fecha firma documento renovación',
        null=True,
        blank=True,
    )
    codigo_renovacion = models.CharField(
        max_length=32,
        verbose_name='Código documento renovación',
        blank=True,
        null=True,
    )

    def tiene_documento_retanqueo_firmado(self):
        """True si es crédito por retanqueo y el cliente ya firmó el documento con OTP."""
        return bool(
            self.credito_retanqueado_id
            and self.documento_retanqueo
            and self.fecha_firma_retanqueo
        )

    def tiene_documento_renovacion_firmado(self):
        """True si es crédito de renovación y el cliente ya firmó el documento con OTP."""
        return bool(
            self.es_renovacion
            and self.documento_renovacion
            and self.fecha_firma_renovacion
        )

    def sugerir_cobrador(self):
        """Sugiere un cobrador basado en el barrio del cliente"""
        if self.cliente.barrio:
            # Buscar rutas que incluyan el barrio del cliente
            rutas_posibles = Ruta.objects.filter(
                barrios__icontains=self.cliente.barrio.strip(),
                activa=True
            )
            
            for ruta in rutas_posibles:
                if self.cliente.barrio.strip().lower() in [b.lower() for b in ruta.get_barrios_lista()]:
                    # Buscar cobradores activos asignados a esta ruta
                    cobradores = ruta.cobradores.filter(activo=True)
                    if cobradores.exists():
                        # Retornar el cobrador con menos créditos activos (balance de carga)
                        cobrador_sugerido = min(cobradores, key=lambda c: c.creditos_activos().count())
                        return cobrador_sugerido
        return None
    
    def asignar_cobrador_automaticamente(self, forzar=False):
        """Asigna automáticamente un cobrador (solo si no tiene uno o se fuerza)"""
        if not self.cobrador or forzar:
            cobrador_sugerido = self.sugerir_cobrador()
            if cobrador_sugerido:
                self.cobrador = cobrador_sugerido
                return True
        return False
    
    def save(self, *args, **kwargs):
        """Calcular campos automáticos al guardar"""
        # Sugerir cobrador automáticamente solo si no tiene uno asignado
        # (La asignación manual tiene prioridad)
        if not self.cobrador:
            self.asignar_cobrador_automaticamente()
        
        # Calcular plazo en meses para compatibilidad usando función centralizada
        from .creditos_utils import calcular_plazo_en_meses
        self.plazo_meses = round(calcular_plazo_en_meses(self.cantidad_cuotas, self.tipo_plazo), 1)
            
        # Calcular cronograma si no está calculado
        if not self.valor_cuota:
            self.calcular_cronograma()
            
        super().save(*args, **kwargs)
    
    def calcular_cronograma(self):
        """Calcula el cronograma de pagos del crédito usando sistema de créditos informales"""
        from .creditos_utils import calcular_credito_informal, generar_descripcion_credito
        
        # Usar la función centralizada del valorizador
        resultado = calcular_credito_informal(
            monto=self.monto,
            tasa_mensual=self.tasa_interes,
            cantidad_cuotas=self.cantidad_cuotas,
            tipo_plazo=self.tipo_plazo
        )
        
        # Actualizar campos del modelo
        calculos = resultado['calculos']
        self.valor_cuota = calculos['valor_cuota']
        self.monto_total = calculos['monto_total']
        self.total_interes = calculos['interes_total']
        
        # Generar descripción usando la función centralizada
        self.descripcion_pago = generar_descripcion_credito(resultado)
    
    def obtener_fechas_pago(self):
        """Genera las fechas de pago basadas en la fecha de desembolso"""
        from .creditos_utils import generar_cronograma_fechas
        
        if not self.fecha_desembolso:
            return []
        
        # Usar función centralizada
        cronograma = generar_cronograma_fechas(
            cantidad_cuotas=self.cantidad_cuotas,
            tipo_plazo=self.tipo_plazo,
            fecha_inicio=self.fecha_desembolso.date() if hasattr(self.fecha_desembolso, 'date') else self.fecha_desembolso
        )
        
        # Retornar solo las fechas para compatibilidad
        return [item['fecha_objeto'] for item in cronograma]
    
    def generar_cronograma(self):
        """Genera el cronograma de pagos en la base de datos usando la lógica centralizada"""
        from .creditos_utils import generar_cronograma_fechas
        
        if not self.fecha_desembolso:
            return
        
        # Eliminar cronograma anterior si existe
        self.cronograma.all().delete()
        
        # Usar función centralizada para generar el cronograma completo
        cronograma = generar_cronograma_fechas(
            cantidad_cuotas=self.cantidad_cuotas,
            tipo_plazo=self.tipo_plazo,
            fecha_inicio=self.fecha_desembolso.date() if hasattr(self.fecha_desembolso, 'date') else self.fecha_desembolso
        )
        
        # Crear registros en la base de datos
        for cuota_info in cronograma:
            CronogramaPago.objects.create(
                credito=self,
                numero_cuota=cuota_info['numero_cuota'],
                fecha_vencimiento=cuota_info['fecha_objeto'],
                monto_cuota=self.valor_cuota
            )
    
    def tiene_pagare_firmado(self):
        """True si el pagaré está firmado (cliente y codeudor si existe) y el PDF está guardado."""
        if not (self.documento_pagare and self.fecha_firma_pagare):
            return False
        try:
            if self.cliente.codeudor and not self.pagare_firmado_codeudor:
                return False
        except Codeudor.DoesNotExist:
            pass
        return True

    def requiere_pagare_para_desembolso(self):
        """True si este crédito exige firma de pagaré (primer crédito normal). Retanqueo y renovación no."""
        return not self.credito_retanqueado_id and not self.es_renovacion

    def puede_desembolsar_segun_firma(self):
        """True si ya cumplió la firma exigida: pagaré (normal), doc. renovación (renovación), doc. retanqueo (retanqueo)."""
        if self.credito_retanqueado_id:
            return self.tiene_documento_retanqueo_firmado()
        if self.es_renovacion:
            return self.tiene_documento_renovacion_firmado()
        return self.tiene_pagare_firmado()

    def __str__(self):
        return f"Crédito {self.id} - {self.cliente.nombre_completo} - ${self.monto}"
    
    def total_pagado(self):
        """Calcula el total pagado en este crédito"""
        try:
            total = self.pago_set.aggregate(total=models.Sum('monto'))['total']
            return total if total is not None else 0
        except Exception:
            return 0
    
    def saldo_pendiente(self):
        """Calcula el saldo pendiente por pagar"""
        try:
            monto_total = self.monto_total if self.monto_total else self.monto
            total_pagado = self.total_pagado()
            saldo = monto_total - total_pagado
            return max(0, saldo)  # No permitir saldos negativos
        except Exception:
            return self.monto_total if self.monto_total else self.monto

    def saldo_a_liquidar(self):
        """
        Saldo a liquidar para retanqueo: capital pendiente + intereses normales a la fecha.
        Coincide con lo que el cliente debe al día (saldo pendiente del crédito).
        """
        return self.saldo_pendiente()

    def puede_retanquear(self):
        """
        True si el crédito está desembolsado, tiene saldo pendiente y el cliente
        ha pagado al menos el 25% del crédito (monto total a pagar).
        """
        if self.estado not in ('DESEMBOLSADO', 'VENCIDO') or self.saldo_pendiente() <= 0:
            return False
        monto_total_credito = self.monto_total if self.monto_total else self.monto
        if not monto_total_credito or monto_total_credito <= 0:
            return False
        total_pagado = self.total_pagado()
        umbral_25 = monto_total_credito * Decimal('0.25')
        return total_pagado >= umbral_25

    def puede_recibir_pagos(self):
        """Verifica si el crédito puede recibir más pagos"""
        try:
            return self.estado in ['APROBADO', 'DESEMBOLSADO'] and self.saldo_pendiente() > 0
        except Exception:
            return False
    
    def esta_al_dia(self):
        """Verifica si el crédito está completamente pagado"""
        try:
            return self.saldo_pendiente() <= 0
        except Exception:
            return False
    
    def calcular_mora(self):
        """Calcula y actualiza el estado de mora del crédito"""
        from datetime import date
        
        if not self.fecha_desembolso or self.estado not in ['DESEMBOLSADO']:
            return
        
        # Si no hay fecha de vencimiento calculada, usar la próxima cuota vencida
        if not self.fecha_vencimiento:
            cuota_vencida = self.cronograma.filter(
                estado__in=['PENDIENTE', 'PARCIAL'],
                fecha_vencimiento__lt=date.today()
            ).order_by('fecha_vencimiento').first()
            
            if cuota_vencida:
                self.fecha_vencimiento = cuota_vencida.fecha_vencimiento
            else:
                # Si no hay cuotas vencidas, no hay mora
                self.dias_mora = 0
                self.estado_mora = 'AL_DIA'
                return
        
        # Calcular días de mora
        if self.fecha_vencimiento < date.today():
            self.dias_mora = (date.today() - self.fecha_vencimiento).days
        else:
            self.dias_mora = 0
        
        # Determinar estado de mora
        if self.dias_mora <= 0:
            self.estado_mora = 'AL_DIA'
        elif self.dias_mora <= 30:
            self.estado_mora = 'MORA_TEMPRANA'
        elif self.dias_mora <= 90:
            self.estado_mora = 'MORA_ALTA'
        else:
            self.estado_mora = 'MORA_CRITICA'
    
    def calcular_interes_moratorio(self):
        """Calcula el interés moratorio acumulado"""
        from decimal import Decimal
        
        if self.dias_mora <= 0:
            self.interes_moratorio = 0
            return 0
        
        # Calcular interés moratorio sobre el saldo pendiente
        saldo = Decimal(str(self.saldo_pendiente()))
        tasa_diaria = self.tasa_mora / Decimal('100')
        interes = saldo * tasa_diaria * Decimal(str(self.dias_mora))
        
        self.interes_moratorio = interes
        return interes
    
    def actualizar_estado_cartera(self):
        """Actualiza completamente el estado de cartera del crédito"""
        self.calcular_mora()
        self.calcular_interes_moratorio()
        
        # Cambiar estado a VENCIDO si está en mora crítica
        if self.estado_mora == 'MORA_CRITICA' and self.estado == 'DESEMBOLSADO':
            self.estado = 'VENCIDO'
        
        self.save(update_fields=[
            'fecha_vencimiento', 'dias_mora', 'estado_mora', 
            'interes_moratorio', 'estado'
        ])
    
    def get_color_mora(self):
        """Retorna el color CSS según el estado de mora"""
        colores = {
            'AL_DIA': 'success',
            'MORA_TEMPRANA': 'warning', 
            'MORA_ALTA': 'danger',
            'MORA_CRITICA': 'dark'
        }
        return colores.get(self.estado_mora, 'secondary')


class PagareOTP(models.Model):
    """OTP pendiente para firma del pagaré (deudor y codeudor por crédito)."""
    TIPO_FIRMANTE = [('cliente', 'Cliente'), ('codeudor', 'Codeudor')]
    credito = models.ForeignKey(Credito, on_delete=models.CASCADE, related_name='pagare_otps')
    tipo_firmante = models.CharField(max_length=10, choices=TIPO_FIRMANTE)
    otp_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['credito', 'tipo_firmante']),
            models.Index(fields=['expires_at']),
        ]


class RenovacionOTP(models.Model):
    """OTP pendiente para firma del documento de renovación (términos del crédito indicado)."""
    credito = models.ForeignKey('Credito', on_delete=models.CASCADE, related_name='renovacion_otps')
    otp_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class RetanqueoOTP(models.Model):
    """OTP pendiente para firma del documento de retanqueo."""
    credito = models.ForeignKey('Credito', on_delete=models.CASCADE, related_name='retanqueo_otps')
    otp_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class CronogramaPago(models.Model):
    """Cronograma de pagos planificado para cada crédito"""
    ESTADOS_CUOTA = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADA', 'Pagada'),
        ('VENCIDA', 'Vencida'),
        ('PARCIAL', 'Pago Parcial'),
    ]
    
    credito = models.ForeignKey(Credito, on_delete=models.CASCADE, related_name='cronograma')
    numero_cuota = models.IntegerField(verbose_name="Número de cuota")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de vencimiento")
    monto_cuota = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto de la cuota")
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Monto pagado")
    estado = models.CharField(max_length=10, choices=ESTADOS_CUOTA, default='PENDIENTE')
    fecha_pago = models.DateField(null=True, blank=True, verbose_name="Fecha de pago real")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    
    class Meta:
        unique_together = ['credito', 'numero_cuota']
        ordering = ['numero_cuota']
    
    def saldo_pendiente(self):
        return self.monto_cuota - self.monto_pagado
    
    def esta_vencida(self):
        from datetime import date
        return self.fecha_vencimiento < date.today() and self.estado == 'PENDIENTE'
    
    def __str__(self):
        return f"Cuota {self.numero_cuota} - Crédito {self.credito.id} - ${self.monto_cuota}"

class Pago(models.Model):
    credito = models.ForeignKey(Credito, on_delete=models.CASCADE)
    cuota = models.ForeignKey(CronogramaPago, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Cuota asociada")
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    numero_cuota = models.IntegerField()
    observaciones = models.TextField(blank=True)
    
    def __str__(self):
        return f"Pago {self.id} - Crédito {self.credito.id} - ${self.monto}"

class CarteraAnalisis(models.Model):
    """Análisis diario de cartera para reportes y métricas"""
    fecha_analisis = models.DateField(auto_now_add=True, verbose_name="Fecha del análisis")
    
    # Métricas generales
    total_creditos_activos = models.IntegerField(default=0)
    cartera_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cartera_al_dia = models.DecimalField(max_digits=15, decimal_places=2, default=0) 
    cartera_vencida = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Métricas por estado de mora
    creditos_al_dia = models.IntegerField(default=0)
    creditos_mora_temprana = models.IntegerField(default=0)
    creditos_mora_alta = models.IntegerField(default=0)
    creditos_mora_critica = models.IntegerField(default=0)
    
    # Métricas de mora
    total_interes_moratorio = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    porcentaje_cartera_vencida = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    dias_mora_promedio = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    
    # Métricas de cobranza
    pagos_del_dia = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    meta_cobranza_diaria = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    porcentaje_cumplimiento_meta = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['-fecha_analisis']
        verbose_name = "Análisis de Cartera"
        verbose_name_plural = "Análisis de Cartera"
    
    def __str__(self):
        return f"Análisis de cartera - {self.fecha_analisis}"
    
    @classmethod
    def generar_analisis_diario_seguro(cls):
        """Versión mejorada y segura del análisis de cartera con datos reales"""
        from datetime import date
        from decimal import Decimal
        from django.db.models import Sum, Count, Avg
        from django.utils import timezone as tz
        
        try:
            hoy = date.today()
            
            # Limpiar análisis existente
            cls.objects.filter(fecha_analisis=hoy).delete()
            
            # Obtener créditos activos
            creditos_activos = Credito.objects.filter(estado__in=['DESEMBOLSADO', 'VENCIDO'])
            total_creditos = creditos_activos.count()
            
            # Cartera = saldo pendiente (lo que falta por cobrar), no monto_total
            try:
                from django.db.models.functions import Coalesce
                from django.db.models import Value
                from django.db.models import DecimalField
                qs = creditos_activos.annotate(
                    total_pagado=Coalesce(Sum('pago__monto'), Value(Decimal('0')), output_field=DecimalField())
                )
                cartera_total = Decimal('0')
                cartera_al_dia_monto = Decimal('0')
                for c in qs:
                    monto_total = c.monto_total or c.monto or Decimal('0')
                    saldo = max(Decimal('0'), monto_total - (c.total_pagado or Decimal('0')))
                    cartera_total += saldo
                    if c.estado_mora == 'AL_DIA':
                        cartera_al_dia_monto += saldo
                cartera_vencida_monto = cartera_total - cartera_al_dia_monto
            except Exception:
                cartera_total = Decimal('0')
                cartera_al_dia_monto = Decimal('0')
                cartera_vencida_monto = Decimal('0')
            
            # Contar por estado de mora
            creditos_al_dia = creditos_activos.filter(estado_mora='AL_DIA').count()
            creditos_mora_temp = creditos_activos.filter(estado_mora='MORA_TEMPRANA').count()
            creditos_mora_alta = creditos_activos.filter(estado_mora='MORA_ALTA').count()
            creditos_mora_crit = creditos_activos.filter(estado_mora='MORA_CRITICA').count()
            
            # Calcular porcentaje de cartera vencida
            try:
                porcentaje_vencida = (cartera_vencida_monto / cartera_total * Decimal('100')) if cartera_total > 0 else Decimal('0')
            except:
                porcentaje_vencida = Decimal('0')
            
            # Calcular pagos del día
            try:
                hoy_timezone = tz.now().date()
                pagos_hoy_raw = Pago.objects.filter(fecha_pago__date=hoy_timezone).aggregate(total=Sum('monto'))['total']
                pagos_hoy = Decimal(str(pagos_hoy_raw)) if pagos_hoy_raw else Decimal('0')
            except:
                pagos_hoy = Decimal('0')
            
            # Meta de cobranza (5% de la cartera)
            meta_diaria = cartera_total * Decimal('0.05') if cartera_total > 0 else Decimal('0')
            
            # Porcentaje de cumplimiento
            try:
                porcentaje_cumplimiento = (pagos_hoy / meta_diaria * Decimal('100')) if meta_diaria > 0 else Decimal('0')
            except:
                porcentaje_cumplimiento = Decimal('0')
            
            # Crear análisis con datos reales
            analisis = cls(
                fecha_analisis=hoy,
                total_creditos_activos=total_creditos,
                cartera_total=cartera_total,
                cartera_al_dia=cartera_al_dia_monto,
                cartera_vencida=cartera_vencida_monto,
                creditos_al_dia=creditos_al_dia,
                creditos_mora_temprana=creditos_mora_temp,
                creditos_mora_alta=creditos_mora_alta,
                creditos_mora_critica=creditos_mora_crit,
                total_interes_moratorio=Decimal('0'),  # Calculado por separado si es necesario
                porcentaje_cartera_vencida=porcentaje_vencida,
                dias_mora_promedio=Decimal('0'),  # Calculado por separado si es necesario
                pagos_del_dia=pagos_hoy,
                meta_cobranza_diaria=meta_diaria,
                porcentaje_cumplimiento_meta=porcentaje_cumplimiento
            )
            analisis.save()
            return analisis
            
        except Exception as e:
            print(f"Error en análisis diario seguro: {e}")
            # Retornar objeto básico si falla todo
            return type('AnalisisBasico', (), {
                'cartera_total': Decimal('0'),
                'cartera_al_dia': Decimal('0'),
                'cartera_vencida': Decimal('0'),
                'porcentaje_cartera_vencida': Decimal('0'),
                'creditos_al_dia': 0,
                'creditos_mora_temprana': 0,
                'creditos_mora_alta': 0,
                'creditos_mora_critica': 0,
                'pagos_del_dia': Decimal('0'),
                'meta_cobranza_diaria': Decimal('0'),
                'porcentaje_cumplimiento_meta': Decimal('0'),
                'dias_mora_promedio': Decimal('0'),
            })()
    
    @classmethod
    def generar_analisis_diario(cls):
        """Genera el análisis de cartera del día actual"""
        from datetime import date
        from django.db.models import Sum, Count, Avg
        from decimal import Decimal, InvalidOperation
        
        # Verificar si ya existe análisis para hoy (usar timezone para fecha correcta)
        from django.utils import timezone as tz
        hoy_timezone = tz.now().date()
        hoy = date.today()  # Mantener para compatibilidad
        
        # Decidir qué fecha usar para el análisis
        fecha_analisis = hoy_timezone if hoy_timezone != hoy else hoy
        
        analisis_existente = cls.objects.filter(fecha_analisis=fecha_analisis).first()
        if analisis_existente:
            analisis_existente.delete()  # Recrear con datos actualizados
        
        # Actualizar todos los créditos (incluir PAGADO para análisis completo)
        creditos_para_analisis = Credito.objects.filter(estado__in=['DESEMBOLSADO', 'VENCIDO', 'PAGADO'])
        for credito in creditos_para_analisis:
            if credito.estado in ['DESEMBOLSADO', 'VENCIDO']:  # Solo actualizar estado de mora si no está pagado
                credito.actualizar_estado_cartera()
        
        # Calcular métricas (incluir PAGADO para cartera total)
        creditos_activos = Credito.objects.filter(estado__in=['DESEMBOLSADO', 'VENCIDO', 'PAGADO'])
        
        # Métricas generales
        total_creditos = creditos_activos.count()
        
        # Cartera = saldo pendiente (lo que falta por cobrar), no monto_total
        try:
            from django.db.models.functions import Coalesce
            from django.db.models import Value
            from django.db.models import DecimalField
            qs = creditos_activos.annotate(
                total_pagado=Coalesce(Sum('pago__monto'), Value(Decimal('0')), output_field=DecimalField())
            )
            cartera_total = Decimal('0')
            cartera_al_dia_monto = Decimal('0')
            for c in qs:
                monto_total = c.monto_total or c.monto or Decimal('0')
                saldo = max(Decimal('0'), monto_total - (c.total_pagado or Decimal('0')))
                cartera_total += saldo
                if c.estado_mora == 'AL_DIA':
                    cartera_al_dia_monto += saldo
            cartera_vencida_monto = cartera_total - cartera_al_dia_monto
        except (InvalidOperation, ValueError, TypeError, Exception):
            cartera_total = Decimal('0')
            cartera_al_dia_monto = Decimal('0')
            cartera_vencida_monto = Decimal('0')
        
        # Métricas por estado de mora
        al_dia = creditos_activos.filter(estado_mora='AL_DIA').count()
        mora_temp = creditos_activos.filter(estado_mora='MORA_TEMPRANA').count()
        mora_alta = creditos_activos.filter(estado_mora='MORA_ALTA').count()
        mora_crit = creditos_activos.filter(estado_mora='MORA_CRITICA').count()
        
        # Intereses moratorios
        try:
            total_interes_mora_raw = creditos_activos.aggregate(
                total=Sum('interes_moratorio')
            )['total']
            total_interes_mora = Decimal(str(total_interes_mora_raw)) if total_interes_mora_raw else Decimal('0')
        except (InvalidOperation, ValueError, TypeError):
            total_interes_mora = Decimal('0')
        
        # Porcentaje de cartera vencida
        try:
            porcentaje_vencida = (
                (cartera_vencida_monto / cartera_total * 100) if cartera_total > 0 else Decimal('0')
            )
            # Asegurar que sea un Decimal válido
            if not isinstance(porcentaje_vencida, Decimal):
                porcentaje_vencida = Decimal(str(porcentaje_vencida))
        except (InvalidOperation, ValueError, TypeError):
            porcentaje_vencida = Decimal('0')
        
        # Días de mora promedio
        try:
            dias_mora_prom_raw = creditos_activos.filter(dias_mora__gt=0).aggregate(
                promedio=Avg('dias_mora')
            )['promedio']
            
            if dias_mora_prom_raw is None:
                dias_mora_prom = Decimal('0')
            else:
                dias_mora_prom = Decimal(str(dias_mora_prom_raw))
        except (InvalidOperation, ValueError, TypeError):
            dias_mora_prom = Decimal('0')
        
        # Pagos del día (usar timezone para manejar correctamente UTC)
        from django.utils import timezone as tz
        hoy_timezone = tz.now().date()  # Fecha actual según timezone de Django
        
        try:
            pagos_hoy_raw = Pago.objects.filter(fecha_pago__date=hoy_timezone).aggregate(
                total=Sum('monto')
            )['total']
            pagos_hoy = Decimal(str(pagos_hoy_raw)) if pagos_hoy_raw else Decimal('0')
        except (InvalidOperation, ValueError, TypeError):
            pagos_hoy = Decimal('0')
        
        # Debug: también verificar con fecha local por si acaso
        if pagos_hoy == Decimal('0'):
            try:
                pagos_hoy_alt_raw = Pago.objects.filter(fecha_pago__date=hoy).aggregate(
                    total=Sum('monto')
                )['total']
                pagos_hoy_alt = Decimal(str(pagos_hoy_alt_raw)) if pagos_hoy_alt_raw else Decimal('0')
                # Usar el que tenga datos
                pagos_hoy = pagos_hoy_alt if pagos_hoy_alt > Decimal('0') else pagos_hoy
            except (InvalidOperation, ValueError, TypeError):
                pass  # Mantener el valor de pagos_hoy original
        
        # Calcular meta de cobranza (5% de la cartera)
        try:
            meta_diaria = cartera_total * Decimal('0.05') if cartera_total > Decimal('0') else Decimal('0')
        except (InvalidOperation, ValueError, TypeError):
            meta_diaria = Decimal('0')
        
        # Calcular porcentaje de cumplimiento
        try:
            porcentaje_cumplimiento = Decimal('0')
            if meta_diaria > Decimal('0'):
                porcentaje_cumplimiento = (pagos_hoy / meta_diaria * Decimal('100'))
        except (InvalidOperation, ValueError, TypeError, ZeroDivisionError):
            porcentaje_cumplimiento = Decimal('0')
        
        # Crear análisis con la fecha correcta
        analisis = cls(
            fecha_analisis=fecha_analisis,
            total_creditos_activos=total_creditos,
            cartera_total=cartera_total,
            cartera_al_dia=cartera_al_dia_monto,
            cartera_vencida=cartera_vencida_monto,
            creditos_al_dia=al_dia,
            creditos_mora_temprana=mora_temp,
            creditos_mora_alta=mora_alta,
            creditos_mora_critica=mora_crit,
            total_interes_moratorio=total_interes_mora,
            porcentaje_cartera_vencida=porcentaje_vencida,
            dias_mora_promedio=dias_mora_prom,
            pagos_del_dia=pagos_hoy,
            meta_cobranza_diaria=meta_diaria,
            porcentaje_cumplimiento_meta=porcentaje_cumplimiento
        )
        analisis.save()
        
        return analisis

class TareaCobro(models.Model):
    """Tareas diarias de cobro asignadas a cobradores"""
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En Proceso'),
        ('COBRADO', 'Cobrado'),
        ('NO_ENCONTRADO', 'Cliente no encontrado'),
        ('NO_ESTABA', 'Cliente no estaba'),
        ('NO_PUDO_PAGAR', 'No pudo pagar'),
        ('REPROGRAMADO', 'Reprogramado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    PRIORIDADES = [
        ('ALTA', 'Alta - Mora crítica'),
        ('MEDIA', 'Media - Mora temprana'),
        ('BAJA', 'Baja - Al día'),
    ]
    
    # Información básica de la tarea
    cobrador = models.ForeignKey('Cobrador', on_delete=models.CASCADE, verbose_name="Cobrador asignado")
    cuota = models.ForeignKey('CronogramaPago', on_delete=models.CASCADE, verbose_name="Cuota a cobrar")
    fecha_asignacion = models.DateField(verbose_name="Fecha asignada")
    
    # Estado y prioridad
    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE')
    prioridad = models.CharField(max_length=10, choices=PRIORIDADES, default='BAJA')
    orden_visita = models.IntegerField(default=1, verbose_name="Orden de visita en ruta")
    
    # Información de ejecución
    fecha_visita = models.DateTimeField(null=True, blank=True, verbose_name="Fecha/hora de visita")
    monto_cobrado = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Monto cobrado")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones del cobrador")
    
    # Información de seguimiento
    intentos_cobro = models.IntegerField(default=0, verbose_name="Número de intentos")
    fecha_reprogramacion = models.DateField(null=True, blank=True, verbose_name="Fecha reprogramada")
    
    # Geolocalización (opcional para verificar visitas)
    latitud = models.FloatField(null=True, blank=True, verbose_name="Latitud de visita")
    longitud = models.FloatField(null=True, blank=True, verbose_name="Longitud de visita")
    
    # Auditoría: quién realizó la última acción (cobrar, reprogramar, etc.)
    usuario_ultima_accion = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tareas_cobro_modificadas', verbose_name="Usuario última acción"
    )
    # Motivo al reprogramar (opcional, para análisis)
    motivo_reprogramacion = models.CharField(
        max_length=255, blank=True, verbose_name="Motivo reprogramación"
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tarea de Cobro"
        verbose_name_plural = "Tareas de Cobro"
        ordering = ['fecha_asignacion', 'orden_visita', 'prioridad']
        unique_together = ['cuota', 'fecha_asignacion']  # Una cuota solo puede tener una tarea por día
    
    @property
    def cliente(self):
        """Cliente asociado a la cuota"""
        return self.cuota.credito.cliente
    
    @property
    def credito(self):
        """Crédito asociado a la cuota"""
        return self.cuota.credito
    
    @property
    def monto_a_cobrar(self):
        """Monto pendiente de la cuota"""
        return self.cuota.saldo_pendiente()
    
    @property
    def dias_vencida(self):
        """Días que lleva vencida la cuota"""
        from datetime import date
        if self.cuota.fecha_vencimiento < date.today():
            return (date.today() - self.cuota.fecha_vencimiento).days
        return 0
    
    @property
    def color_prioridad(self):
        """Color CSS según la prioridad"""
        colores = {
            'ALTA': 'danger',
            'MEDIA': 'warning',
            'BAJA': 'success'
        }
        return colores.get(self.prioridad, 'secondary')
    
    @property
    def color_estado(self):
        """Color CSS según el estado"""
        colores = {
            'PENDIENTE': 'secondary',
            'EN_PROCESO': 'warning',
            'COBRADO': 'success',
            'NO_ENCONTRADO': 'danger',
            'NO_ESTABA': 'warning',
            'NO_PUDO_PAGAR': 'info',
            'REPROGRAMADO': 'primary',
            'CANCELADO': 'danger'
        }
        return colores.get(self.estado, 'secondary')
    
    def marcar_como_cobrado(self, monto, observaciones="", latitud=None, longitud=None):
        """Marca la tarea como cobrada Y registra el pago automáticamente"""
        from django.utils import timezone
        from decimal import Decimal, InvalidOperation
        
        # Convertir monto a Decimal de forma segura
        if isinstance(monto, (str, int, float)):
            try:
                # Limpiar el monto si es string
                if isinstance(monto, str):
                    monto_limpio = str(monto).replace(',', '').replace(' ', '').strip()
                else:
                    monto_limpio = str(monto)
                monto_decimal = Decimal(monto_limpio)
                print(f"[DEBUG][marcar_como_cobrado] monto convertido a Decimal: {monto_decimal}")
            except (ValueError, InvalidOperation) as e:
                print(f"[DEBUG][marcar_como_cobrado] Error al convertir monto: {e}")
                raise ValueError(f"Monto inválido: {monto}")
        elif isinstance(monto, Decimal):
            monto_decimal = monto
            print(f"[DEBUG][marcar_como_cobrado] monto ya es Decimal: {monto_decimal}")
        else:
            raise ValueError(f"Tipo de monto no soportado: {type(monto)}")
        
        # 1. Actualizar la tarea
        self.estado = 'COBRADO'
        self.fecha_visita = timezone.now()
        self.monto_cobrado = monto_decimal
        self.observaciones = observaciones
        if latitud:
            self.latitud = latitud
        if longitud:
            self.longitud = longitud
        
        self.save()
        
        # 2. Actualizar la cuota asociada
        self.cuota.monto_pagado += monto_decimal
        
        if self.cuota.monto_pagado >= self.cuota.monto_cuota:
            self.cuota.estado = 'PAGADA'
            self.cuota.fecha_pago = timezone.now().date()
        else:
            self.cuota.estado = 'PARCIAL'
        
        self.cuota.save()
        
        # 3. CREAR EL PAGO AUTOMÁTICAMENTE (¡Esta es la magia!)
        from .models import Pago
        pago = Pago.objects.create(
            credito=self.credito,
            cuota=self.cuota,
            monto=monto_decimal,
            numero_cuota=self.cuota.numero_cuota,
            observaciones=f"💰 Cobro en campo por {self.cobrador.nombre_completo}\n📍 Cliente: {self.credito.cliente.nombre_completo}\n📋 {observaciones}".strip()
        )
        
        # 4. Actualizar estado del crédito si es necesario
        credito = self.credito
        saldo_restante = credito.saldo_pendiente()
        
        if saldo_restante <= 0:
            credito.estado = 'PAGADO'
            credito.save()
        
        return pago  # Retornamos el pago creado
    
    def cambiar_estado(self, nuevo_estado, observaciones="", fecha_reprogramacion=None, motivo_reprogramacion=""):
        """Cambia el estado de la tarea (incrementa intentos_cobro)."""
        from django.utils import timezone
        
        self.estado = nuevo_estado
        self.fecha_visita = timezone.now()
        self.observaciones = observaciones
        self.intentos_cobro += 1
        
        if nuevo_estado == 'REPROGRAMADO':
            if fecha_reprogramacion:
                self.fecha_reprogramacion = fecha_reprogramacion
            if motivo_reprogramacion:
                self.motivo_reprogramacion = motivo_reprogramacion[:255]
        
        self.save()
    
    @classmethod
    def generar_tareas_diarias(cls, fecha=None, verbose=False):
        """Genera tareas de cobro para el día especificado.
        Reglas:
        - Incluir TODAS las cuotas que vencen exactamente en 'fecha'.
        - Incluir cuotas que fueron reprogramadas para 'fecha'.
        - Sin límite de cantidad por cobrador.
        - No arrastrar backlog de días anteriores (solo hoy), salvo reprogramadas.
        """
        from datetime import date
        from django.db.models import Q
        import logging

        logger = logging.getLogger(__name__)

        if not fecha:
            fecha = date.today()

        if verbose:
            logger.info(f'Iniciando generación de tareas (solo hoy y reprogramadas) para {fecha}')

        # Obtener todos los cobradores activos
        cobradores_activos = Cobrador.objects.filter(activo=True).prefetch_related('rutas')

        if verbose:
            logger.info(f'Encontrados {cobradores_activos.count()} cobradores activos')

        tareas_creadas = 0

        for cobrador in cobradores_activos:
            rutas_cobrador = cobrador.rutas.all()
            if not rutas_cobrador.exists():
                if verbose:
                    logger.info(f'Cobrador {cobrador.nombre_completo} sin rutas asignadas, omitiendo')
                continue

            if verbose:
                rutas_nombres = [r.nombre for r in rutas_cobrador]
                logger.info(f'Procesando cobrador {cobrador.nombre_completo} con rutas: {rutas_nombres}')

            # 1) Reprogramadas para hoy: llevar a estado PENDIENTE y fecha de hoy
            reprogramadas_hoy = cls.objects.filter(
                cobrador=cobrador,
                fecha_reprogramacion=fecha
            )
            for tarea in reprogramadas_hoy:
                # Si ya existe una tarea en hoy para la misma cuota, evitar duplicar
                existe_hoy = cls.objects.filter(cuota=tarea.cuota, fecha_asignacion=fecha).exclude(id=tarea.id).exists()
                if not existe_hoy:
                    tarea.fecha_asignacion = fecha
                    tarea.estado = 'PENDIENTE'
                    # Prioridad según días respecto a hoy
                    dias_mora = (fecha - tarea.cuota.fecha_vencimiento).days
                    if dias_mora > 15:
                        tarea.prioridad = 'ALTA'
                    elif dias_mora > 5:
                        tarea.prioridad = 'MEDIA'
                    else:
                        tarea.prioridad = 'BAJA'
                    tarea.save(update_fields=['fecha_asignacion', 'estado', 'prioridad'])
                    tareas_creadas += 1
                    if verbose:
                        logger.info(f"Reprogramada para hoy: {tarea.cliente.nombre_completo} - Cuota #{tarea.cuota.numero_cuota}")

            # 2) Cuotas que vencen HOY para créditos del cobrador
            cuotas_hoy = CronogramaPago.objects.filter(
                Q(credito__cobrador=cobrador) &
                Q(fecha_vencimiento=fecha) &
                Q(estado__in=['PENDIENTE', 'PARCIAL']) &
                Q(credito__estado__in=['DESEMBOLSADO', 'VENCIDO'])
            ).exclude(
                # Evitar duplicar si ya existe tarea hoy para la cuota
                id__in=cls.objects.filter(fecha_asignacion=fecha).values_list('cuota_id', flat=True)
            ).select_related('credito__cliente').order_by(
                'credito__cliente__nombres', 'credito__cliente__apellidos'
            )

            if verbose and cuotas_hoy.exists():
                logger.info(f'Cuotas que vencen hoy para {cobrador.nombre_completo}: {cuotas_hoy.count()}')

            orden_visita = 1
            tareas_cobrador = 0

            for cuota in cuotas_hoy:
                dias_mora = (fecha - cuota.fecha_vencimiento).days  # 0 si es hoy
                if dias_mora > 15:
                    prioridad = 'ALTA'
                elif dias_mora > 5:
                    prioridad = 'MEDIA'
                else:
                    prioridad = 'BAJA'

                try:
                    cls.objects.create(
                        cobrador=cobrador,
                        cuota=cuota,
                        fecha_asignacion=fecha,
                        prioridad=prioridad,
                        orden_visita=orden_visita
                    )
                    tareas_creadas += 1
                    tareas_cobrador += 1
                    orden_visita += 1
                    if verbose:
                        logger.info(
                            f'Tarea creada (HOY): {cuota.credito.cliente.nombre_completo} - '
                            f'Cuota #{cuota.numero_cuota} - ${cuota.monto_cuota} - Prioridad: {prioridad}'
                        )
                except Exception as e:
                    if verbose:
                        logger.error(
                            f'Error creando tarea (HOY) para {cuota.credito.cliente.nombre_completo}: {str(e)}'
                        )
                    continue

            if verbose:
                logger.info(f'Total tareas creadas para {cobrador.nombre_completo}: {tareas_cobrador}')

        # Optimizar rutas si se crearon tareas
        if tareas_creadas > 0:
            cls._optimizar_rutas_cobradores(fecha)

        if verbose:
            logger.info(f'Total de tareas creadas: {tareas_creadas}')

        return tareas_creadas
    
    @classmethod
    def _optimizar_rutas_cobradores(cls, fecha):
        """Optimiza el orden de visitas por cobrador agrupando por barrio"""
        cobradores = Cobrador.objects.filter(activo=True)
        
        for cobrador in cobradores:
            tareas = cls.objects.filter(
                cobrador=cobrador,
                fecha_asignacion=fecha,
                estado='PENDIENTE'
            ).select_related('cuota__credito__cliente')
            
            # Agrupar por barrio y asignar orden
            tareas_por_barrio = {}
            for tarea in tareas:
                barrio = tarea.cliente.barrio or 'Sin barrio'
                if barrio not in tareas_por_barrio:
                    tareas_por_barrio[barrio] = []
                tareas_por_barrio[barrio].append(tarea)
            
            # Asignar orden de visita
            orden = 1
            for barrio, tareas_barrio in tareas_por_barrio.items():
                # Ordenar por prioridad dentro del barrio
                tareas_barrio.sort(key=lambda t: (t.prioridad != 'ALTA', t.prioridad != 'MEDIA'))
                
                for tarea in tareas_barrio:
                    tarea.orden_visita = orden
                    tarea.save(update_fields=['orden_visita'])
                    orden += 1
    
    def __str__(self):
        return f"Tarea {self.id} - {self.cobrador.nombre_completo} - {self.cliente.nombre_completo} - {self.get_estado_display()}"


class TareaCobroLog(models.Model):
    """Registro de auditoría: cada cambio de estado o acción sobre una tarea de cobro."""
    ACCIONES = [
        ('CREADA', 'Tarea creada'),
        ('COBRADO', 'Marcada como cobrada'),
        ('NO_ENCONTRADO', 'Cliente no encontrado'),
        ('NO_ESTABA', 'Cliente no estaba'),
        ('NO_PUDO_PAGAR', 'No pudo pagar'),
        ('REPROGRAMADO', 'Reprogramada'),
        ('CANCELADO', 'Cancelada'),
    ]
    tarea = models.ForeignKey(
        TareaCobro, on_delete=models.CASCADE, related_name='logs',
        verbose_name="Tarea"
    )
    usuario = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Usuario"
    )
    accion = models.CharField(max_length=20, choices=ACCIONES, verbose_name="Acción")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    motivo_reprogramacion = models.CharField(max_length=255, blank=True)
    monto_registrado = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name="Monto (si aplica)"
    )

    class Meta:
        verbose_name = "Log tarea de cobro"
        verbose_name_plural = "Logs tareas de cobro"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tarea_id} - {self.get_accion_display()} - {self.fecha}"


class Ruta(models.Model):
    """Rutas geográficas para asignación de cobradores"""
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la ruta")
    descripcion = models.TextField(blank=True, verbose_name="Descripción de la ruta")
    barrios = models.TextField(verbose_name="Barrios incluidos (separados por comas)")
    zona = models.CharField(max_length=50, verbose_name="Zona/Sector", blank=True)
    activa = models.BooleanField(default=True, verbose_name="Ruta activa")
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Ruta"
        verbose_name_plural = "Rutas"
        ordering = ['nombre']
    
    def get_barrios_lista(self):
        """Retorna la lista de barrios como array"""
        return [barrio.strip() for barrio in self.barrios.split(',') if barrio.strip()]
    
    def total_clientes(self):
        """Cuenta el total de clientes asignados a esta ruta"""
        return Cliente.objects.filter(barrio__in=self.get_barrios_lista()).count()
    
    def total_creditos_activos(self):
        """Cuenta créditos activos en esta ruta"""
        return Credito.objects.filter(
            cobrador__rutas=self,
            estado__in=['APROBADO', 'DESEMBOLSADO']
        ).count()
    
    def __str__(self):
        return f"{self.nombre} ({self.zona})"

class Cobrador(models.Model):
    """Cobradores de campo para gestión de cartera"""
    TIPOS_DOCUMENTO = [
        ('CC', 'Cédula de Ciudadanía'),
        ('TI', 'Tarjeta de Identidad'),
        ('CE', 'Cédula de Extranjería'),
    ]
    
    # Información personal
    nombres = models.CharField(max_length=100, verbose_name="Nombres")
    apellidos = models.CharField(max_length=100, verbose_name="Apellidos")
    tipo_documento = models.CharField(max_length=2, choices=TIPOS_DOCUMENTO, default='CC', verbose_name="Tipo de documento")
    numero_documento = models.CharField(max_length=20, unique=True, verbose_name="Número de documento")
    
    # Información de contacto
    telefono_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Teléfono debe tener formato válido. Ej: +573001234567 o 3001234567"
    )
    celular = models.CharField(
        validators=[telefono_validator], 
        max_length=17, 
        verbose_name="Celular"
    )
    email = models.EmailField(verbose_name="Correo electrónico", blank=True, null=True)
    direccion = models.TextField(verbose_name="Dirección de residencia")
    
    # Asignación de rutas (un cobrador puede tener múltiples rutas)
    rutas = models.ManyToManyField(Ruta, verbose_name="Rutas asignadas", related_name='cobradores')
    
    # Información laboral
    fecha_ingreso = models.DateField(verbose_name="Fecha de ingreso")
    activo = models.BooleanField(default=True, verbose_name="Cobrador activo")
    comision_porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name="Comisión por cobro (%)"
    )
    meta_diaria = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="Meta diaria de cobros"
    )
    
    # Usuario del sistema (opcional)
    usuario = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Usuario del sistema"
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cobrador"
        verbose_name_plural = "Cobradores"
        ordering = ['nombres', 'apellidos']
    
    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
    
    def get_rutas_nombres(self):
        """Retorna los nombres de las rutas asignadas"""
        return ', '.join([ruta.nombre for ruta in self.rutas.all()])
    
    def total_creditos_asignados(self):
        """Total de créditos asignados a este cobrador"""
        return self.credito_set.count()
    
    def creditos_activos(self):
        """Créditos activos asignados a este cobrador"""
        return self.credito_set.filter(estado__in=['APROBADO', 'DESEMBOLSADO'])
    
    def creditos_por_cobrar_hoy(self):
        """Créditos con cuotas que vencen hoy"""
        from datetime import date
        return self.credito_set.filter(
            cronograma__fecha_vencimiento=date.today(),
            cronograma__estado='PENDIENTE'
        ).distinct()
    
    def monto_por_cobrar_hoy(self):
        """Monto total a cobrar hoy"""
        from datetime import date
        from django.db.models import Sum
        
        total = CronogramaPago.objects.filter(
            credito__cobrador=self,
            fecha_vencimiento=date.today(),
            estado='PENDIENTE'
        ).aggregate(Sum('monto_cuota'))['monto_cuota__sum']
        
        return total if total is not None else 0
    
    def __str__(self):
        return f"{self.nombre_completo} - {self.numero_documento}"


class CierreCobroDiario(models.Model):
    """Registro del cierre de cobro de un cobrador en una fecha: lo que debía entregar vs lo recibido (arqueo)."""
    cobrador = models.ForeignKey(Cobrador, on_delete=models.CASCADE, related_name='cierres_diarios')
    fecha = models.DateField(verbose_name="Fecha de cierre")
    # Lo que el sistema dice que cobró ese día (suma de pagos registrados a su nombre)
    monto_esperado = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name="Monto según sistema (lo que cobró)"
    )
    cantidad_pagos = models.IntegerField(default=0, verbose_name="Cantidad de pagos")
    # Lo que el cobrador entrega físicamente (arqueo)
    monto_recibido = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name="Monto recibido (arqueo)"
    )
    diferencia = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name="Diferencia (recibido - esperado)"
    )
    cerrado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Cerrado por"
    )
    fecha_cierre = models.DateTimeField(auto_now_add=True, verbose_name="Fecha/hora de cierre")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    class Meta:
        verbose_name = "Cierre de cobro diario"
        verbose_name_plural = "Cierres de cobro diario"
        ordering = ['-fecha', '-fecha_cierre']
        unique_together = [['cobrador', 'fecha']]

    def __str__(self):
        return f"Cierre {self.cobrador.nombre_completo} - {self.fecha}"
