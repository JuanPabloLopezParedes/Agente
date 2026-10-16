import os
import json
import uuid
import time
import re
import io
import smtplib
from datetime import datetime
from enum import Enum
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# Librería para verificación de registros MX de DNS
import dns.resolver

# Librerías para generación de PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Librería moderna de correo con soporte UTF-8 nativo
from email.message import EmailMessage

# 1. Cargar configuración y cliente
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("ERROR: No se encontró la variable GEMINI_API_KEY en el archivo .env")

client = genai.Client(api_key=api_key)

# 2. Definición de Enums
class TipoPQRS(str, Enum):
    PETICION = "Petición"
    QUEJA = "Queja"
    RECLAMO = "Reclamo"
    SUGERENCIA = "Sugerencia"

class Prioridad(str, Enum):
    BAJA = "Baja"
    MEDIA = "Media"
    ALTA = "Alta"
    CRITICA = "Crítica"

class Departamento(str, Enum):
    SOPORTE_TECNICO = "Soporte Técnico"
    FACTURACION = "Facturación"
    VENTAS = "Ventas"
    SERVICIO_CLIENTE = "Servicio al Cliente"
    LEGAL = "Legal"

class EstadoTicket(str, Enum):
    PENDIENTE = "Pendiente"
    EN_PROCESO = "En Proceso"
    RESUELTO = "Resuelto"

# 3. Esquema Pydantic
class AnalisisPQRS(BaseModel):
    tipo: TipoPQRS = Field(description="Clasificación principal del mensaje del usuario")
    prioridad: Prioridad = Field(description="Nivel de urgencia evaluado")
    departamento: Departamento = Field(description="Área encargada de atender la solicitud")
    sentimiento_cliente: str = Field(description="Estado emocional del cliente")
    resumen: str = Field(description="Resumen breve del caso en una sola oración")
    requiere_escalado_humano: bool = Field(description="True si la solicitud requiere intervención humana urgente")
    alerta_legal_o_regulatoria: bool = Field(description="True si menciona entidades reguladoras, tutelas o demandas")
    sla_horas: int = Field(description="Horas máximas de compromiso de respuesta (SLA) sugeridas")
    acciones_sugeridas: list[str] = Field(description="Lista de 2 a 3 pasos concretos para resolver el caso")
    palabras_clave: list[str] = Field(description="Lista de 3 a 5 palabras clave extraídas")
    borrador_respuesta: str = Field(description="Respuesta profesional y empática dirigida al cliente")

# 4. Función de Validación de Correo Electrónico
def validar_correo_existente(email: str) -> tuple[bool, str]:
    email = email.strip()
    
    # a. Validación Sintáctica con Expresión Regular
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(patron, email):
        return False, "El formato del correo electrónico es inválido (ejemplo: usuario@dominio.com)."
    
    # b. Verificación de Dominio Activo mediante Consulta DNS MX
    dominio = email.split('@')[1]
    try:
        dns.resolver.resolve(dominio, 'MX')
        return True, "Correo válido y dominio de correo existente."
    except Exception:
        return True, "Sintaxis de correo válida."

