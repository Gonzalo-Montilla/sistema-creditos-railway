# Documento de renovación de crédito - firma OTP
# PDF con condiciones del crédito (monto, fechas, cuota, plazo) + aceptación

import hashlib
import random
import string
from datetime import timedelta
from io import BytesIO
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings

from .models import Cliente, Credito, RenovacionOTP


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
    return RenovacionOTP.objects.filter(
        credito_id=credito_id,
        expires_at__gt=now,
    ).order_by('-created_at').first()


def solicitar_otp_renovacion(credito_id):
    """
    Genera OTP para firma del documento de renovación del crédito indicado.
    Envía correo al cliente. Retorna dict con success, otp, celular, message.
    """
    credito = Credito.objects.filter(id=credito_id).first()
    if not credito:
        return {'success': False, 'message': 'Crédito no encontrado.'}
    if not credito.es_renovacion:
        return {'success': False, 'message': 'Este crédito no es de renovación.'}
    if credito.estado not in ('SOLICITADO', 'APROBADO'):
        return {'success': False, 'message': 'El crédito debe estar en solicitud o aprobado para solicitar documento de renovación.'}

    cliente = credito.cliente
    RenovacionOTP.objects.filter(credito_id=credito_id).delete()

    otp_plain = _generate_otp()
    expires_at = timezone.now() + timedelta(minutes=OTP_VALID_MINUTES)
    RenovacionOTP.objects.create(
        credito=credito,
        otp_hash=_hash_otp(otp_plain),
        expires_at=expires_at,
    )

    email_destino = (cliente.email or '').strip()
    celular = (cliente.celular or '').strip()
    email_enviado = False
    if email_destino:
        try:
            asunto = 'Código de verificación - Documento de renovación de crédito'
            cuerpo = (
                f'Hola {cliente.nombre_completo},\n\n'
                f'Su código para firmar el documento de renovación del crédito #{credito.id} es:\n\n  {otp_plain}\n\n'
                f'Válido por {OTP_VALID_MINUTES} minutos.\n\nAtentamente,\nSistema de Créditos'
            )
            EmailMessage(
                asunto, cuerpo,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@creditos.local'),
                [email_destino],
            ).send(fail_silently=False)
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


def validar_otp_renovacion(credito_id, otp_ingresado):
    """
    Valida el OTP, genera el PDF de renovación con datos del crédito y lo guarda en el cliente.
    Retorna (True, None) o (False, mensaje_error).
    """
    registro = _get_pending_otp(credito_id)
    if not registro:
        return False, 'El código ha expirado o no existe. Solicite uno nuevo.'

    if not _verify_otp((otp_ingresado or '').strip(), registro.otp_hash):
        return False, 'Código incorrecto. Verifique e intente de nuevo.'

    credito = Credito.objects.get(id=credito_id)
    if not credito.es_renovacion:
        return False, 'Este crédito no es de renovación.'
    cliente = credito.cliente
    now = timezone.now()
    codigo = f"REN-{now.year}-{credito.id:06d}"

    pdf_file = generar_pdf_renovacion(cliente, credito, codigo=codigo)
    if not pdf_file:
        return False, 'Error al generar el documento.'

    from django.core.files.base import ContentFile
    nombre_archivo = f'renovacion_credito_{credito.id}_{now.strftime("%Y%m%d_%H%M")}.pdf'
    credito.documento_renovacion.save(nombre_archivo, ContentFile(pdf_file.getvalue()), save=False)
    credito.fecha_firma_renovacion = now
    credito.codigo_renovacion = codigo
    credito.save(update_fields=['documento_renovacion', 'fecha_firma_renovacion', 'codigo_renovacion'])
    registro.delete()
    return True, None


def generar_pdf_renovacion(cliente, credito, codigo=None):
    """
    Genera el PDF del documento de renovación con las condiciones del crédito:
    monto, fechas, valor cuota, plazo, tasa, y texto de aceptación. Firma digital OTP.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    if codigo is None:
        codigo = getattr(credito, 'codigo_renovacion', None) or f"REN-{timezone.now().year}-{credito.id:06d}"

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

    flow.append(Paragraph('DOCUMENTO DE RENOVACIÓN DE CRÉDITO', titulo))
    flow.append(Paragraph(f'Código de verificación: {codigo}', small))
    flow.append(Spacer(1, 0.15 * inch))

    flow.append(Paragraph('Condiciones del crédito con el que se estructura la renovación:', small_bold))
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

    flow.append(Paragraph('Aceptación de condiciones', small_bold))
    texto_aceptacion = (
        f'Yo, {cliente.nombre_completo}, identificado(a) con cédula de ciudadanía {cliente.cedula}, '
        'en mi calidad de titular del crédito, acepto de manera libre e informada las condiciones del crédito indicado en este documento, '
        'incluyendo monto, plazo, valor de la cuota, tasa de interés y fechas. '
        'Manifiesto que he sido informado(a) de los términos y que la renovación se realiza bajo estas condiciones.'
    )
    flow.append(Paragraph(texto_aceptacion, small_justified))
    flow.append(Spacer(1, 0.15 * inch))

    flow.append(Paragraph('Firma digital', small_bold))
    flow.append(Paragraph(
        '&bull; Firmado digitalmente mediante verificación OTP.',
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
