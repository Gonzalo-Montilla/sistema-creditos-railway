from django.core.management.base import BaseCommand
from decimal import Decimal
from main.models import Pago, TareaCobro, CronogramaPago

class Command(BaseCommand):
    help = 'Identifica y analiza montos erróneos en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--corregir',
            action='store_true',
            help='Corrige automáticamente los datos identificados como erróneos'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Iniciando análisis de datos problemáticos...")
        
        # Identificar datos problemáticos
        pagos_sospechosos, tareas_sospechosas, cuotas_problematicas = self.identificar_datos_problematicos()
        
        # Analizar patrones
        self.analizar_patron_error()
        
        # Mostrar resumen
        self.mostrar_resumen()
        
        # Si se solicita corrección, ejecutarla
        if options['corregir']:
            self.corregir_datos_automaticamente(pagos_sospechosos, tareas_sospechosas, cuotas_problematicas)
        
        self.stdout.write(self.style.SUCCESS("✅ Análisis completado"))

    def identificar_datos_problematicos(self):
        """Identifica registros con montos sospechosamente bajos o altos"""
        self.stdout.write("=== Identificando datos problemáticos ===")
        
        # 1. Buscar pagos con montos muy bajos (posibles errores)
        pagos_sospechosos = Pago.objects.filter(monto__lt=1000)  # Menos de $1,000 COP
        self.stdout.write(f"\n📊 Pagos con montos < $1,000: {pagos_sospechosos.count()}")
        
        for pago in pagos_sospechosos:
            self.stdout.write(f"  Pago #{pago.id}: ${pago.monto} - Cliente: {pago.credito.cliente.nombre_completo} - Fecha: {pago.fecha_pago}")
        
        # 2. Buscar tareas con montos cobrados muy bajos
        tareas_sospechosas = TareaCobro.objects.filter(
            estado='COBRADO',
            monto_cobrado__lt=1000,
            monto_cobrado__isnull=False
        )
        self.stdout.write(f"\n📊 Tareas con montos cobrados < $1,000: {tareas_sospechosas.count()}")
        
        for tarea in tareas_sospechosas:
            monto_esperado = tarea.cuota.monto_cuota
            self.stdout.write(f"  Tarea #{tarea.id}: Cobrado=${tarea.monto_cobrado}, Esperado=${monto_esperado} - Cliente: {tarea.cliente.nombre_completo}")
        
        # 3. Buscar cuotas con pagos parciales sospechosos
        cuotas_problematicas = CronogramaPago.objects.filter(
            estado='PARCIAL',
            monto_pagado__lt=1000,
            monto_pagado__gt=0
        )
        self.stdout.write(f"\n📊 Cuotas con pagos parciales < $1,000: {cuotas_problematicas.count()}")
        
        for cuota in cuotas_problematicas:
            self.stdout.write(f"  Cuota #{cuota.id}: Pagado=${cuota.monto_pagado}, Total=${cuota.monto_cuota} - Cliente: {cuota.credito.cliente.nombre_completo}")
        
        return pagos_sospechosos, tareas_sospechosas, cuotas_problematicas

    def analizar_patron_error(self):
        """Analiza si hay un patrón en los errores de montos"""
        self.stdout.write("\n=== Análisis de patrones de error ===")
        
        # Buscar el caso específico mencionado: $368.38 en lugar de $36470
        pagos_368 = Pago.objects.filter(monto=Decimal('368.38'))
        self.stdout.write(f"\nPagos con exactamente $368.38: {pagos_368.count()}")
        
        for pago in pagos_368:
            self.stdout.write(f"  Pago #{pago.id} - Cliente: {pago.credito.cliente.nombre_completo}")
            self.stdout.write(f"    Fecha: {pago.fecha_pago}")
            self.stdout.write(f"    Monto del crédito: ${pago.credito.monto}")
            self.stdout.write(f"    Valor cuota esperado: ${pago.credito.valor_cuota}")
            
            # Verificar si podría ser un error de división por 100
            posible_monto_real = pago.monto * 100
            self.stdout.write(f"    Posible monto real (x100): ${posible_monto_real}")
            
            # Verificar si el monto correcto sería cercano a la cuota esperada
            diferencia_con_cuota = abs(pago.credito.valor_cuota - posible_monto_real)
            if diferencia_con_cuota < 100:  # Diferencia menor a $100
                self.stdout.write(self.style.WARNING(f"    🎯 POSIBLE CORRECCIÓN: ${posible_monto_real} (muy cercano a cuota esperada)"))

    def mostrar_resumen(self):
        """Muestra un resumen de los datos encontrados"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("RESUMEN DE HALLAZGOS")
        self.stdout.write("="*50)
        
        total_pagos = Pago.objects.count()
        pagos_normales = Pago.objects.filter(monto__gte=1000).count()
        pagos_bajos = Pago.objects.filter(monto__lt=1000).count()
        
        self.stdout.write(f"Total de pagos: {total_pagos}")
        self.stdout.write(f"Pagos con montos normales (≥$1,000): {pagos_normales}")
        self.stdout.write(f"Pagos con montos bajos (<$1,000): {pagos_bajos}")
        if total_pagos > 0:
            self.stdout.write(f"Porcentaje problemático: {(pagos_bajos/total_pagos)*100:.1f}%")

    def corregir_datos_automaticamente(self, pagos_sospechosos, tareas_sospechosas, cuotas_problematicas):
        """Corrige automáticamente los datos identificados como claramente erróneos"""
        self.stdout.write("\n=== Iniciando corrección automática ===")
        
        correcciones_realizadas = 0
        
        # Corregir pagos con el patrón específico $368.38 -> $36838.00 (x100)
        for pago in pagos_sospechosos:
            if pago.monto == Decimal('368.38'):
                # Multiplicar por 100 como corrección probable
                monto_corregido = pago.monto * 100
                
                # Verificar que esté cerca del valor de cuota esperado
                diferencia_con_cuota = abs(pago.credito.valor_cuota - monto_corregido)
                if diferencia_con_cuota < 500:  # Diferencia razonable
                    self.stdout.write(f"  Corrigiendo Pago #{pago.id}: ${pago.monto} -> ${monto_corregido}")
                    pago.monto = monto_corregido
                    pago.save()
                    correcciones_realizadas += 1
                    
                    # También corregir la tarea asociada si existe
                    try:
                        tarea_asociada = TareaCobro.objects.get(
                            cuota=pago.cuota,
                            estado='COBRADO',
                            monto_cobrado=Decimal('368.38')
                        )
                        self.stdout.write(f"    Corrigiendo Tarea asociada #{tarea_asociada.id}")
                        tarea_asociada.monto_cobrado = monto_corregido
                        tarea_asociada.save()
                    except TareaCobro.DoesNotExist:
                        pass
                    
                    # Corregir la cuota si el monto pagado también está mal
                    cuota = pago.cuota
                    if cuota.monto_pagado == Decimal('368.38'):
                        self.stdout.write(f"    Corrigiendo Cuota #{cuota.id}: monto_pagado")
                        cuota.monto_pagado = monto_corregido
                        if cuota.monto_pagado >= cuota.monto_cuota:
                            cuota.estado = 'PAGADA'
                        cuota.save()
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Se realizaron {correcciones_realizadas} correcciones automáticas"))
        
        if correcciones_realizadas > 0:
            self.stdout.write(self.style.WARNING("⚠️  Se recomienda verificar los cambios y hacer backup antes de continuar"))