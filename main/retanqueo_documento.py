# Documento de retanqueo - firma OTP
# PDF con condiciones del crédito nuevo y monto aplicado al anterior + aceptación

import hashlib
import random
import string
from datetime import timedelta
from io import BytesIO
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings

from .models import Credito, RetanqueoOTP


OTP_LENGTH = 6
OTP_VALID_MINUTES = 15


def _generate_otp():
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def _hash_otp(otp):
    return hashlib.sha256(otp.encode('utf-8')).hexdigest()


def _verify_otp(plain_otp, otp_hash):
    return _hash_otp(plain_otp) == otp_hash


def _get_pending_otp(credito_id):
    now = timezone.now()
    return RetanqueoOTP.objects.filter(
        credito_id=credito_id,
        expires_at__gt=now,
    ).order_by('-created_at').first()


def solicitar_otp_retanqueo(credito_id):
    """
    Genera OTP para firma del documento de retanqueo del crédito indicado.
    Solo aplica si el crédito tiene credito_retanqueado y está APROBADO.
    Envía correo al cliente. Retorna dict con success, otp, celular, message.
    """
    credito = Credito.objects.filter(id=credito_id).select_related('cliente').first()
    if not credito:
        return {'success': False, 'message': 'Crédito no encontrado.'}
    if not credito.credito_retanqueado_id:
        return {'success': False, 'message': 'Este crédito no es por retanqueo.'}
    if credito.estado != 'APROBADO':
        return {'success': False, 'message': 'El crédito debe estar aprobado para solicitar documento de retanqueo.'}

    cliente = credito.cliente
    RetanqueoOTP.objects.filter(credito_id=credito_id).delete()

    otp_plain = _generate_otp()
    expires_at = timezone.now() + timedelta(minutes=OTP_VALID_MINUTES)
    RetanqueoOTP.objects.create(
        credito=credito,
        otp_hash=_hash_otp(otp_plain),
        expires_at=expires_at,
    )

    email_destino = (cliente.email or '').strip()
    celular = (cliente.celular or '').strip()
    email_enviado = False
    if email_destino:
        try:
            asunto = 'Código de verificación - Documento de retanqueo de crédito'
            cuerpo = (
                f'Hola {cliente.nombre_completo},\n\n'
                f'Su código para firmar el documento de retanqueo del crédito #{credito.id} es:\n\n  {otp_plain}\n\n'
                f'Válido por {OTP_VALID_MINUTES} minutos.\n\nAtentamente,\nSistema de Créditos'
            )
            EmailMessage(
                asunto, cuerpo,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@creditos.local'),
                [email_destino],
            ).send(fail_silently=True)
            email_enviado = True
        except Exception:
            pass

    message = f'Código enviado a {email_destino}.' if email_enviado else 'Sin correo; use WhatsApp para enviar el código.'
    return {
        'success': True,
        'otp': otp_plain,
        'celular': celular,
        'message': message,
    }


def validar_otp_retanqueo(credito_id, otp_ingresado):
    """
    Valida el OTP, genera el PDF de retanqueo y lo guarda en el crédito.
    Retorna (True, None) o (False, mensaje_error).
    """
    registro = _get_pending_otp(credito_id)
    if not registro:
        return False, 'El código ha expirado o no existe. Solicite uno nuevo.'

    if not _verify_otp((otp_ingresado or '').strip(), registro.otp_hash):
        return False, 'Código incorrecto. Verifique e intente de nuevo.'

    credito = Credito.objects.get(id=credito_id)
    now = timezone.now()
    codigo = f"RET-{now.year}-{credito.id:06d}"

    pdf_file = generar_pdf_retanqueo(credito, codigo=codigo)
    if not pdf_file:
        return False, 'Error al generar el documento.'

    from django.core.files.base import ContentFile
    nombre_archivo = f'retanqueo_credito_{credito.id}_{now.strftime("%Y%m%d_%H%M")}.pdf'
    credito.documento_retanqueo.save(nombre_archivo, ContentFile(pdf_file.getvalue()), save=False)
    credito.fecha_firma_retanqueo = now
    credito.codigo_retanqueo = codigo
    credito.save(update_fields=['documento_retanqueo', 'fecha_firma_retanqueo', 'codigo_retanqueo'])
    registro.delete()
    return True, None


