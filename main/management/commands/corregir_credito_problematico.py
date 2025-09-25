from django.core.management.base import BaseCommand
from decimal import Decimal
from main.models import Credito, CronogramaPago, Pago, TareaCobro

class Command(BaseCommand):
    help = 'Corrige la configuración del crédito problemático'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ejecutar',
            action='store_true',
            help='Ejecuta la corrección (sin esta flag, solo muestra lo que se haría)'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔧 Analizando crédito problemático...")
        
        # Buscar el crédito problemático
        credito = Credito.objects.get(id=22)
        
        self.stdout.write(f"\n=== CRÉDITO PROBLEMÁTICO #{credito.id} ===")
        self.stdout.write(f"Cliente: {credito.cliente.nombre_completo}")
        self.stdout.write(f"Monto: ${credito.monto}")
        self.stdout.write(f"Tasa actual: {credito.tasa_interes}% anual")
        self.stdout.write(f"Tipo plazo: {credito.get_tipo_plazo_display()}")
        self.stdout.write(f"Cuotas: {credito.cantidad_cuotas}")
        self.stdout.write(f"Valor cuota actual: ${credito.valor_cuota}")
        self.stdout.write(f"Total a pagar actual: ${credito.monto_total}")
        
        # Proponer corrección
        self.stdout.write(f"\n=== ANÁLISIS DEL PROBLEMA ===")
        
        # Una tasa del 240% anual es absurda para créditos diarios
        # Las tasas típicas para microcréditos diarios en Colombia serían:
        # - 0.1% a 0.5% diario (36.5% a 182.5% anual)
        # - Para este ejemplo, usaremos una tasa más razonable
        
        tasa_razonable = Decimal('60.00')  # 60% anual (más razonable)
        
        self.stdout.write(f"Tasa actual: {credito.tasa_interes}% (EXCESIVA)")
        self.stdout.write(f"Tasa propuesta: {tasa_razonable}% (más razonable)")
        
        # Calcular con la nueva tasa
        tasa_anual = tasa_razonable / 100
        tasa_diaria = tasa_anual / 365
        
        if tasa_diaria > 0:
            factor = (tasa_diaria * (1 + tasa_diaria) ** credito.cantidad_cuotas) / ((1 + tasa_diaria) ** credito.cantidad_cuotas - 1)
            nueva_cuota = credito.monto * Decimal(str(factor))
        else:
            nueva_cuota = credito.monto / credito.cantidad_cuotas
        
        nuevo_total = nueva_cuota * credito.cantidad_cuotas
        nuevos_intereses = nuevo_total - credito.monto
        
        self.stdout.write(f"\nCon tasa corregida ({tasa_razonable}%):")
        self.stdout.write(f"  Cuota diaria: ${nueva_cuota}")
        self.stdout.write(f"  Total a pagar: ${nuevo_total}")
        self.stdout.write(f"  Intereses: ${nuevos_intereses}")
        
        # Verificar si esto coincide con lo que esperamos
        cuota_esperada = Decimal('36470')  # El valor mencionado por el usuario
        diferencia = abs(nueva_cuota - cuota_esperada)
        self.stdout.write(f"\nComparación con cuota esperada:")
        self.stdout.write(f"  Cuota calculada: ${nueva_cuota}")
        self.stdout.write(f"  Cuota esperada: ${cuota_esperada}")
        self.stdout.write(f"  Diferencia: ${diferencia}")
        
        if diferencia > 100:
            # Probar con cuota exacta esperada
            self.stdout.write(f"\n=== ALTERNATIVA: USAR CUOTA EXACTA ESPERADA ===")
            cuota_exacta = cuota_esperada
            total_exacto = cuota_exacta * credito.cantidad_cuotas
            intereses_exactos = total_exacto - credito.monto
            tasa_implícita = (intereses_exactos / credito.monto) * 100
            
            self.stdout.write(f"Con cuota exacta de ${cuota_exacta}:")
            self.stdout.write(f"  Total a pagar: ${total_exacto}")
            self.stdout.write(f"  Intereses: ${intereses_exactos}")
            self.stdout.write(f"  Tasa implícita: {tasa_implícita}% anual")
        
        # Ejecutar corrección si se solicita
        if options['ejecutar']:
            self.stdout.write(f"\n=== EJECUTANDO CORRECCIÓN ===")
            
            # Decidir qué valores usar
            if diferencia <= 100:
                # Usar la tasa corregida
                credito.tasa_interes = tasa_razonable
                credito.valor_cuota = nueva_cuota
                credito.monto_total = nuevo_total
                credito.total_interes = nuevos_intereses
                self.stdout.write(f"Usando tasa corregida de {tasa_razonable}%")
            else:
                # Usar cuota exacta esperada
                credito.valor_cuota = cuota_esperada
                credito.monto_total = cuota_esperada * credito.cantidad_cuotas
                credito.total_interes = credito.monto_total - credito.monto
                # Ajustar tasa para que coincida
                credito.tasa_interes = (credito.total_interes / credito.monto) * 100
                self.stdout.write(f"Usando cuota exacta de ${cuota_esperada}")
            
            # Guardar el crédito
            credito.save()
            self.stdout.write(f"✅ Crédito actualizado")
            
            # Actualizar cronograma
            self.stdout.write("🔄 Actualizando cronograma...")
            cronograma = CronogramaPago.objects.filter(credito=credito)
            cronograma.update(monto_cuota=credito.valor_cuota)
            self.stdout.write(f"✅ {cronograma.count()} cuotas actualizadas")
            
            # Corregir el pago existente
            self.stdout.write("🔄 Corrigiendo pago existente...")
            pago_problema = Pago.objects.get(id=45)
            # El pago de $368.38 debería ser $36,470 (si usamos cuota exacta)
            if credito.valor_cuota == cuota_esperada:
                monto_correcto = cuota_esperada
            else:
                monto_correcto = credito.valor_cuota
            
            # Actualizar pago
            pago_problema.monto = monto_correcto
            pago_problema.save()
            self.stdout.write(f"✅ Pago corregido: ${monto_correcto}")
            
            # Actualizar tarea
            tarea_problema = TareaCobro.objects.get(id=50)
            tarea_problema.monto_cobrado = monto_correcto
            tarea_problema.save()
            self.stdout.write(f"✅ Tarea corregida")
            
            # Actualizar cuota
            cuota_problema = CronogramaPago.objects.get(id=276)
            cuota_problema.monto_pagado = monto_correcto
            cuota_problema.estado = 'PAGADA'  # Ahora está completamente pagada
            cuota_problema.save()
            self.stdout.write(f"✅ Cuota marcada como PAGADA")
            
            self.stdout.write(self.style.SUCCESS("🎉 Corrección completada exitosamente"))
        else:
            self.stdout.write(self.style.WARNING("ℹ️  Para ejecutar la corrección, use: --ejecutar"))
        
        self.stdout.write(self.style.SUCCESS("✅ Análisis completado"))