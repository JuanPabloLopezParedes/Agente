import os
import json
import io
import csv
import streamlit as st
from agente_pqrs import (
    analizar_pqrs, 
    guardar_ticket, 
    cambiar_estado_ticket, 
    DB_FILE, 
    Prioridad, 
    EstadoTicket
)

# 1. Configuración de página
st.set_page_config(
    page_title="NEXUS AGENT | Gestión Inteligente PQRS",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS Personalizado - Estilo Cibernético (Tech HUD)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;600;700&family=JetBrains+Mono:wght@400;600&family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, .cyber-font {
        font-family: 'Chakra Petch', sans-serif !important;
        letter-spacing: 0.05em;
    }

    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

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
        border-radius: 4px;
        color: #ffffff !important;
        text-transform: uppercase;
    }

    .sidebar-kpi {
        background: rgba(13, 17, 23, 0.85);
        border: 1px solid rgba(0, 243, 255, 0.2);
        border-left: 4px solid #00f3ff;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 12px;
        color: #f8fafc;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: all 0.25s ease;
    }

    .kpi-title {
        font-family: 'Chakra Petch', sans-serif;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #00f3ff;
        font-weight: 600;
        margin-bottom: 4px;
    }

    .kpi-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.7rem;
        font-weight: 700;
        color: #ffffff;
    }

    .sidebar-profile {
        display: flex;
        align-items: center;
        gap: 12px;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(0, 243, 255, 0.2);
        margin-bottom: 1.2rem;
    }

    .stButton>button {
        font-family: 'Chakra Petch', sans-serif !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        border: 1px solid #00f3ff !important;
        background: linear-gradient(135deg, #090d16 0%, #1e1b4b 100%) !important;
        color: #00f3ff !important;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.2) !important;
    }

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

# Helpers
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

def obtener_badge_estado(estado_str: str) -> str:
    e = estado_str.lower()
    if "pendiente" in e:
        return '<span class="badge" style="background-color: #b45309; border: 1px solid #f59e0b;">⏳ PENDIENTE</span>'
    elif "proceso" in e:
        return '<span class="badge" style="background-color: #1d4ed8; border: 1px solid #3b82f6;">⚙️ EN PROCESO</span>'
    else:
        return '<span class="badge" style="background-color: #15803d; border: 1px solid #22c55e;">✅ RESUELTO</span>'

def cargar_tickets():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def generar_csv(tickets):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID Ticket", "Fecha", "Estado", "Tipo", "Prioridad", "Departamento", "SLA (Horas)", "Alerta Legal", "Mensaje Original"])
    for t in tickets:
        a = t.get("analisis", {})
        writer.writerow([
            t.get("id_ticket"),
            t.get("fecha_registro"),
            t.get("estado", "Pendiente"),
            a.get("tipo"),
            a.get("prioridad"),
            a.get("departamento"),
            a.get("sla_horas", "N/A"),
            "SÍ" if a.get("alerta_legal_o_regulatoria") else "NO",
            t.get("mensaje_original")
        ])
    return output.getvalue()

tickets_lista = cargar_tickets()

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-profile">
        <img src="https://png.pngtree.com/png-vector/20241009/ourmid/pngtree-3d-robots-png-image_14024071.png" width="55">
        <div class="profile-info">
            <h3>NEXUS AGENT</h3>
            <p>● ONLINE | v3.0 Pro</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    total_tickets = len(tickets_lista)
    escalados = sum(1 for t in tickets_lista if t["analisis"].get("requiere_escalado_humano"))
    pct_escalados = (escalados / total_tickets * 100) if total_tickets > 0 else 0.0
    alertas_legales = sum(1 for t in tickets_lista if t["analisis"].get("alerta_legal_o_regulatoria"))

    st.markdown(f"""
    <div class="sidebar-kpi">
        <div class="kpi-title">⚡ Total Procesados</div>
        <div class="kpi-value">{total_tickets}</div>
    </div>

    <div class="sidebar-kpi" style="border-left-color: #ff2a5f;">
        <div class="kpi-title" style="color: #ff2a5f;">⚠️ Escalados a Humanos</div>
        <div class="kpi-value">{escalados} <span style="font-size:0.9rem;">({pct_escalados:.1f}%)</span></div>
    </div>

    <div class="sidebar-kpi" style="border-left-color: #d946ef;">
        <div class="kpi-title" style="color: #d946ef;">⚖️ Alertas Legales / Tutelas</div>
        <div class="kpi-value">{alertas_legales}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div class="cyber-sys-status">
        <div><b>Motor:</b> <span style="color: #00f3ff;">Gemini Multimodels</span></div>
        <div><b>SLA Engine:</b> <span style="color: #00ff66;">🟢 Activo</span></div>
        <div><b>Persistencia:</b> <span style="color: #f8fafc;">JSON Store</span></div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# CABECERA PRINCIPAL
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>🤖 Agente Inteligente de Gestión de PQRS</h1>
    <p>Triaje automático, cálculo de SLA, detección de riesgos legales y enrutamiento operativo.</p>
</div>
""", unsafe_allow_html=True)

tab_nueva, tab_historial = st.tabs(["✨ Registrar & Analizar PQRS", "🗂️ Historial & Gestión de Tickets"])

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
            placeholder="Ejemplo: Buenas tardes, llevo dos días sin servicio de internet en mi domicilio. Si no me dan respuesta hoy mismo instauraré una tutela con mi abogado..."
        )
        btn_procesar = st.button("🚀 Analizar Solicitud con IA", type="primary", use_container_width=True)

    with col_info:
        st.info(
            "💡 **Capacidades Avanzadas v3.0:**\n\n"
            "1. **Cálculo de SLA:** Asigna horas límite de respuesta.\n"
            "2. **Detección Legal:** Identifica amenazas reglamentarias o demandas.\n"
            "3. **Checklist Operativo:** Pasos concretos para el personal técnico.\n"
            "4. **Borrador Empático:** Redacción automatizada de respuesta."
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
                    st.success(f"✅ **Ticket Generado Exitosamente:** `{ticket['id_ticket']}` | **Estado Inicial:** `Pendiente`")

                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Tipo de PQRS", analisis.tipo.value)
                    c2.metric("Departamento", analisis.departamento.value)
                    c3.metric("SLA Compromiso", f"⏱️ {analisis.sla_horas} Horas")
                    c4.markdown(
                        f"**Prioridad:**<br>{obtener_badge_prioridad(analisis.prioridad.value)}", 
                        unsafe_allow_html=True
                    )

                    st.markdown("### 📋 Diagnóstico & Riesgos")
                    
                    if analisis.alerta_legal_o_regulatoria:
                        st.warning("⚖️ **ALERTA LEGAL / REGULATORIA DETECTADA:** El cliente menciona posibles acciones legales o entes reguladores. Tratar con máxima cautela.")

                    if analisis.requiere_escalado_humano or analisis.prioridad in [Prioridad.ALTA, Prioridad.CRITICA]:
                        st.error(
                            f"🚨 **REQUIERE INTERVENCIÓN HUMANA URGENTE**\n\n"
                            f"El agente ha determinado que este caso debe ser gestionado por el departamento de **{analisis.departamento.value}**."
                        )
                    else:
                        st.success("✅ **AUTOMATIZABLE:** Este caso puede gestionarse mediante respuesta estándar de primer nivel.")

                    st.markdown(f"**Resumen Ejecutivo:** {analisis.resumen}")

                    col_acc, col_resp = st.columns(2)
                    with col_acc:
                        st.markdown("### 🛠️ Acciones Recomendadas para el Equipo")
                        for idx, accion in enumerate(analisis.acciones_sugeridas, 1):
                            st.write(f"**{idx}.** {accion}")
                        
                        st.markdown("**Palabras Clave Extraídas:**")
                        st.write(" • ".join([f"`{tag}`" for tag in analisis.palabras_clave]))

                    with col_resp:
                        st.markdown("### 📩 Borrador de Respuesta al Cliente")
                        st.text_area(
                            "Respuesta sugerida:",
                            value=analisis.borrador_respuesta,
                            height=170
                        )

                except Exception as e:
                    st.error(f"Error procesando la solicitud: {e}")

# ---------------------------------------------------------
# PESTAÑA 2: Historial, Filtros y Gestión de Estados
# ---------------------------------------------------------
with tab_historial:
    st.subheader("Gestión e Historial de Solicitudes")
    
    tickets_actualizados = cargar_tickets()

    if not tickets_actualizados:
        st.info("No hay tickets almacenados en el sistema actualmente.")
    else:
        # Barra superior de Filtros y Descarga
        col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1])
        
        busqueda = col_f1.text_input("🔍 Buscar por ID o texto:", placeholder="Ej: PQRS-8F2A o internet")
        filtro_prioridad = col_f2.selectbox("Filtrar Prioridad", ["Todas"] + [p.value for p in Prioridad])
        filtro_estado = col_f3.selectbox("Filtrar Estado", ["Todos"] + [e.value for e in EstadoTicket])
        
        # Botón de Descargar CSV
        csv_data = generar_csv(tickets_actualizados)
        col_f4.download_button(
            label="📥 Exportar CSV",
            data=csv_data,
            file_name="reporte_pqrs_nexus.csv",
            mime="text/csv",
            use_container_width=True
        )

        # Filtrado dinámico
        filtrados = []
        for t in tickets_actualizados:
            a = t.get("analisis", {})
            match_busqueda = (
                busqueda.lower() in t["id_ticket"].lower() or 
                busqueda.lower() in t["mensaje_original"].lower() or 
                busqueda.lower() in a.get("resumen", "").lower()
            )
            match_prioridad = (filtro_prioridad == "Todas") or (a.get("prioridad") == filtro_prioridad)
            match_estado = (filtro_estado == "Todos") or (t.get("estado", "Pendiente") == filtro_estado)

            if match_busqueda and match_prioridad and match_estado:
                filtrados.append(t)

        st.caption(f"Mostrando {len(filtrados)} de {len(tickets_actualizados)} tickets registrados.")

        for t in reversed(filtrados):
            a = t.get("analisis", {})
            p_val = a.get("prioridad", "Baja")
            estado_curr = t.get("estado", EstadoTicket.PENDIENTE.value)
            
            titulo_expander = f"🎫 {t['id_ticket']} | {estado_curr.upper()} | {p_val.upper()} | {a.get('tipo')} - {a.get('departamento')} ({t['fecha_registro']})"
            
            with st.expander(titulo_expander):
                col_info_t, col_est_t = st.columns([3, 1])
                
                with col_info_t:
                    st.markdown(f"**Mensaje Original del Cliente:**")
                    st.caption(f'"{t["mensaje_original"]}"')
                    st.markdown(f"**Resumen:** {a.get('resumen')}")
                    
                with col_est_t:
                    st.markdown("**Cambiar Estado:**")
                    nuevo_est = st.selectbox(
                        "Estado actual:",
                        options=[e.value for e in EstadoTicket],
                        index=[e.value for e in EstadoTicket].index(estado_curr) if estado_curr in [e.value for e in EstadoTicket] else 0,
                        key=f"select_{t['id_ticket']}"
                    )
                    if nuevo_est != estado_curr:
                        if cambiar_estado_ticket(t['id_ticket'], nuevo_est):
                            st.success("¡Estado actualizado!")
                            st.rerun()

                st.markdown("---")
                c_a, c_b, c_c, c_d = st.columns(4)
                c_a.markdown(f"**Prioridad:** {obtener_badge_prioridad(p_val)}", unsafe_allow_html=True)
                c_b.markdown(f"**Estado:** {obtener_badge_estado(estado_curr)}", unsafe_allow_html=True)
                c_c.write(f"**SLA:** {a.get('sla_horas', 'N/A')} Horas")
                c_d.write(f"**Alerta Legal:** {'🚨 SÍ' if a.get('alerta_legal_o_regulatoria') else '🟢 NO'}")

                st.markdown("\n**Acciones Sugeridas:**")
                st.write(", ".join(a.get("acciones_sugeridas", [])))

                st.markdown("**Borrador Propuesto:**")
                st.info(a.get('borrador_respuesta'))