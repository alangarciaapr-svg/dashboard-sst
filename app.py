import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
from fpdf import FPDF

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="SGSST - Maderas Galvez", layout="wide", page_icon="🌲")

# --- 2. GESTIÓN DE DATOS ---
CSV_FILE = "base_datos_galvez.csv"

def get_structure():
    return pd.DataFrame({
        'Año': [2026], 'Mes': ['Enero'],
        # DATOS ESTRUCTURALES
        'Masa Laboral': [100], 'HHT': [18000],
        # REACTIVOS
        'Accidentes CTP': [0], 'Días Perdidos': [0], 'Días Cargo': [0],
        # GESTIÓN (DS 44)
        'Insp. Programadas': [10], 'Insp. Ejecutadas': [8],
        'Cap. Programadas': [5], 'Cap. Ejecutadas': [5],
        'Medidas Correctivas Abiertas': [5], 'Medidas Correctivas Cerradas': [4],
        'Expuestos Silice/Ruido': [10], 'Vigilancia Salud Vigente': [10]
    })

def load_data():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            ref = get_structure()
            # Reparar columnas faltantes
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
    st.title("🌲 Configuración")
    uploaded_logo = st.file_uploader("Subir Logo", type=['png', 'jpg'])
    logo_path = "logo_temp.png"
    if uploaded_logo:
        with open(logo_path, "wb") as f: f.write(uploaded_logo.getbuffer())
    
    st.markdown("---")
    if st.button("♻️ Reiniciar Datos"):
        save_data(get_structure())
        st.rerun()

# --- 4. MOTOR PDF CORREGIDO (SIN SUPERPOSICIÓN) ---
class PDF_GALVEZ(FPDF):
    def header(self):
        # 1. LOGO (Izquierda)
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 30) # x, y, ancho
        
        # 2. TEXTOS (Derecha alineados para no chocar con logo)
        self.set_xy(45, 10)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 5, 'SOCIEDAD MADERERA GALVEZ Y DI GENOVA LTDA', 0, 1, 'L')
        
        self.set_xy(45, 16)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(183, 28, 28) # Rojo corporativo
        self.cell(0, 8, 'INFORME MENSUAL DE GESTIÓN SST (DS 44)', 0, 1, 'L')
        
        self.set_xy(45, 24)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'Sistema de Gestión de Seguridad y Salud en el Trabajo', 0, 1, 'L')
        
        # Línea separadora
        self.set_draw_color(200, 200, 200)
        self.line(10, 32, 285, 32)
        self.ln(10) # Espacio seguro después del header

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def kpi_card(self, title, val, unit, x, y, w, h=25):
        """Dibuja una tarjeta KPI con fondo gris claro y borde"""
        self.set_fill_color(248, 249, 250) # Gris muy claro
        self.set_draw_color(200, 200, 200)
        self.rect(x, y, w, h, 'DF')
        
        # Título
        self.set_xy(x, y + 3)
        self.set_font('Arial', 'B', 7)
        self.set_text_color(80, 80, 80)
        self.cell(w, 4, title, 0, 1, 'C')
        
        # Valor
        self.set_xy(x, y + 9)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 0, 0)
        self.cell(w, 8, str(val), 0, 1, 'C')
        
        # Unidad
        self.set_xy(x, y + 18)
        self.set_font('Arial', '', 7)
        self.set_text_color(100, 100, 100)
        self.cell(w, 4, unit, 0, 1, 'C')

    def draw_progress_bar(self, label, percentage, x, y, w_total):
        """Barra de progreso nativa"""
        # Etiqueta
        self.set_xy(x, y)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(0, 0, 0)
        self.cell(60, 5, label, 0, 0, 'L')
        
        # Fondo Barra
        bar_x = x
        bar_y = y + 6
        bar_h = 5
        self.set_fill_color(230, 230, 230)
        self.rect(bar_x, bar_y, w_total, bar_h, 'F')
        
        # Relleno Color
        if percentage >= 90: self.set_fill_color(46, 125, 50) # Verde
        elif percentage >= 70: self.set_fill_color(255, 143, 0) # Naranja
        else: self.set_fill_color(198, 40, 40) # Rojo
        
        fill_w = (percentage / 100) * w_total
        if fill_w > w_total: fill_w = w_total
        self.rect(bar_x, bar_y, fill_w, bar_h, 'F')
        
        # Texto %
        self.set_xy(bar_x + w_total + 2, bar_y - 1)
        self.set_font('Arial', '', 9)
        self.cell(15, 6, f"{percentage:.0f}%", 0, 0, 'L')

