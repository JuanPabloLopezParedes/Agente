import os
import time
from dotenv import load_dotenv
from google import genai

# Se cargan las variables del archivo .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("ERROR: No se encontró la variable GEMINI_API_KEY en el archivo .env")

client = genai.Client(api_key=api_key)

# Modelos incluyendo variantes Lite de menor congestión
candidate_models = [
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
    "gemini-pro-latest"
]

connected = False

for model_name in candidate_models:
    print(f"Intentando conectar con {model_name}...")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Hola. Confirma en una sola frase que la conexión con el Agente de PQRS fue exitosa."
        )
        print(f"\n ¡Conexión Exitosa usando {model_name}!")
        print("Respuesta de Gemini:", response.text)
        connected = True
        break
    except Exception as e:
        print(f" No disponible ({model_name}): {e}\n")
        time.sleep(1)

if not connected:
    print("Los servidores de Google siguen saturados. Espera 30 segundos y vuelve a ejecutar.")