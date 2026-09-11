import os
import json
import uuid
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

# 3. Esquema Pydantic
class AnalisisPQRS(BaseModel):
    tipo: TipoPQRS = Field(description="Clasificación del mensaje del usuario")
    
    prioridad: Prioridad = Field(description="Nivel de urgencia")
    
    departamento: Departamento = Field(description="Área encargada de atender la solicitud")
    
    sentimiento_cliente: str = Field(description="Estado emocional del cliente")
    
    resumen: str = Field(description="Resumen breve del caso en una oracion")
    
    requiere_escalado_humano: bool = Field(description="True si la solicitud requiere intervención humana urgente")
    
    borrador_respuesta: str = Field(description="Respuesta profesional dirigida al cliente")
    


# 4. Función de análisis con el agente
def analizar_pqrs(texto_cliente: str) -> AnalisisPQRS:
    prompt = f"""
    Eres un agente inteligente especializado en gestión de PQRS.
    Analiza la siguiente solicitud enviada por un cliente y extrae la información requerida bajo el esquema estructurado.

    Mensaje del cliente:
    \"\"\"{texto_cliente}\"\"\"
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=AnalisisPQRS,
            temperature=0.1
        ),
    )

    return AnalisisPQRS.model_validate_json(response.text)



# 5. Sistema de Persistencia y Reglas de Negocio
DB_FILE = "tickets_pqrs.json"

def guardar_ticket(analisis: AnalisisPQRS, texto_original: str):
    ticket_data = {
        "id_ticket": f"PQRS-{str(uuid.uuid4())[:8].upper()}",
        "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mensaje_original": texto_original,
        "analisis": analisis.model_dump()
    }

    # Leer datos existentes o crear lista vacía
    tickets = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                tickets = json.load(f)
            except json.JSONDecodeError:
                tickets = []

    tickets.append(ticket_data)

    # Guardar en archivo JSON
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(tickets, f, ensure_ascii=False, indent=4)

    return ticket_data

def procesar_flujo_pqrs(texto_cliente: str):
    print("\n" + "="*60)
    print("🤖 PROCESANDO NUEVA SOLICITUD DE PQRS...")
    print("="*60)

    # 1. Análisis con IA
    analisis = analizar_pqrs(texto_cliente)

    # 2. Guardar en Base de Datos Local
    ticket = guardar_ticket(analisis, texto_cliente)

    # 3. Mostrar Resumen del Procesamiento
    print(f"\n✅ TICKET CREADO CON ÉXITO | ID: {ticket['id_ticket']}")
    print(f"• Fecha/Hora: {ticket['fecha_registro']}")
    print(f"• Tipo: {analisis.tipo.value}")
    print(f"• Prioridad: {analisis.prioridad.value}")
    print(f"• Departamento Destino: {analisis.departamento.value}")
    print(f"• Sentimiento detectado: {analisis.sentimiento_cliente}")
    print(f"• Resumen: {analisis.resumen}")

    # 4. Evaluación de Reglas de Negocio / Enrutamiento
    print("\n📌 ACCIÓN DEL SISTEMA:")
    if analisis.requiere_escalado_humano or analisis.prioridad in [Prioridad.ALTA, Prioridad.CRITICA]:
        print("⚠️ [ALERTA DE SISTEMA] Este caso requiere intervención humana inmediata.")
        print(f"   🔔 Notificación enviada al equipo de: {analisis.departamento.value}")
    else:
        print("ℹ️ Case resuelto vía respuesta automatizada estándar.")

    print(f"\n📩 RESPUETA SUGERIDA PARA EL CLIENTE:\n{analisis.borrador_respuesta}")
    print("="*60 + "\n")

# 6. Modo Interactivo
if __name__ == "__main__":
    print("=== SISTEMA AGENTE DE GESTIÓN DE PQRS ===")
    print("Escribe 'salir' para finalizar el programa.\n")

    while True:
        entrada = input("Ingrese la PQRS del cliente > ")
        if entrada.lower().strip() == "salir":
            print("\nCerrando el Agente de PQRS. ¡Hasta luego!")
            break
        if not entrada.strip():
            continue
        
        procesar_flujo_pqrs(entrada)