import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
import tempfile
from fpdf import FPDF

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SGSST - DS 44", layout="wide", page_icon="🛡️")

# --- 2. SISTEMA DE AUTO-GUARDADO ---
CSV_FILE = "base_datos_sgsst.csv"

def crear_estructura_completa():
    return pd.DataFrame({
        'Año': [2024],
        'Mes': ['Enero'],
        # DATOS BASE
        'Masa Laboral': [100],
        'HHT': [18000],
        # SEGURIDAD (REACTIVOS)
        'Accidentes CTP': [0],
        'Días Perdidos': [0],
        'Días Cargo': [0],
        # GESTIÓN PREVENTIVA (PROACTIVOS)
        'Insp. Programadas': [10],
        'Insp. Ejecutadas': [10],
        'Cap. Programadas': [5],
        'Cap. Ejecutadas': [5],
        'Cierre Medidas Correctivas (%)': [100], 
        # SALUD OCUPACIONAL (DS 44 / MINSAL)
        'Expuestos Ruido (PREXOR)': [0],
        'Vigilancia Salud al Día (%)': [100],
        'Entrega EPP (%)': [100]
    })

def cargar_datos():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            columnas_nuevas = ['Cierre Medidas Correctivas (%)', 'Expuestos Ruido (PREXOR)', 'Vigilancia Salud al Día (%)']
            # Si faltan columnas, regenerar estructura para evitar errores
            if not all(col in df.columns for col in columnas_nuevas):
                return crear_estructura_completa()
            return df
        except:
            return crear_estructura_completa()
    else:
        return crear_estructura_completa()

def guardar_cambios(df):
    df.to_csv(CSV_FILE, index=False)

if 'df_sgsst' not in st.session_state:
    st.session_state['df_sgsst'] = cargar_datos()

