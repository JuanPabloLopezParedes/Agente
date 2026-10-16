import os
import json
import uuid
import time
from datetime import datetime
from enum import Enum
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

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

# 3. Esquema Pydantic Ampliado con Métricas de Negocio
class AnalisisPQRS(BaseModel):
    tipo: TipoPQRS = Field(description="Clasificación principal del mensaje del usuario")
    prioridad: Prioridad = Field(description="Nivel de urgencia evaluado")
    departamento: Departamento = Field(description="Área encargada de atender la solicitud")
    sentimiento_cliente: str = Field(description="Estado emocional del cliente (ej. Frustrado, Neutral, Agradecido)")
    resumen: str = Field(description="Resumen breve del caso en una sola oración")
    requiere_escalado_humano: bool = Field(description="True si la solicitud requiere intervención humana urgente")
    alerta_legal_o_regulatoria: bool = Field(description="True si menciona entidades reguladoras, tutelas, abogados o demandas")
    sla_horas: int = Field(description="Horas máximas de compromiso de respuesta (SLA) sugeridas según gravedad")
    acciones_sugeridas: list[str] = Field(description="Lista de 2 a 3 pasos concretos que el equipo interno debe ejecutar")
    palabras_clave: list[str] = Field(description="Lista de 3 a 5 palabras clave extraídas del caso")
    borrador_respuesta: str = Field(description="Respuesta profesional y empática dirigida al cliente")

# 4. Función de análisis con redundancia de modelos (Fallback y Reintentos)
# 4. Función de análisis con modelos activos y estables
# 4. Función de análisis con los modelos actualizados de Google
def analizar_pqrs(texto_cliente: str) -> AnalisisPQRS:
    prompt = f"""
    Eres un agente inteligente experto en gestión y triaje operativo de PQRS.
    Analiza la siguiente solicitud enviada por un cliente y extrae la información requerida bajo el esquema estructurado.

    Mensaje del cliente:
    \"\"\"{texto_cliente}\"\"\"
    """

    # Modelos activos recomendados por la API de Google Gemini
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
                # Si el servidor se encuentra saturado (503/429), reintenta con pausa
                if any(k in error_str for k in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"]):
                    time.sleep(2 * (intento + 1))
                else:
                    break  # Si el modelo no existe (404) u ocurre otro error, pasa de inmediato al siguiente modelo

    raise RuntimeError(f"El servicio de IA no estuvo disponible. Detalle: {ultimo_error}")
# 5. Sistema de Persistencia y Gestión de Estados
DB_FILE = "tickets_pqrs.json"

def guardar_ticket(analisis: AnalisisPQRS, texto_original: str):
    ticket_data = {
        "id_ticket": f"PQRS-{str(uuid.uuid4())[:8].upper()}",
        "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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