# -*- coding: utf-8 -*-
"""
Lógica de retanqueo: liquidar crédito anterior y crear nuevo crédito con trazabilidad.
Saldo a liquidar = capital pendiente + intereses normales a la fecha (saldo_pendiente del crédito).
"""
from decimal import Decimal
from django.db import transaction

from .models import Credito, Pago


def ejecutar_retanqueo(credito_anterior_id, monto_nueva_solicitud):
    """
    Liquida el crédito anterior con un pago por el saldo a liquidar y crea un nuevo
    crédito con monto = monto_nueva_solicitud, vinculado al anterior.

    - monto_nueva_solicitud: monto del nuevo crédito (debe ser >= saldo a liquidar).
    - Retorna: (success: bool, nuevo_credito o None, message: str)
    """
    try:
        credito_anterior = Credito.objects.get(id=credito_anterior_id)
    except Credito.DoesNotExist:
        return False, None, 'Crédito no encontrado.'

    if not credito_anterior.puede_retanquear():
        total_pagado = credito_anterior.total_pagado()
        monto_total = credito_anterior.monto_total or credito_anterior.monto
        umbral = (monto_total * Decimal('0.25')) if monto_total else Decimal('0')
        if credito_anterior.estado not in ('DESEMBOLSADO', 'VENCIDO') or credito_anterior.saldo_pendiente() <= 0:
            msg = 'Este crédito no puede retanquearse. Debe estar desembolsado o vencido y con saldo pendiente.'
        elif total_pagado < umbral:
            msg = (
                f'No puede retanquear: el cliente debe tener al menos el 25% del crédito pagado. '
                f'Actual: {float(total_pagado):,.0f} de {float(umbral):,.0f} requerido.'
            )
        else:
            msg = 'Este crédito no puede retanquearse.'
        return False, None, msg

    saldo = credito_anterior.saldo_a_liquidar()
    monto_decimal = Decimal(str(monto_nueva_solicitud))
    if monto_decimal < saldo:
        return False, None, (
            f'El monto del nuevo crédito (${monto_decimal:,.0f}) debe ser al menos '
            f'el saldo a liquidar (${saldo:,.0f}).'
        )

    with transaction.atomic():
        # 1. Registrar pago en el crédito anterior por el saldo a liquidar (observaciones incluirán ID del nuevo crédito después de crearlo)
        pago_retanqueo = Pago.objects.create(
            credito=credito_anterior,
            cuota=None,
            monto=saldo,
            numero_cuota=0,
            observaciones=(
                'Pago por retanqueo: liquidación del crédito anterior. '
                'Se creará nuevo crédito con este monto aplicado.'
            ),
        )

        # 2. Marcar crédito anterior como PAGADO si quedó en cero
        credito_anterior.refresh_from_db()
        if credito_anterior.saldo_pendiente() <= 0:
            credito_anterior.estado = 'PAGADO'
            credito_anterior.save(update_fields=['estado'])

        # 3. Crear nuevo crédito (mismo cliente, misma tasa/plazo; monto = nueva solicitud)
        nuevo_credito = Credito.objects.create(
            cliente=credito_anterior.cliente,
            cobrador=credito_anterior.cobrador,
            monto=monto_decimal,
            tasa_interes=credito_anterior.tasa_interes,
            tipo_plazo=credito_anterior.tipo_plazo,
            cantidad_cuotas=credito_anterior.cantidad_cuotas,
            tasa_mora=credito_anterior.tasa_mora,
            estado='SOLICITADO',
            credito_retanqueado=credito_anterior,
            monto_aplicado_credito_anterior=saldo,
            valor_cuota=Decimal('0'),
            total_interes=Decimal('0'),
            monto_total=Decimal('0'),
        )

        # 4. Vincular el pago al nuevo crédito (para poder revertir si rechazan la solicitud)
        pago_retanqueo.observaciones = (
            f'Pago por retanqueo: liquidación del crédito anterior. Nuevo crédito #{nuevo_credito.id}.'
        )
        pago_retanqueo.save(update_fields=['observaciones'])

    return True, nuevo_credito, (
        f'Retanqueo realizado. Crédito #{credito_anterior.id} liquidado. '
        f'Nuevo crédito #{nuevo_credito.id} creado (monto ${monto_decimal:,.0f}; '
        f'a desembolsar al cliente: ${monto_decimal - saldo:,.0f}).'
    )


def revertir_retanqueo(credito_nuevo_id):
    """
    Revierte un retanqueo cuando se rechaza la solicitud del nuevo crédito:
    elimina el pago registrado en el crédito anterior y devuelve ese crédito a vigente
    (DESEMBOLSADO), para que la deuda siga apareciendo en cartera.

    - credito_nuevo_id: ID del crédito creado por retanqueo que está siendo rechazado.
    - Retorna: (success: bool, message: str)
    """
    try:
        credito_nuevo = Credito.objects.get(id=credito_nuevo_id)
    except Credito.DoesNotExist:
        return False, 'Crédito no encontrado.'

    if not credito_nuevo.credito_retanqueado_id or not credito_nuevo.monto_aplicado_credito_anterior:
        return True, ''  # No es un crédito por retanqueo, no hay nada que revertir

    credito_anterior = credito_nuevo.credito_retanqueado
    monto = credito_nuevo.monto_aplicado_credito_anterior
    marcador = f'Nuevo crédito #{credito_nuevo.id}.'

    pago = Pago.objects.filter(
        credito=credito_anterior,
        monto=monto,
        observaciones__icontains=marcador,
    ).order_by('-fecha_pago').first()

    if not pago:
        # Fallback: buscar por monto y texto genérico (por si el pago es anterior a guardar el ID)
        pago = Pago.objects.filter(
            credito=credito_anterior,
            monto=monto,
            observaciones__icontains='retanqueo',
        ).order_by('-fecha_pago').first()

    if not pago:
        return False, (
            f'No se encontró el pago de retanqueo en el crédito #{credito_anterior.id}. '
            'Revise manualmente la cartera.'
        )

    with transaction.atomic():
        pago.delete()
        credito_anterior.refresh_from_db()
        credito_anterior.estado = 'DESEMBOLSADO'
        credito_anterior.save(update_fields=['estado'])

    return True, (
        f'Retanqueo revertido: crédito #{credito_anterior.id} vuelve a estar vigente con su saldo pendiente. '
        f'El cliente sigue debiendo.'
    )
