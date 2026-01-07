import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
from fpdf import FPDF

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="SGSST - DS 44", layout="wide", page_icon="🛡️")

# --- 2. GESTIÓN DE DATOS ---
CSV_FILE = "base_datos_ds44.csv"

def get_structure():
    # Estructura alineada al CICLO PHVA del DS 44
    return pd.DataFrame({
        'Año': [2024], 'Mes': ['Enero'],
        # 1. DATOS ESTRUCTURALES
        'Masa Laboral': [100], 'HHT': [18000],
        # 2. REACTIVOS (Resultado)
        'Accidentes CTP': [0], 'Días Perdidos': [0], 'Días Cargo': [0],
        # 3. GESTIÓN OPERATIVA (Verificación)
        'Insp. Programadas': [10], 'Insp. Ejecutadas': [8],
        'Cap. Programadas': [5], 'Cap. Ejecutadas': [5],
        # 4. MEJORA CONTINUA (Acción)
        'Medidas Correctivas Abiertas': [5], 'Medidas Correctivas Cerradas': [4],
        # 5. SALUD OCUPACIONAL (Higiene)
        'Expuestos Silice/Ruido': [10], 'Vigilancia Salud Vigente': [10]
    })

def load_data():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            # Reparación automática de columnas si cambias el formato
            ref = get_structure()
            for col in ref.columns:
                if col not in df.columns: df[col] = 0
            return df
        except: return get_structure()
    return get_structure()

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

if 'df_main' not in st.session_state:
    st.session_state['df_main'] = load_data()

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.title("⚙️ Configuración SGSST")
    # Logo
    uploaded_logo = st.file_uploader("Logo Empresa", type=['png', 'jpg'])
    logo_path = "logo_temp.png"
    if uploaded_logo:
        with open(logo_path, "wb") as f: f.write(uploaded_logo.getbuffer())
    
    st.markdown("---")
    # Reset
    if st.button("♻️ Reiniciar Base de Datos"):
        save_data(get_structure())
        st.rerun()

# --- 4. MOTOR DE REPORTE PDF (NATIVO & DINÁMICO) ---
class PDF_SGSST(FPDF):
    def header(self):
        # Logo Izquierda
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 25)
        # Título y Subtítulo
        self.set_font('Arial', 'B', 14)
        self.set_xy(40, 10)
        self.cell(0, 10, 'INFORME MENSUAL DE DESEMPEÑO SGSST', 0, 1, 'L')
        self.set_font('Arial', 'I', 10)
        self.set_xy(40, 16)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'Cumplimiento Normativo DS 44 (Gestión de Riesgos)', 0, 1, 'L')
        self.set_draw_color(200, 200, 200)
        self.line(10, 28, 285, 28)
        self.ln(15)

    def draw_progress_bar(self, label, percentage, x, y, w):
        """Dibuja una barra de progreso nativa en el PDF"""
        # Etiqueta
        self.set_xy(x, y)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(0, 0, 0)
        self.cell(50, 5, label, 0, 0, 'L')
        
        # Fondo Barra (Gris)
        self.set_fill_color(230, 230, 230)
        self.rect(x, y+6, w, 6, 'F')
        
        # Color según cumplimiento (Dinámico)
        if percentage >= 90: self.set_fill_color(46, 125, 50) # Verde
        elif percentage >= 70: self.set_fill_color(255, 143, 0) # Naranja
        else: self.set_fill_color(198, 40, 40) # Rojo
        
        # Barra Progreso
        fill_w = (percentage / 100) * w
        if fill_w > w: fill_w = w
        self.rect(x, y+6, fill_w, 6, 'F')
        
        # Texto Porcentaje
        self.set_xy(x + w + 2, y+5)
        self.set_font('Arial', '', 9)
        self.cell(15, 6, f"{percentage:.0f}%", 0, 0, 'L')

    def kpi_card(self, title, val, unit, x, y, w):
        self.set_fill_color(250, 250, 250)
        self.set_draw_color(220, 220, 220)
        self.rect(x, y, w, 25, 'DF')
        
        self.set_xy(x, y+2)
        self.set_font('Arial', 'B', 8)
        self.set_text_color(100, 100, 100)
        self.cell(w, 5, title, 0, 1, 'C')
        
        self.set_xy(x, y+8)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 0, 0)
        self.cell(w, 10, str(val), 0, 1, 'C')
        
        self.set_xy(x, y+18)
        self.set_font('Arial', '', 8)
        self.cell(w, 4, unit, 0, 1, 'C')