# 5. Función de análisis con IA (Gemini API)
def analizar_pqrs(texto_cliente: str) -> AnalisisPQRS:
    prompt = f"""
    Eres un agente inteligente experto en gestión y triaje operativo de PQRS.
    Analiza la siguiente solicitud enviada por un cliente y extrae la información requerida bajo el esquema estructurado.

    Mensaje del cliente:
    \"\"\"{texto_cliente}\"\"\"
    """

    modelos_candidatos = [
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash"
    ]

    ultimo_error = None

    for modelo in modelos_candidatos:
        for intento in range(3):
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=AnalisisPQRS,
                        temperature=0.1
                    ),
                )
                return AnalisisPQRS.model_validate_json(response.text)

            except Exception as e:
                ultimo_error = e
                error_str = str(e)
                if any(k in error_str for k in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"]):
                    time.sleep(2 * (intento + 1))
                else:
                    break

    raise RuntimeError(f"El servicio de IA no estuvo disponible. Detalle: {ultimo_error}")

# 6. Generador de PDF de Plan de Soluciones
def generar_pdf_plan_solucion(ticket: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'SubTitleStyle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=colors.HexColor('#0284c7'),
        spaceAfter=6
    )

    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    story = []
    analisis = ticket.get("analisis", {})

    story.append(Paragraph("NEXUS AGENT - PLAN DE SOLUCIÓN Y RESPUESTA PQRS", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#0284c7'), spaceAfter=12))

    data_meta = [
        [Paragraph("<b>ID Ticket:</b>", normal_style), Paragraph(ticket.get("id_ticket", ""), normal_style),
         Paragraph("<b>Fecha:</b>", normal_style), Paragraph(ticket.get("fecha_registro", ""), normal_style)],
        [Paragraph("<b>Tipo:</b>", normal_style), Paragraph(str(analisis.get("tipo")), normal_style),
         Paragraph("<b>Prioridad:</b>", normal_style), Paragraph(str(analisis.get("prioridad")), normal_style)],
        [Paragraph("<b>Departamento:</b>", normal_style), Paragraph(str(analisis.get("departamento")), normal_style),
         Paragraph("<b>SLA Compromiso:</b>", normal_style), Paragraph(f"{analisis.get('sla_horas', 'N/A')} Horas", normal_style)],
    ]

    t_meta = Table(data_meta, colWidths=[90, 160, 90, 160])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 12))

    story.append(Paragraph("1. Diagnóstico y Resumen del Caso", subtitle_style))
    story.append(Paragraph(f"<b>Mensaje Original:</b> \"{ticket.get('mensaje_original', '')}\"", normal_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>Resumen de IA:</b> {analisis.get('resumen', '')}", normal_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("2. Plan de Acción y Checklist Operativo", subtitle_style))
    acciones = analisis.get("acciones_sugeridas", [])
    for idx, acc in enumerate(acciones, 1):
        story.append(Paragraph(f"<b>Paso {idx}:</b> {acc}", normal_style))
        story.append(Spacer(1, 3))
    story.append(Spacer(1, 10))

    story.append(Paragraph("3. Respuesta Oficial para el Cliente", subtitle_style))
    story.append(Paragraph(analisis.get("borrador_respuesta", ""), normal_style))
    story.append(Spacer(1, 15))

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1'), spaceAfter=8))
    story.append(Paragraph("Documento oficial generado automáticamente por el Sistema de Gestión NEXUS AGENT.", normal_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

# 7. Envío de Correo Electrónico (EmailMessage con UTF-8 NATIVO)
def enviar_correo_con_pdf(correo_destino: str, ticket: dict, pdf_bytes: bytes) -> tuple[bool, str]:
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        return False, "No se configuraron las credenciales de correo en el archivo .env (SMTP_USER / SMTP_PASSWORD)."

    try:
        id_t = ticket.get('id_ticket', '')

        # Crear mensaje con la API moderna de Python (Soporte UTF-8 nativo)
        msg = EmailMessage()
        msg['Subject'] = f"Respuesta a su PQRS [{id_t}] - Plan de Soluciones"
        msg['From'] = smtp_user
        msg['To'] = correo_destino

        # Versión en texto plano
        msg.set_content(
            f"Estimado(a) Usuario(a),\n\n"
            f"Le informamos que su solicitud registrada bajo el radicado {id_t} ha sido analizada y procesada con éxito.\n"
            f"Adjunto a este correo encontrará el documento PDF con el Plan de Soluciones y Respuesta Oficial.\n\n"
            f"Atentamente,\nNEXUS AGENT"
        )

        # Versión en HTML
        cuerpo_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #0284c7;">Estimado(a) Usuario(a),</h2>
            <p>Le informamos que su solicitud registrada bajo el radicado <b>{id_t}</b> ha sido analizada y procesada con éxito.</p>
            <p>Adjunto a este correo encontrará el documento en formato <b>PDF</b> con el <b>Plan de Soluciones y Respuesta Oficial</b>.</p>
            <hr style="border: none; border-top: 1px solid #ccc;">
            <p style="font-size: 0.85rem; color: #666;">Este es un mensaje automático generado por el Agente Inteligente NEXUS AGENT.</p>
        </body>
        </html>
        """
        msg.add_alternative(cuerpo_html, subtype='html')

        # Adjuntar PDF
        msg.add_attachment(
            pdf_bytes,
            maintype='application',
            subtype='pdf',
            filename=f"Plan_Soluciones_{id_t}.pdf"
        )

        # Enviar vía SMTP
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return True, f"Correo enviado exitosamente a: {correo_destino}"
    except Exception as e:
        return False, f"Error al enviar el correo: {str(e)}"

# 8. Persistencia de Datos
DB_FILE = "tickets_pqrs.json"

def guardar_ticket(analisis: AnalisisPQRS, texto_original: str, correo_cliente: str):
    ticket_data = {
        "id_ticket": f"PQRS-{str(uuid.uuid4())[:8].upper()}",
        "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "correo_cliente": correo_cliente,
        "estado": EstadoTicket.PENDIENTE.value,
        "mensaje_original": texto_original,
        "analisis": analisis.model_dump()
    }

    tickets = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                tickets = json.load(f)
            except json.JSONDecodeError:
                tickets = []

    tickets.append(ticket_data)

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(tickets, f, ensure_ascii=False, indent=4)

    return ticket_data

def cambiar_estado_ticket(id_ticket: str, nuevo_estado: str):
    if not os.path.exists(DB_FILE):
        return False

    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            tickets = json.load(f)
        except json.JSONDecodeError:
            return False

    actualizado = False
    for t in tickets:
        if t["id_ticket"] == id_ticket:
            t["estado"] = nuevo_estado
            actualizado = True
            break

    if actualizado:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(tickets, f, ensure_ascii=False, indent=4)

    return actualizado