# --- 3. ESTILOS CSS ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    .kpi-card {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .kpi-title { font-size: 13px; color: #555; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
    .kpi-value { font-size: 26px; font-weight: bold; color: #222; }
    .kpi-footer { font-size: 11px; color: #888; margin-top: 5px; }
    
    .status-good { color: #2E7D32; }
    .status-warning { color: #F57C00; }
    .status-bad { color: #C62828; }
    </style>
""", unsafe_allow_html=True)

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Configuración")
    
    uploaded_logo = st.file_uploader("Subir Logo Empresa", type=['png', 'jpg', 'jpeg'])
    logo_path = "logo_empresa.png"
    if uploaded_logo:
        with open(logo_path, "wb") as f:
            f.write(uploaded_logo.getbuffer())
    
    st.markdown("---")
    if st.button("⚠️ Restaurar Base de Datos"):
        df_reset = crear_estructura_completa()
        st.session_state['df_sgsst'] = df_reset
        guardar_cambios(df_reset)
        st.rerun()

# --- 5. LÓGICA DE CÁLCULO ---
df = st.session_state['df_sgsst']
tab_dash, tab_data = st.tabs(["📊 DASHBOARD DE GESTIÓN (DS 44)", "📝 INGRESO DE DATOS"])

with tab_dash:
    # --- HEADER ---
    col_header_1, col_header_2 = st.columns([1, 4])
    with col_header_1:
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
        else:
            st.info("Subir Logo")
            
    with col_header_2:
        st.markdown("""
            <div style="text-align:left; padding-top:10px;">
                <h1 style="margin:0; font-size:32px; color:#B71C1C;">SISTEMA DE GESTIÓN SST</h1>
                <h4 style="margin:0; color:#555;">REPORTE MENSUAL DE DESEMPEÑO | NORMATIVA DS 44</h4>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

    # Selectores
    col_sel1, col_sel2 = st.columns(2)
    years = sorted(df['Año'].unique(), reverse=True)
    sel_year = col_sel1.selectbox("Año", years)
    df_year = df[df['Año'] == sel_year]
    
    months = df_year['Mes'].unique().tolist()
    orden_meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    months = sorted(months, key=lambda x: orden_meses.index(x) if x in orden_meses else 99)
    sel_month = col_sel2.selectbox("Mes de Reporte", months, index=len(months)-1 if months else 0)
    
    df_month = df_year[df_year['Mes'] == sel_month]
    
    if not df_month.empty:
        # Variables
        masa = df_month['Masa Laboral'].values[0]
        hht = df_month['HHT'].values[0]
        acc = df_month['Accidentes CTP'].values[0]
        dp = df_month['Días Perdidos'].values[0]
        dc = df_month['Días Cargo'].values[0]
        
        tasa_acc = (acc / masa * 100) if masa > 0 else 0
        tasa_sin = (dp / masa * 100) if masa > 0 else 0
        if_mensual = (acc * 1000000 / hht) if hht > 0 else 0
        
        # Gestión
        insp_p = df_month['Insp. Programadas'].values[0]
        insp_e = df_month['Insp. Ejecutadas'].values[0]
        cumpl_insp = (insp_e / insp_p * 100) if insp_p > 0 else 0
        
        cap_p = df_month['Cap. Programadas'].values[0]
        cap_e = df_month['Cap. Ejecutadas'].values[0]
        cumpl_cap = (cap_e / cap_p * 100) if cap_p > 0 else 0
        
        cierre_medidas = df_month['Cierre Medidas Correctivas (%)'].values[0]
        vigilancia_salud = df_month['Vigilancia Salud al Día (%)'].values[0]
    else:
        st.error("No hay datos para este mes.")
        st.stop()

    # --- SECCIÓN KPIs ---
    st.markdown("### 🚑 Indicadores de Siniestralidad (Reactivos)")
    k1, k2, k3, k4 = st.columns(4)
    
    def kpi_box(col, title, value, footer, color_class=""):
        col.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value {color_class}">{value}</div>
            <div class="kpi-footer">{footer}</div>
        </div>
        """, unsafe_allow_html=True)

    kpi_box(k1, "TASA ACCIDENTABILIDAD", f"{tasa_acc:.2f}%", "Meta: < 3.0%", "status-bad" if tasa_acc > 3 else "status-good")
    kpi_box(k2, "TASA SINIESTRALIDAD", f"{tasa_sin:.2f}", "Días / Trab.", "status-warning" if tasa_sin > 10 else "status-good")
    kpi_box(k3, "ÍNDICE FRECUENCIA", f"{if_mensual:.2f}", "Acc x 1M HHT", "status-bad" if if_mensual > 10 else "status-good")
    kpi_box(k4, "ACCIDENTES CTP", f"{int(acc)}", "Eventos en el mes")

    st.markdown("---")
    
    # --- SECCIÓN GESTIÓN ---
    st.markdown("### 📋 Gestión Preventiva y Salud (DS 44)")
    g1, g2, g3, g4 = st.columns(4)
    
    def plot_donut(val, title, color):
        fig = go.Figure(go.Pie(
            values=[val, 100-val], 
            labels=['Cumplido', 'Pendiente'],
            hole=0.6,
            marker_colors=[color, '#eee'],
            textinfo='none'
        ))
        fig.update_layout(showlegend=False, height=120, margin=dict(t=0, b=0, l=0, r=0),
            annotations=[dict(text=f"{val:.0f}%", x=0.5, y=0.5, font_size=20, showarrow=False)])
        st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:14px;'>{title}</div>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)

    with g1: plot_donut(cumpl_insp, "Plan Inspecciones", "#1976D2")
    with g2: plot_donut(cumpl_cap, "Plan Capacitación", "#388E3C")
    with g3: plot_donut(cierre_medidas, "Cierre Medidas Correctivas", "#FBC02D")
    with g4: plot_donut(vigilancia_salud, "Vigilancia Salud (MINSAL)", "#8E24AA")

    st.markdown("---")
    
    # --- GRÁFICOS ---
    c_graf1, c_graf2 = st.columns(2)
    with c_graf1:
        st.subheader("Tendencia Anual: Accidentabilidad")
        df_year['Tasa_Acc'] = (df_year['Accidentes CTP'] / df_year['Masa Laboral']) * 100
        fig_line = px.line(df_year, x='Mes', y='Tasa_Acc', markers=True, title="Evolución Tasa Mensual")
        fig_line.update_traces(line_color='#B71C1C', line_width=3)
        fig_line.update_layout(height=300)
        st.plotly_chart(fig_line, use_container_width=True)
        
    with c_graf2:
        st.subheader("Gestión de Salud: Expuestos (PREXOR)")
        fig_bar = px.bar(df_year, x='Mes', y='Expuestos Ruido (PREXOR)', title="Trabajadores en Vigilancia Ruido")
        fig_bar.update_traces(marker_color='#8E24AA')
        fig_bar.update_layout(height=300)
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- PDF DINÁMICO ---
    st.markdown("### 🖨️ Exportar Reporte Mensual")
    
    if st.button("Generar PDF DS 44"):
        class PDF(FPDF):
            def header(self):
                if os.path.exists(logo_path):
                    self.image(logo_path, 10, 8, 33)
                self.set_font('Arial', 'B', 15)
                self.set_xy(50, 10)
                self.cell(0, 10, 'INFORME MENSUAL DE GESTIÓN SST', 0, 1, 'R')
                self.set_font('Arial', '', 10)
                self.set_xy(50, 18)
                self.cell(0, 10, 'CONFORMIDAD NORMATIVA VIGENTE (DS 44)', 0, 1, 'R')
                self.ln(15)
                self.set_draw_color(183, 28, 28)
                self.line(10, 30, 290, 30)

        pdf = PDF(orientation='L', format='A4')
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 12)
        pdf.set_xy(10, 35)
        pdf.cell(0, 10, f"PERIODO: {sel_month.upper()} {sel_year}", 0, 1, 'L')
        
        # Tabla
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font('Arial', 'B', 10)
        headers = ["INDICADOR", "VALOR DEL MES", "UNIDAD", "ESTADO"]
        w_col = [80, 50, 50, 50]
        
        pdf.set_xy(10, 50)
        for i, h in enumerate(headers):
            pdf.cell(w_col[i], 10, h, 1, 0, 'C', 1)
        pdf.ln()
        
        data_rows = [
            ("TASA ACCIDENTABILIDAD", f"{tasa_acc:.2f}", "%", "CRÍTICO" if tasa_acc > 3 else "NORMAL"),
            ("TASA SINIESTRALIDAD", f"{tasa_sin:.2f}", "Días/Trab", "-"),
            ("INDICE FRECUENCIA", f"{if_mensual:.2f}", "IF", "-"),
            ("CUMPLIMIENTO INSP.", f"{cumpl_insp:.0f}", "%", "BAJO" if cumpl_insp < 80 else "OPTIMO"),
            ("CUMPLIMIENTO CAP.", f"{cumpl_cap:.0f}", "%", "BAJO" if cumpl_cap < 80 else "OPTIMO"),
            ("CIERRE MEDIDAS CORR.", f"{cierre_medidas:.0f}", "%", "PENDIENTE" if cierre_medidas < 100 else "CERRADO"),
            ("VIGILANCIA SALUD", f"{vigilancia_salud:.0f}", "%", "ALERTA" if vigilancia_salud < 100 else "OK"),
        ]
        
        pdf.set_font('Arial', '', 10)
        for row in data_rows:
            pdf.cell(w_col[0], 10, row[0], 1, 0, 'L')
            pdf.cell(w_col[1], 10, row[1], 1, 0, 'C')
            pdf.cell(w_col[2], 10, row[2], 1, 0, 'C')
            pdf.cell(w_col[3], 10, row[3], 1, 0, 'C')
            pdf.ln()

        # Insertar Gráfico CON SEGURIDAD (TRY/EXCEPT)
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                fig_line.write_image(tmp.name, width=700, height=300)
                pdf.image(tmp.name, x=20, y=130, w=150)
        except Exception as e:
            pdf.set_xy(20, 130)
            pdf.set_font('Arial', 'I', 10)
            pdf.set_text_color(255, 0, 0)
            pdf.cell(0, 10, f"Nota: Gráfico no disponible en PDF (Falta librería Kaleido en servidor)", 0, 1)

        pdf.set_xy(10, 190)
        pdf.set_font('Arial', 'I', 8)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 5, "Este documento certifica el desempeño del SGSST conforme a los requisitos del DS 44.")
        
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button("📥 Descargar Reporte PDF", pdf_bytes, "Reporte_SGSST.pdf", "application/pdf")

with tab_data:
    st.subheader("📝 Base de Datos Maestra (Editable)")
    config_cols = {
        "Mes": st.column_config.SelectboxColumn("Mes", options=orden_meses, required=True),
        "Cierre Medidas Correctivas (%)": st.column_config.ProgressColumn("Cierre Medidas", min_value=0, max_value=100, format="%f%%"),
        "Vigilancia Salud al Día (%)": st.column_config.ProgressColumn("Vigilancia Salud", min_value=0, max_value=100, format="%f%%"),
    }
    
    edited_df = st.data_editor(st.session_state['df_sgsst'], num_rows="dynamic", column_config=config_cols, use_container_width=True)
    
    if not edited_df.equals(st.session_state['df_sgsst']):
        st.session_state['df_sgsst'] = edited_df
        guardar_cambios(edited_df)
        st.rerun()
