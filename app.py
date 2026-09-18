import os
import json
import streamlit as st
from agente_pqrs import analizar_pqrs, guardar_ticket, DB_FILE, Prioridad

# 1. Configuración de página
st.set_page_config(
    page_title="Gestión Inteligente de PQRS",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inyección de CSS Personalizado - Estilo Cibernético Elegant (Tech HUD)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;600;700&family=JetBrains+Mono:wght@400;600&family=Inter:wght@300;400;600;700&display=swap');
    
    /* Tipografía General */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Fuentes de estilo cibernético para Encabezados y Títulos */
    h1, h2, h3, .cyber-font {
        font-family: 'Chakra Petch', sans-serif !important;
        letter-spacing: 0.05em;
    }

    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Encabezado Principal Cibernético */
    .main-header {
        background: linear-gradient(135deg, #090d16 0%, #0f172a 100%);
        padding: 2rem;
        border-radius: 12px;
        color: #ffffff;
        margin-bottom: 2rem;
        border: 1px solid rgba(0, 243, 255, 0.25);
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.12), inset 0 0 15px rgba(0, 243, 255, 0.03);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, #00f3ff, #a855f7, #00f3ff);
    }
    
    .main-header h1 {
        font-family: 'Chakra Petch', sans-serif;
        color: #00f3ff;
        font-weight: 700;
        font-size: 2.2rem;
        margin: 0;
        text-shadow: 0 0 12px rgba(0, 243, 255, 0.4);
    }
    
    .main-header p {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-top: 0.5rem;
    }

    /* Insignias de Prioridad Cibernéticas con destello Glow */
    .badge {
        display: inline-block;
        padding: 0.4em 0.85em;
        font-family: 'Chakra Petch', sans-serif;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 4px;
        color: #ffffff !important;
        text-transform: uppercase;
    }

    /* Tarjetas de Métricas del Sidebar (Estilo Tarjeta de Datos) */
    .sidebar-kpi {
        background: rgba(13, 17, 23, 0.85);
        border: 1px solid rgba(0, 243, 255, 0.2);
        border-left: 4px solid #00f3ff;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 12px;
        color: #f8fafc;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: all 0.25 ease;
    }
    
    .sidebar-kpi:hover {
        border-color: #00f3ff;
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.25);
        transform: translateX(3px);
    }

    .kpi-title {
        font-family: 'Chakra Petch', sans-serif;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #00f3ff;
        font-weight: 600;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .kpi-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.7rem;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.2;
        text-shadow: 0 0 8px rgba(255, 255, 255, 0.2);
    }

    .kpi-subtext {
        font-size: 0.75rem;
        margin-top: 4px;
        font-weight: 500;
    }

    .sub-green { color: #00ff66; text-shadow: 0 0 5px rgba(0, 255, 102, 0.3); }
    .sub-red { color: #ff2a5f; text-shadow: 0 0 5px rgba(255, 42, 95, 0.3); }
    .sub-yellow { color: #ffcc00; text-shadow: 0 0 5px rgba(255, 204, 0, 0.3); }
    .sub-blue { color: #00f3ff; text-shadow: 0 0 5px rgba(0, 243, 255, 0.3); }

    /* Perfil del Agente en el Sidebar */
    .sidebar-profile {
        display: flex;
        align-items: center;
        gap: 12px;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(0, 243, 255, 0.2);
        margin-bottom: 1.2rem;
    }

    .sidebar-profile img {
        border-radius: 8px;
        background: #090d16;
        padding: 4px;
        border: 1px solid #00f3ff;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.3);
    }

    .profile-info h3 {
        font-family: 'Chakra Petch', sans-serif;
        margin: 0;
        font-size: 1.1rem;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: 0.05em;
    }

    .profile-info p {
        font-family: 'JetBrains Mono', monospace;
        margin: 0;
        font-size: 0.75rem;
        color: #00f3ff;
        font-weight: 600;
        text-shadow: 0 0 5px rgba(0, 243, 255, 0.5);
    }

    /* Botón Cibernético Estilizado */
    .stButton>button {
        font-family: 'Chakra Petch', sans-serif !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        border: 1px solid #00f3ff !important;
        background: linear-gradient(135deg, #090d16 0%, #1e1b4b 100%) !important;
        color: #00f3ff !important;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.2) !important;
        transition: all 0.3s ease-in-out !important;
    }

    .stButton>button:hover {
        background: #00f3ff !important;
        color: #090d16 !important;
        box-shadow: 0 0 20px rgba(0, 243, 255, 0.7) !important;
        transform: translateY(-1px);
    }

    /* Caja de Infraestructura */
    .cyber-sys-status {
        background: rgba(9, 13, 22, 0.9);
        padding: 12px;
        border-radius: 6px;
        border: 1px solid rgba(0, 243, 255, 0.2);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)

# Helper para badges de prioridad cibernéticos con glow
def obtener_badge_prioridad(prioridad_str: str) -> str:
    p = prioridad_str.lower().replace("í", "i")
    colores = {
        "baja": {"bg": "#059669", "border": "#10b981", "glow": "rgba(16, 185, 129, 0.4)", "label": "🟢 BAJA"},
        "media": {"bg": "#d97706", "border": "#f59e0b", "glow": "rgba(245, 158, 11, 0.4)", "label": "🟡 MEDIA"},
        "alta": {"bg": "#dc2626", "border": "#ef4444", "glow": "rgba(239, 68, 68, 0.4)", "label": "🔴 ALTA"},
        "critica": {"bg": "#701a75", "border": "#d946ef", "glow": "rgba(217, 70, 239, 0.5)", "label": "🚨 CRÍTICA"}
    }
    config = colores.get(p, {"bg": "#334155", "border": "#64748b", "glow": "rgba(100, 116, 139, 0.4)", "label": prioridad_str.upper()})
    return f'<span class="badge" style="background-color: {config["bg"]}; border: 1px solid {config["border"]}; box-shadow: 0 0 10px {config["glow"]};">{config["label"]}</span>'

# Helper para emoji rápido
def obtener_emoji_prioridad(prioridad_str: str) -> str:
    p = prioridad_str.lower().replace("í", "i")
    emojis = {"baja": "🟢", "media": "🟡", "alta": "🔴", "critica": "🚨"}
    return emojis.get(p, "⚪")

# Helper para cargar tickets
def cargar_tickets():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

tickets_lista = cargar_tickets()

# ---------------------------------------------------------
# SIDEBAR: Panel Estadístico Avanzado & Ejecutivo (Cyber HUD)
# ---------------------------------------------------------
with st.sidebar:
    # Header del Panel con Avatar/Icono estilizado
    st.markdown("""
    <div class="sidebar-profile">
        <img src="https://png.pngtree.com/png-vector/20241009/ourmid/pngtree-3d-robots-png-image_14024071.png" width="55">
        <div class="profile-info">
            <h3>NEXUS AGENT</h3>
            <p>● ONLINE | v2.4</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Cálculo de métricas
    total_tickets = len(tickets_lista)
    escalados = sum(1 for t in tickets_lista if t["analisis"].get("requiere_escalado_humano"))
    pct_escalados = (escalados / total_tickets * 100) if total_tickets > 0 else 0.0
    criticos_altos = sum(1 for t in tickets_lista if t["analisis"].get("prioridad") in ["Alta", "Crítica"])
    
    # Desglose por tipos
    quejas = sum(1 for t in tickets_lista if t["analisis"].get("tipo") == "Queja")
    reclamos = sum(1 for t in tickets_lista if t["analisis"].get("tipo") == "Reclamo")
    peticiones = sum(1 for t in tickets_lista if t["analisis"].get("tipo") == "Petición")
    sugerencias = sum(1 for t in tickets_lista if t["analisis"].get("tipo") == "Sugerencia")

    # Tarjetas KPI CSS Cibernéticas
    st.markdown(f"""
    <div class="sidebar-kpi">
        <div class="kpi-title">⚡ Total Procesados</div>
        <div class="kpi-value">{total_tickets}</div>
        <div class="kpi-subtext sub-blue">Solicitudes registradas</div>
    </div>

    <div class="sidebar-kpi" style="border-left-color: #ff2a5f;">
        <div class="kpi-title" style="color: #ff2a5f;">⚠️ Escalados a Humanos</div>
        <div class="kpi-value">{escalados}</div>
        <div class="kpi-subtext sub-red">{pct_escalados:.1f}% del total recibido</div>
    </div>

    <div class="sidebar-kpi" style="border-left-color: #ffcc00;">
        <div class="kpi-title" style="color: #ffcc00;">🔥 Prioridad Alta / Crítica</div>
        <div class="kpi-value">{criticos_altos}</div>
        <div class="kpi-subtext sub-yellow">Casos de atención urgente</div>
    </div>
    """, unsafe_allow_html=True)

    # Sección Desglose por Categoria
    st.markdown("---")
    st.caption("📈 **DESGLOSE POR TIPO DE PQRS**")
    
    col_d1, col_d2 = st.columns(2)
    col_d1.caption(f"• **Quejas:** {quejas}")
    col_d2.caption(f"• **Reclamos:** {reclamos}")
    col_d1.caption(f"• **Peticiones:** {peticiones}")
    col_d2.caption(f"• **Sugerencias:** {sugerencias}")

    # Pie de Panel: Estado de la infraestructura
    st.markdown("---")
    st.markdown("""
    <div class="cyber-sys-status">
        <div><b>Motor IA:</b> <span style="color: #00f3ff;">Gemini 3.5 Flash Lite</span></div>
        <div><b>Estado API:</b> <span style="color: #00ff66;">🟢 Sync Activa</span></div>
        <div><b>Persistencia:</b> <span style="color: #f8fafc;">JSON Local</span></div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# CABECERA PRINCIPAL
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🤖 Agente Inteligente de Gestión de PQRS</h1>
    <p>Plataforma de procesamiento de lenguaje natural, clasificación de prioridades y generación de respuestas automáticas.</p>
</div>
""", unsafe_allow_html=True)

# Pestañas principales
tab_nueva, tab_historial = st.tabs(["✨ Registrar & Analizar PQRS", "🗂️ Historial de Solicitudes"])

# ---------------------------------------------------------
# PESTAÑA 1: Formulario Inteligente
# ---------------------------------------------------------
with tab_nueva:
    col_input, col_info = st.columns([2, 1])

    with col_input:
        st.subheader("Ingreso de la Solicitud")
        texto_cliente = st.text_area(
            "Escriba el mensaje emitido por el usuario:",
            height=160,
            placeholder="Ejemplo: Buenas tardes, llevo dos días sin servicio de internet en mi domicilio y requiero solución urgente, de lo contrario cancelaré el contrato..."
        )

        btn_procesar = st.button("🚀 Analizar Solicitud con IA", type="primary", use_container_width=True)

    with col_info:
        st.info(
            "💡 **¿Cómo funciona este agente?**\n\n"
            "1. **Extrae** el tipo de solicitud (Petición, Queja, Reclamo, Sugerencia).\n"
            "2. **Determina** el nivel de urgencia y el sentimiento del usuario.\n"
            "3. **Enruta** al departamento correspondiente.\n"
            "4. **Genera** un borrador formal de respuesta."
        )

    if btn_procesar:
        if not texto_cliente.strip():
            st.warning("⚠️ Por favor ingrese un mensaje válido antes de ejecutar el análisis.")
        else:
            with st.spinner("🤖 El agente está evaluando su caso..."):
                try:
                    analisis = analizar_pqrs(texto_cliente)
                    ticket = guardar_ticket(analisis, texto_cliente)

                    st.markdown("---")
                    st.success(f"✅ **Ticket Generado Exitosamente:** `{ticket['id_ticket']}`")

                    # Métricas destacadas con insignia en color para la prioridad
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Tipo de PQRS", analisis.tipo.value)
                    c2.metric("Departamento", analisis.departamento.value)
                    c3.metric("Sentimiento", analisis.sentimiento_cliente)
                    c4.markdown(
                        f"**Prioridad Asignada:**<br>{obtener_badge_prioridad(analisis.prioridad.value)}", 
                        unsafe_allow_html=True
                    )

                    st.markdown("### 📋 Análisis y Diagnóstico")
                    
                    # Alerta visual de escalado
                    if analisis.requiere_escalado_humano or analisis.prioridad in [Prioridad.ALTA, Prioridad.CRITICA]:
                        st.error(
                            f"🚨 **REQUIERE INTERVENCIÓN HUMANA URGENTE**\n\n"
                            f"El agente ha determinado que este caso debe ser revisado por un asesor del departamento de **{analisis.departamento.value}**."
                        )
                    else:
                        st.success("✅ **AUTOMATIZABLE:** Este caso puede gestionarse mediante respuesta estándar de primer nivel.")

                    st.markdown(f"**Resumen Ejecutivo:** {analisis.resumen}")

                    st.markdown("### 📩 Borrador de Respuesta Generado por IA")
                    st.text_area(
                        "Respuesta lista para revisión/envío al cliente:",
                        value=analisis.borrador_respuesta,
                        height=150
                    )

                except Exception as e:
                    st.error(f"Error procesando la solicitud: {e}")

# ---------------------------------------------------------
# PESTAÑA 2: Historial Elegantemente Diseñado
# ---------------------------------------------------------
with tab_historial:
    st.subheader("Historial de Tickets")
    
    # Recargar datos
    tickets_actualizados = cargar_tickets()

    if not tickets_actualizados:
        st.info("No hay tickets almacenados en el sistema actualmente.")
    else:
        st.caption(f"Mostrando {len(tickets_actualizados)} solicitudes registradas.")
        
        for t in reversed(tickets_actualizados):
            a = t["analisis"]
            p_val = a["prioridad"]
            emoji_p = obtener_emoji_prioridad(p_val)
            
            # Título del expander con emoji según prioridad
            titulo_expander = f"🎫 {t['id_ticket']} | {emoji_p} {p_val.upper()} | {a['tipo']} - {a['departamento']} ({t['fecha_registro']})"
            
            with st.expander(titulo_expander):
                st.markdown(f"**Mensaje Original del Cliente:**")
                st.caption(f'"{t["mensaje_original"]}"')
                
                col_a, col_b, col_c = st.columns(3)
                col_a.markdown(f"**Prioridad:**<br>{obtener_badge_prioridad(p_val)}", unsafe_allow_html=True)
                col_b.write(f"**Sentimiento:** {a['sentimiento_cliente']}")
                col_c.write(f"**Escalado a Humano:** {'🔴 Sí' if a['requiere_escalado_humano'] else '🟢 No'}")
                
                st.markdown(f"\n**Resumen:** {a['resumen']}")
                st.markdown(f"**Respuesta propuesta:**")
                st.info(a['borrador_respuesta'])