# --- 5. LOGICA APP ---
df = st.session_state['df_main']
tab_dash, tab_editor = st.tabs(["📊 DASHBOARD", "📝 EDITOR DE DATOS"])

with tab_dash:
    # Encabezado App
    c1, c2 = st.columns([1, 5])
    with c1:
        if os.path.exists(logo_path): st.image(logo_path, width=120)
    with c2:
        st.title("SOCIEDAD MADERERA GALVEZ Y DI GENOVA LTDA")
        st.markdown("**Sistema de Gestión SST - DS 44**")

    # Filtros
    col_y, col_m = st.columns(2)
    years = sorted(df['Año'].unique(), reverse=True)
    sel_year = col_y.selectbox("Año", years)
    df_year = df[df['Año'] == sel_year]
    
    months = df_year['Mes'].unique().tolist()
    m_order = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    months = sorted(months, key=lambda x: m_order.index(x) if x in m_order else 99)
    sel_month = col_m.selectbox("Mes", months, index=len(months)-1 if months else 0)
    
    # Dataframe Mes
    df_m = df_year[df_year['Mes'] == sel_month]
    if df_m.empty: st.stop()
    row = df_m.iloc[0]

    # Cálculos
    masa = row['Masa Laboral']; hht = row['HHT']
    acc = row['Accidentes CTP']; dp = row['Días Perdidos']
    
    tasa_acc = (acc / masa * 100) if masa > 0 else 0
    tasa_sin = (dp / masa * 100) if masa > 0 else 0
    if_men = (acc * 1000000 / hht) if hht > 0 else 0
    
    # KPIs Gestión
    def safe_div(a, b): return (a/b*100) if b > 0 else 0
    
    p_insp = safe_div(row['Insp. Ejecutadas'], row['Insp. Programadas'])
    p_cap = safe_div(row['Cap. Ejecutadas'], row['Cap. Programadas'])
    # Medidas: Si hay 0 abiertas, asumimos 100% cumplimiento si cerradas >= abiertas, sino 100
    if row['Medidas Correctivas Abiertas'] == 0:
        p_medidas = 100
    else:
        p_medidas = safe_div(row['Medidas Correctivas Cerradas'], row['Medidas Correctivas Abiertas'])
        
    p_salud = safe_div(row['Vigilancia Salud Vigente'], row['Expuestos Silice/Ruido']) if row['Expuestos Silice/Ruido'] > 0 else 100

    # Visualización
    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tasa Accidentabilidad", f"{tasa_acc:.2f}%", "Meta < 3%")
    k2.metric("Tasa Siniestralidad", f"{tasa_sin:.2f}", "Días/Trab")
    k3.metric("Indice Frecuencia", f"{if_men:.2f}", "Acc/1M HHT")
    k4.metric("Accidentes CTP", int(acc), "Eventos")
    
    st.markdown("### Gestión Preventiva")
    g1, g2, g3, g4 = st.columns(4)
    
    def donut(val, title):
        fig = go.Figure(go.Pie(values=[val, 100-val], hole=0.7, marker_colors=['#1976D2', '#eee'], textinfo='none'))
        fig.update_layout(height=120, margin=dict(t=0,b=0,l=0,r=0), 
                         annotations=[dict(text=f"{val:.0f}%", x=0.5, y=0.5, font_size=20, showarrow=False)])
        st.markdown(f"<div style='text-align:center; font-size:14px;'>{title}</div>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)

    with g1: donut(p_insp, "Inspecciones")
    with g2: donut(p_cap, "Capacitaciones")
    with g3: donut(p_medidas, "Cierre Medidas")
    with g4: donut(p_salud, "Salud Ocup.")

    # --- GENERAR PDF ---
    st.markdown("---")
    if st.button("📄 Descargar PDF Oficial"):
        pdf = PDF_GALVEZ(orientation='L', format='A4')
        pdf.add_page()
        
        # 1. Info Periodo (Coordenada Y segura: 40)
        pdf.set_xy(10, 40)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 10, f"PERIODO REPORTADO: {sel_month.upper()} {sel_year}", 0, 1)
        
        # 2. KPIs Cards (Coordenada Y segura: 55)
        y_kpi = 55
        w_kpi = 65 # Más ancho para que quepa bien
        gap = 5
        pdf.kpi_card("TASA ACCIDENTABILIDAD", f"{tasa_acc:.2f}%", "Meta < 3.0%", 10, y_kpi, w_kpi)
        pdf.kpi_card("TASA SINIESTRALIDAD", f"{tasa_sin:.2f}", "Días Perdidos / Masa Laboral", 10 + w_kpi + gap, y_kpi, w_kpi)
        pdf.kpi_card("INDICE FRECUENCIA", f"{if_men:.2f}", "Acc. CTP x 1.000.000 / HHT", 10 + (w_kpi + gap)*2, y_kpi, w_kpi)
        pdf.kpi_card("ACCIDENTES CTP", int(acc), "Nº Eventos", 10 + (w_kpi + gap)*3, y_kpi, w_kpi)
        
        # 3. Barras de Gestión (Coordenada Y segura: 95)
        y_bars = 95
        pdf.set_xy(10, y_bars)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Cumplimiento Programa de Gestión (DS 44)", 0, 1)
        
        y_start_bars = y_bars + 15
        pdf.draw_progress_bar("Plan Inspecciones", p_insp, 10, y_start_bars, 100)
        pdf.draw_progress_bar("Plan Capacitaciones", p_cap, 10, y_start_bars + 15, 100)
        pdf.draw_progress_bar("Cierre Medidas Corr.", p_medidas, 10, y_start_bars + 30, 100)
        pdf.draw_progress_bar("Vigilancia Salud (Prexor)", p_salud, 10, y_start_bars + 45, 100)
        
        # 4. Tabla Detalle (Lado derecho de las barras - Coordenada X: 140)
        x_tab = 140
        y_tab = y_start_bars
        
        pdf.set_xy(x_tab, y_tab - 6)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(60, 6, "DETALLE OPERATIVO", 0, 1, 'L')
        
        pdf.set_font('Arial', '', 9)
        def add_row(label, val, y_pos):
            pdf.set_xy(x_tab, y_pos)
            pdf.cell(80, 7, label, 1)
            pdf.cell(30, 7, str(val), 1, 1, 'C')
        
        add_row("Masa Laboral", int(masa), y_tab)
        add_row("Horas Hombre (HHT)", int(hht), y_tab + 7)
        add_row("Días Perdidos", int(dp), y_tab + 14)
        add_row("Insp. Realizadas", int(row['Insp. Ejecutadas']), y_tab + 21)
        add_row("Cap. Realizadas", int(row['Cap. Ejecutadas']), y_tab + 28)
        add_row("Hallazgos Cerrados", int(row['Medidas Correctivas Cerradas']), y_tab + 35)

        # Generar
        out = pdf.output(dest='S').encode('latin-1')
        st.download_button("📥 Descargar PDF Corregido", out, f"Reporte_Galvez_{sel_month}.pdf", "application/pdf")

with tab_editor:
    st.subheader("📝 Editor de Datos")
    st.info("Ingresa los datos del mes. Guarda automáticamente.")
    
    cfg = {
        "Mes": st.column_config.SelectboxColumn("Mes", options=m_order, required=True),
        "Masa Laboral": st.column_config.NumberColumn("Masa Laboral", min_value=1),
        "Cierre Medidas Correctivas (%)": None, # Ocultar columna vieja si existe
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
