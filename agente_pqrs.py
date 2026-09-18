import os
import json
import uuid
from datetime import datetime
from enum import Enum
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("ERROR: No se encontró la variable GEMINI_API_KEY en el archivo .env")

client = genai.Client(api_key=api_key)

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

# Esquema Pydantic ampliado
class AnalisisPQRS(BaseModel):
    tipo: TipoPQRS = Field(description="Clasificación exacta del mensaje del usuario")
    prioridad: Prioridad = Field(description="Nivel de urgencia evaluado")
    justificacion_prioridad: str = Field(description="Explicación técnica de 1 frase del porqué de la prioridad")
    departamento: Departamento = Field(description="Área especializada para resolver el caso")
    sentimiento_cliente: str = Field(description="Tono emocional del cliente (ej. Frustrado, Amable, Indignado, Neutral)")
    resumen: str = Field(description="Resumen ejecutivo del problema central en 1 sola frase")
    pasos_accion_interna: list[str] = Field(description="Lista de 2 a 3 tareas clave que debe realizar el equipo interno para resolver la PQRS")
    requiere_escalado_humano: bool = Field(description="True si implica cobros indebidos, fallas totales de servicio, amenazas legales o enfado extremo")
    borrador_respuesta: str = Field(description="Respuesta profesional, empática, personalizada y estructurada para el cliente")

def analizar_pqrs(texto_cliente: str) -> AnalisisPQRS:
    prompt_sistema = """
    Eres un Agente Senior de Servicio al Cliente y Gestión Operativa de PQRS.
    Tu objetivo es analizar la solicitud enviada por el cliente y generar una respuesta con estándares de excelencia en atención.

    CRITERIOS DE PRIORIZACIÓN:
    - CRÍTICA: Amenazas legales, pérdidas financieras graves, fallas masivas del servicio o clientes extremadamente indignados.
    - ALTA: Interrupción total del servicio de un usuario, errores repetidos de facturación.
    - MEDIA: Peticiones complejas, fallas parciales, solicitudes de ajustes de cuenta.
    - BAJA: Consultas generales, sugerencias, retroalimentación positiva.

    REGLAS PARA EL BORRADOR DE RESPUESTA:
    1. Inicia con un saludo formal pero cálido.
    2. Muestra empatía genuina reconociendo la frustración o solicitud específica del usuario.
    3. Explica los pasos claros que la empresa está tomando para darle solución.
    4. Proporciona una expectativa de tiempo realista para la resolución final.
    5. Despídete cordialmente manteniendo la elegancia institucional.
    """

    prompt_usuario = f"""
    Analiza la siguiente PQRS enviada por el usuario:
    \"\"\"{texto_cliente}\"\"\"
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_usuario,
        config=types.GenerateContentConfig(
            system_instruction=prompt_sistema,
            response_mime_type="application/json",
            response_schema=AnalisisPQRS,
            temperature=0.2
        ),
    )

    return AnalisisPQRS.model_validate_json(response.text)

DB_FILE = "tickets_pqrs.json"

def guardar_ticket(analisis: AnalisisPQRS, texto_original: str):
    ticket_data = {
        "id_ticket": f"PQRS-{str(uuid.uuid4())[:8].upper()}",
        "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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