# agente_pqrs.py (Cerebro del Sistema)

Contiene el procesamiento de lenguaje natural y las reglas de negocio.

- Se conecta con la [[Gemini_API]] para procesar las PQRS.
- Valida que la respuesta sea estricta usando el esquema [[AnalisisPQRS_Pydantic]].
- Si hay prioridad Alta o Crítica, activa el [[Escalado_Humano]].
- Guarda el ticket generado en [[tickets_pqrs_json]].