def generar_pdf_retanqueo(credito, codigo=None):
    """
    Genera el PDF del documento de retanqueo: condiciones del crédito nuevo,
    monto aplicado al crédito anterior, texto de aceptación y firma OTP.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    if codigo is None:
        codigo = getattr(credito, 'codigo_retanqueo', None) or f"RET-{timezone.now().year}-{credito.id:06d}"

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=0.75 * inch, leftMargin=0.75 * inch,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
    )
    styles = getSampleStyleSheet()
    normal = styles['Normal']
    small = ParagraphStyle('Small', parent=normal, fontSize=9, spaceAfter=4)
    small_justified = ParagraphStyle('SmallJustified', parent=small, alignment=TA_JUSTIFY)
    small_bold = ParagraphStyle('SmallBold', parent=small, fontName='Helvetica-Bold')
    titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], fontSize=12, spaceAfter=6, alignment=1)

    flow = []

    flow.append(Paragraph('DOCUMENTO DE RETANQUEO DE CRÉDITO', titulo))
    flow.append(Paragraph(f'Código de verificación: {codigo}', small))
    flow.append(Spacer(1, 0.15 * inch))

    flow.append(Paragraph('Condiciones del crédito nuevo (retanqueo):', small_bold))
    flow.append(Spacer(1, 0.08 * inch))

    fecha_solic = credito.fecha_solicitud.strftime('%d/%m/%Y') if credito.fecha_solicitud else '—'
    datos = [
        ['Monto del crédito', f'$ {credito.monto:,.0f}'.replace(',', '.')],
        ['Tasa de interés mensual', f'{credito.tasa_interes}%'],
        ['Plazo', f'{credito.cantidad_cuotas} cuotas {credito.get_tipo_plazo_display().lower()}s'],
        ['Valor de la cuota', f'$ {credito.valor_cuota:,.0f}'.replace(',', '.')],
        ['Monto total a pagar', f'$ {credito.monto_total:,.0f}'.replace(',', '.')],
        ['Fecha de solicitud', fecha_solic],
    ]
    if credito.monto_aplicado_credito_anterior is not None:
        datos.append(['Monto aplicado al crédito anterior', f'$ {credito.monto_aplicado_credito_anterior:,.0f}'.replace(',', '.')])
    if credito.fecha_desembolso:
        datos.append(['Fecha de desembolso', credito.fecha_desembolso.strftime('%d/%m/%Y %H:%M')])
    t = Table(datos, colWidths=[2.2 * inch, 3.5 * inch])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 0.2 * inch))

    cliente = credito.cliente
    flow.append(Paragraph('Aceptación de condiciones', small_bold))
    texto_aceptacion = (
        f'Yo, {cliente.nombre_completo}, identificado(a) con cédula de ciudadanía {cliente.cedula}, '
        'en mi calidad de titular del crédito, acepto de manera libre e informada las condiciones del retanqueo indicado en este documento, '
        'incluyendo monto del nuevo crédito, plazo, valor de la cuota, tasa de interés y el monto aplicado al crédito anterior. '
        'Manifiesto que he sido informado(a) de los términos y que el retanqueo se realiza bajo estas condiciones.'
    )
    flow.append(Paragraph(texto_aceptacion, small_justified))
    flow.append(Spacer(1, 0.15 * inch))

    flow.append(Paragraph('Firma digital', small_bold))
    flow.append(Paragraph(
        '• Firmado digitalmente mediante verificación OTP.',
        ParagraphStyle('Disclaimer', parent=small, fontSize=8, alignment=1),
    ))
    flow.append(Paragraph(
        f'Fecha y hora de aceptación: {(timezone.now().strftime("%d/%m/%Y %H:%M"))}',
        small,
    ))
    flow.append(Spacer(1, 0.1 * inch))
    flow.append(Paragraph(
        f'Documento generado por el sistema. Código: {codigo}',
        ParagraphStyle('Code', parent=small, fontSize=7, textColor=colors.grey, alignment=1),
    ))

    try:
        doc.build(flow)
        buffer.seek(0)
        return buffer
    except Exception:
        return None