# --- 5. LÓGICA DE NEGOCIO ---
df = st.session_state['df_main']

# Tabs
tab_dash, tab_editor = st.tabs(["📊 DASHBOARD INTEGRAL", "📝 EDITOR DE DATOS"])

with tab_dash:
    # Header App
    c_logo, c_title = st.columns([1, 5])
    with c_logo:
        if os.path.exists(logo_path): st.image(logo_path, width=100)
    with c_title:
        st.markdown("## SISTEMA DE GESTIÓN SST (DS 44)")
        st.markdown("**Estado del Sistema:** Monitoreo Mensual")

    # Filtros
    col_y, col_m = st.columns(2)
    years = sorted(df['Año'].unique(), reverse=True)
    sel_year = col_y.selectbox("Año", years)
    df_year = df[df['Año'] == sel_year]
    
    months = df_year['Mes'].unique().tolist()
    # Ordenador de meses
    m_order = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    months = sorted(months, key=lambda x: m_order.index(x) if x in m_order else 99)
    sel_month = col_m.selectbox("Mes", months, index=len(months)-1 if months else 0)
    
    # Data Mensual
    df_m = df_year[df_year['Mes'] == sel_month]
    
    if df_m.empty: st.stop()
    
    # Extraer valores
    row = df_m.iloc[0]
    masa = row['Masa Laboral']; hht = row['HHT']
    acc = row['Accidentes CTP']; dp = row['Días Perdidos']
    
    # Cálculos
    tasa_acc = (acc / masa * 100) if masa > 0 else 0
    tasa_sin = (dp / masa * 100) if masa > 0 else 0
    if_men = (acc * 1000000 / hht) if hht > 0 else 0
    
    # Gestión %
    p_insp = (row['Insp. Ejecutadas'] / row['Insp. Programadas'] * 100) if row['Insp. Programadas'] > 0 else 0
    p_cap = (row['Cap. Ejecutadas'] / row['Cap. Programadas'] * 100) if row['Cap. Programadas'] > 0 else 0
    p_medidas = (row['Medidas Correctivas Cerradas'] / row['Medidas Correctivas Abiertas'] * 100) if row['Medidas Correctivas Abiertas'] > 0 else 100
    p_salud = (row['Vigilancia Salud Vigente'] / row['Expuestos Silice/Ruido'] * 100) if row['Expuestos Silice/Ruido'] > 0 else 100

    # --- VISUALIZACIÓN ---
    st.markdown("### 1. Indicadores de Resultado (Accidentabilidad)")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tasa Accidentabilidad", f"{tasa_acc:.2f}%", delta="Meta: <3%", delta_color="inverse")
    k2.metric("Tasa Siniestralidad", f"{tasa_sin:.2f}", "Días/Trab")
    k3.metric("Indice Frecuencia", f"{if_men:.2f}", "Acc x 1M HHT")
    k4.metric("Accidentes CTP", int(acc), "Eventos Reales", delta_color="inverse")
    
    st.markdown("---")
    
    st.markdown("### 2. Indicadores de Gestión (DS 44)")
    g1, g2, g3, g4 = st.columns(4)
    
    def donut(val, title, color):
        fig = go.Figure(go.Pie(values=[val, 100-val], hole=0.7, marker_colors=[color, '#eee'], textinfo='none'))
        fig.update_layout(height=140, margin=dict(t=0,b=0,l=0,r=0), 
                         annotations=[dict(text=f"{val:.0f}%", x=0.5, y=0.5, font_size=24, showarrow=False)])
        st.markdown(f"<div style='text-align:center; font-weight:bold;'>{title}</div>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)

    with g1: donut(p_insp, "Inspecciones", "#29B6F6")
    with g2: donut(p_cap, "Capacitaciones", "#66BB6A")
    with g3: donut(p_medidas, "Cierre Hallazgos", "#FFA726")
    with g4: donut(p_salud, "Salud Ocupacional", "#AB47BC")
    
    st.markdown("---")
    
    # --- BOTÓN PDF ---
    if st.button("📄 Generar PDF Ejecutivo (Dinámico)"):
        pdf = PDF_SGSST(orientation='L', format='A4')
        pdf.add_page()
        
        # Periodo
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"Periodo Reportado: {sel_month.upper()} {sel_year}", 0, 1)
        
        # 1. KPIs Cards (Dibujados nativamente)
        y_kpi = 45
        w_kpi = 60
        pdf.kpi_card("TASA ACCIDENTABILIDAD", f"{tasa_acc:.2f}%", "Meta < 3.0%", 10, y_kpi, w_kpi)
        pdf.kpi_card("TASA SINIESTRALIDAD", f"{tasa_sin:.2f}", "Días / Trab", 10 + w_kpi + 5, y_kpi, w_kpi)
        pdf.kpi_card("INDICE FRECUENCIA", f"{if_men:.2f}", "Acc / 1M HHT", 10 + (w_kpi + 5)*2, y_kpi, w_kpi)
        pdf.kpi_card("ACCIDENTES CTP", int(acc), "Eventos", 10 + (w_kpi + 5)*3, y_kpi, w_kpi)
        
        # 2. Barras de Gestión (Dibujadas nativamente - NO IMAGEN)
        pdf.set_xy(10, 85)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Cumplimiento del Programa de Gestión (DS 44)", 0, 1)
        
        y_bars = 100
        pdf.draw_progress_bar("Plan Inspecciones", p_insp, 10, y_bars, 120)
        pdf.draw_progress_bar("Plan Capacitación", p_cap, 10, y_bars + 15, 120)
        pdf.draw_progress_bar("Cierre Hallazgos", p_medidas, 10, y_bars + 30, 120)
        pdf.draw_progress_bar("Vigilancia Salud", p_salud, 10, y_bars + 45, 120)
        
        # 3. Tabla Resumen (Lado derecho)
        x_table = 160
        y_table = 95
        pdf.set_xy(x_table, y_table)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(50, 50, 50)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 8, "DETALLE OPERATIVO", 0, 1, 'C', 1)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 10)
        def row_tab(label, val):
            pdf.set_x(x_table)
            pdf.cell(70, 8, label, 1)
            pdf.cell(30, 8, str(val), 1, 1, 'C')
            
        row_tab("Masa Laboral Promedio", int(masa))
        row_tab("Horas Hombre (HHT)", int(hht))
        row_tab("Días Perdidos", int(dp))
        row_tab("Insp. Realizadas", int(row['Insp. Ejecutadas']))
        row_tab("Cap. Realizadas", int(row['Cap. Ejecutadas']))
        
        # Footer
        pdf.set_xy(10, 180)
        pdf.set_font('Arial', 'I', 8)
        pdf.multi_cell(0, 5, "Reporte generado conforme a los requisitos de información del Sistema de Gestión de Seguridad y Salud en el Trabajo (DS 44).")

        out = pdf.output(dest='S').encode('latin-1')
        st.download_button("📥 Descargar Reporte PDF", out, "Reporte_SGSST.pdf", "application/pdf")

with tab_editor:
    st.subheader("📝 Ingreso de Datos")
    
    # Configuración de columnas
    cfg = {
        "Mes": st.column_config.SelectboxColumn("Mes", options=m_order, required=True),
        "Masa Laboral": st.column_config.NumberColumn("Masa Laboral", min_value=1),
        "Medidas Correctivas Abiertas": st.column_config.NumberColumn("Hallazgos Totales"),
        "Medidas Correctivas Cerradas": st.column_config.NumberColumn("Hallazgos Cerrados"),
        "Expuestos Silice/Ruido": st.column_config.NumberColumn("Trab. Expuestos"),
        "Vigilancia Salud Vigente": st.column_config.NumberColumn("Exámenes al Día")
    }
    
    edited = st.data_editor(st.session_state['df_main'], num_rows="dynamic", column_config=cfg, use_container_width=True)
    
    if not edited.equals(st.session_state['df_main']):
        st.session_state['df_main'] = edited
        save_data(edited)
        st.rerun()
