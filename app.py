import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
from fpdf import FPDF

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SST - Maderas Galvez", layout="wide", page_icon="🌲")

# --- 2. GESTIÓN DE DATOS ---
CSV_FILE = "base_datos_galvez_final.csv"

def get_structure():
    return pd.DataFrame({
        'Año': [2026], 
        'Mes': ['Enero'],
        # DATOS BASE
        'Masa Laboral': [100.0], 
        'Horas Extras': [0.0],
        'Horas Ausentismo': [0.0],
        'Accidentes CTP': [0.0], 
        'Días Perdidos': [0.0], 
        'Días Cargo': [0.0],
        # GESTIÓN DEPARTAMENTO SST
        'Insp. Programadas': [10.0], 'Insp. Ejecutadas': [8.0],
        'Cap. Programadas': [5.0], 'Cap. Ejecutadas': [5.0],
        'Medidas Abiertas': [5.0], 'Medidas Cerradas': [4.0],
        'Expuestos Silice/Ruido': [10.0], 'Vig. Salud Vigente': [10.0],
        # CALCULADOS (Placeholders)
        'HHT': [18000.0],
        'Tasa Acc.': [0.0], 'Tasa Sin.': [0.0],
        'Indice Frec.': [0.0], 'Indice Grav.': [0.0]
    })

def limpiar_y_calcular(df):
    """Realiza cálculos mensuales automáticos"""
    cols_num = df.columns.drop(['Año', 'Mes'])
    for col in cols_num:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 1. HHT Mensual (Base 180)
    df['HHT'] = (df['Masa Laboral'] * 180) + df['Horas Extras'] - df['Horas Ausentismo']
    df['HHT'] = df['HHT'].apply(lambda x: x if x > 0 else 1)
    
    masa_segura = df['Masa Laboral'].apply(lambda x: x if x > 0 else 1)
    
    # 2. Índices Mensuales
    df['Tasa Acc.'] = (df['Accidentes CTP'] / masa_segura) * 100
    df['Tasa Sin.'] = (df['Días Perdidos'] / masa_segura) * 100
    df['Indice Frec.'] = (df['Accidentes CTP'] * 1000000) / df['HHT']
    df['Indice Grav.'] = ((df['Días Perdidos'] + df['Días Cargo']) * 1000000) / df['HHT']
    
    return df

def load_data():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            ref = get_structure()
            for col in ref.columns:
                if col not in df.columns: df[col] = 0
            return limpiar_y_calcular(df)
        except: return get_structure()
    return get_structure()

def save_data(df):
    df_calc = limpiar_y_calcular(df)
    df_calc.to_csv(CSV_FILE, index=False)
    return df_calc

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
    st.success("Sistema configurado según DS 67 y DS 44.")
    if st.button("♻️ Reiniciar Base de Datos"):
        save_data(get_structure())
        st.rerun()

# --- 4. MOTOR PDF PROFESIONAL ---
class PDF_SST(FPDF):
    def header(self):
        # 1. LOGO GRANDE (Izquierda)
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 40) # Ancho 40mm (Grande)
        
        # 2. TÍTULOS (Alineados para no chocar con el logo grande)
        self.set_xy(55, 12)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 6, 'SOCIEDAD MADERERA GALVEZ Y DI GENOVA LTDA', 0, 1, 'L')
        
        self.set_xy(55, 19)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, 'SISTEMA DE GESTIÓN EN SST DS44', 0, 1, 'L')
        
        self.set_xy(55, 25)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(150, 150, 150)
        self.cell(0, 6, 'Informe de Indicadores Mensuales y Acumulados (DS 67)', 0, 1, 'L')
        
        # Línea divisoria
        self.set_draw_color(183, 28, 28) # Rojo
        self.set_line_width(0.5)
        self.line(10, 35, 285, 35)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Depto. Prevención de Riesgos - Pagina {self.page_no()}', 0, 0, 'C')

    def kpi_comparison_box(self, title, val_acum, val_mes, unit, x, y, w, h=35):
        """Caja que muestra Acumulado vs Mensual lado a lado"""
        # Fondo y Borde
        self.set_draw_color(200, 200, 200)
        self.set_fill_color(252, 252, 252)
        self.set_line_width(0.2)
        self.rect(x, y, w, h, 'DF')
        
        # Título Caja
        self.set_xy(x, y)
        self.set_font('Arial', 'B', 8)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(50, 50, 50) # Encabezado Gris Oscuro
        self.cell(w, 6, title, 1, 1, 'C', 1)
        
        # Mitad Izquierda (Acumulado - Destacado)
        w_half = w / 2
        self.set_xy(x, y + 6)
        self.set_font('Arial', 'B', 7)
        self.set_text_color(183, 28, 28) # Rojo
        self.cell(w_half, 5, "ACUMULADO", 0, 1, 'C')
        
        self.set_xy(x, y + 11)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 0, 0)
        self.cell(w_half, 8, str(val_acum), 0, 1, 'C')
        
        # Mitad Derecha (Mensual)
        self.set_xy(x + w_half, y + 6)
        self.set_font('Arial', 'B', 7)
        self.set_text_color(100, 100, 100)
        self.cell(w_half, 5, "DEL MES", 0, 1, 'C')
        
        self.set_xy(x + w_half, y + 11)
        self.set_font('Arial', '', 12)
        self.set_text_color(80, 80, 80)
        self.cell(w_half, 8, str(val_mes), 0, 1, 'C')
        
        # Unidad (Abajo, centrada)
        self.set_xy(x, y + 22)
        self.set_font('Arial', 'I', 7)
        self.set_text_color(150, 150, 150)
        self.cell(w, 5, f"Unidad: {unit}", 0, 1, 'C')

    def draw_management_bar(self, label, percentage, x, y, w_total):
        # Texto Label
        self.set_xy(x, y)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(0, 0, 0)
        self.cell(60, 5, label, 0, 0, 'L')
        
        # Coordenadas Barra
        bx, by = x, y + 6
        bh = 5
        
        # Fondo
        self.set_fill_color(230, 230, 230)
        self.rect(bx, by, w_total, bh, 'F')
        
        # Color Semáforo
        if percentage >= 90: self.set_fill_color(46, 125, 50)
        elif percentage >= 70: self.set_fill_color(255, 143, 0)
        else: self.set_fill_color(198, 40, 40)
        
        # Relleno
        fill = (percentage / 100) * w_total
        if fill > w_total: fill = w_total
        if fill < 0: fill = 0
        self.rect(bx, by, fill, bh, 'F')
        
        # Valor Texto
        self.set_xy(bx + w_total + 2, by - 1)
        self.set_font('Arial', '', 9)
        self.cell(15, 6, f"{percentage:.0f}%", 0, 0, 'L')

# --- 5. LÓGICA DE NEGOCIO ---
df = st.session_state['df_main']
tab_dash, tab_editor = st.tabs(["📊 DASHBOARD SST", "📝 EDITOR DE DATOS"])

with tab_dash:
    # Encabezado App
    c_head1, c_head2 = st.columns([1, 4])
    with c_head1:
        if os.path.exists(logo_path): st.image(logo_path, width=150)
    with c_head2:
        st.title("SOCIEDAD MADERERA GALVEZ Y DI GENOVA LTDA")
        st.subheader("SISTEMA DE GESTION EN SST DS44")

    # Filtros de Tiempo
    col_y, col_m = st.columns(2)
    years = sorted(df['Año'].unique(), reverse=True)
    sel_year = col_y.selectbox("Año Fiscal", years)
    
    # Preparar datos del año
    df_year = df[df['Año'] == sel_year].copy()
    m_order = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    df_year['Mes_Idx'] = df_year['Mes'].apply(lambda x: m_order.index(x) if x in m_order else 99)
    df_year = df_year.sort_values('Mes_Idx')
    
    # Selector Mes de Corte
    months = df_year['Mes'].tolist()
    sel_month = col_m.selectbox("Mes de Cierre (Acumulado)", months, index=len(months)-1 if months else 0)
    
    # --- CÁLCULOS DS 67 (ACUMULADOS) ---
    idx_corte = m_order.index(sel_month)
    df_acum = df_year[df_year['Mes_Idx'] <= idx_corte] # Enero hasta mes seleccionado
    
    # 1. Sumas acumuladas
    sum_acc = df_acum['Accidentes CTP'].sum()
    sum_dias = df_acum['Días Perdidos'].sum()
    sum_hht = df_acum['HHT'].sum()
    avg_masa = df_acum['Masa Laboral'].mean() # El DS67 usa el promedio de masa del periodo
    
    # 2. Tasas Acumuladas
    ta_acum = (sum_acc / avg_masa * 100) if avg_masa > 0 else 0
    ts_acum = (sum_dias / avg_masa * 100) if avg_masa > 0 else 0
    if_acum = (sum_acc * 1000000 / sum_hht) if sum_hht > 0 else 0
    
    # 3. Datos del Mes Aislado
    row_mes = df_year[df_year['Mes'] == sel_month].iloc[0]
    
    # Gestión Depto SST
    def safe_div(a, b): return (a/b*100) if b > 0 else 0
    
    p_insp = safe_div(row_mes['Insp. Ejecutadas'], row_mes['Insp. Programadas'])
    p_cap = safe_div(row_mes['Cap. Ejecutadas'], row_mes['Cap. Programadas'])
    p_medidas = safe_div(row_mes['Medidas Cerradas'], row_mes['Medidas Abiertas']) if row_mes['Medidas Abiertas'] > 0 else 100
    p_salud = safe_div(row_mes['Vig. Salud Vigente'], row_mes['Expuestos Silice/Ruido']) if row_mes['Expuestos Silice/Ruido'] > 0 else 100

    # --- VISUALIZACIÓN DASHBOARD ---
    st.markdown("---")
    st.markdown(f"### 📈 Indicadores DS67 (Periodo: Enero - {sel_month})")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tasa Accidentabilidad (Acum)", f"{ta_acum:.2f}%", f"Mes: {row_mes['Tasa Acc.']:.2f}%", delta_color="inverse")
    k2.metric("Tasa Siniestralidad (Acum)", f"{ts_acum:.2f}", f"Mes: {row_mes['Tasa Sin.']:.2f}", delta_color="inverse")
    k3.metric("Indice Frecuencia (Acum)", f"{if_acum:.2f}", f"Mes: {row_mes['Indice Frec.']:.2f}", delta_color="inverse")
    k4.metric("HHT Totales (Acum)", f"{int(sum_hht)}", f"Mes: {int(row_mes['HHT'])}")
    
    st.markdown("### 📋 Gestión Depto SST")
    g1, g2, g3, g4 = st.columns(4)
    
    def chart_donut(val, title):
        fig = go.Figure(go.Pie(values=[val, 100-val], hole=0.7, marker_colors=['#1565C0', '#eeeeee'], textinfo='none'))
        fig.update_layout(height=120, margin=dict(t=0,b=0,l=0,r=0),
                         annotations=[dict(text=f"{val:.0f}%", x=0.5, y=0.5, font_size=20, showarrow=False)])
        st.markdown(f"<div style='text-align:center;'>{title}</div>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, key=title)

    with g1: chart_donut(p_insp, "Inspecciones")
    with g2: chart_donut(p_cap, "Capacitaciones")
    with g3: chart_donut(p_medidas, "Cierre Hallazgos")
    with g4: chart_donut(p_salud, "Salud Ocupacional")

    # --- GENERAR PDF ---
    st.markdown("---")
    if st.button("📄 Descargar PDF Profesional"):
        pdf = PDF_SST(orientation='L', format='A4')
        pdf.add_page()
        
        # Info Periodo
        pdf.set_xy(10, 40)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 10, f"PERIODO EVALUADO: ENERO A {sel_month.upper()} {sel_year}", 0, 1)
        
        # 1. KPIs DS 67 (Cajas comparativas)
        y_kpi = 55; w_kpi = 65; gap = 5
        
        # Fila 1 de KPIs
        pdf.kpi_comparison_box("TASA ACCIDENTABILIDAD", f"{ta_acum:.2f}%", f"{row_mes['Tasa Acc.']:.2f}%", "%", 10, y_kpi, w_kpi)
        pdf.kpi_comparison_box("TASA SINIESTRALIDAD", f"{ts_acum:.2f}", f"{row_mes['Tasa Sin.']:.2f}", "Dias/Trab", 10+w_kpi+gap, y_kpi, w_kpi)
        pdf.kpi_comparison_box("INDICE FRECUENCIA", f"{if_acum:.2f}", f"{row_mes['Indice Frec.']:.2f}", "Acc/1M HHT", 10+(w_kpi+gap)*2, y_kpi, w_kpi)
        pdf.kpi_comparison_box("HHT / MASA LABORAL", f"{int(sum_hht)}", f"{avg_masa:.1f}", "HHT Totales / Prom. Trab", 10+(w_kpi+gap)*3, y_kpi, w_kpi)
        
        # 2. Gestión SST (Barras)
        y_gest = 105
        pdf.set_xy(10, y_gest)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"Indicadores de Gestión Depto. SST ({sel_month})", 0, 1)
        
        y_bar_start = y_gest + 15
        pdf.draw_management_bar("Cumplimiento Inspecciones", p_insp, 10, y_bar_start, 110)
        pdf.draw_management_bar("Cumplimiento Capacitaciones", p_cap, 10, y_bar_start+15, 110)
        pdf.draw_management_bar("Eficacia Cierre Hallazgos", p_medidas, 10, y_bar_start+30, 110)
        pdf.draw_management_bar("Cobertura Vigilancia Salud", p_salud, 10, y_bar_start+45, 110)
        
        # 3. Tabla Detalle (Derecha)
        x_tab = 150
        y_tab = y_bar_start - 5
        pdf.set_xy(x_tab, y_tab)
        pdf.set_fill_color(50, 50, 50); pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(100, 8, "RESUMEN OPERATIVO ACUMULADO", 0, 1, 'C', 1)
        
        pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 9)
        def add_row(label, val, y):
            pdf.set_xy(x_tab, y)
            pdf.cell(70, 7, label, 1)
            pdf.cell(30, 7, str(val), 1, 1, 'C')
        
        add_row("Total Accidentes CTP", int(sum_acc), y_tab+8)
        add_row("Total Días Perdidos", int(sum_dias), y_tab+15)
        add_row("Masa Laboral Promedio", f"{avg_masa:.1f}", y_tab+22)
        add_row("Medidas Correctivas Totales", int(row_mes['Medidas Abiertas']), y_tab+29)
        add_row("Trabajadores Expuestos (Ruido/Silice)", int(row_mes['Expuestos Silice/Ruido']), y_tab+36)
        
        out = pdf.output(dest='S').encode('latin-1')
        st.download_button("📥 Descargar Reporte Profesional", out, f"Reporte_SST_{sel_month}.pdf", "application/pdf")

with tab_editor:
    st.subheader("📝 Editor Mensual")
    st.info("Ingresa los datos del mes. El sistema calcula HHT, Índices Mensuales y Acumulados.")
    
    cfg = {
        "Mes": st.column_config.SelectboxColumn("Mes", options=m_order, required=True),
        "Masa Laboral": st.column_config.NumberColumn("Trabajadores Promedio", min_value=1),
        "Accidentes CTP": st.column_config.NumberColumn("Accidentes CTP", min_value=0),
        "Días Perdidos": st.column_config.NumberColumn("Días Perdidos", min_value=0),
        
        # Bloqueados
        "HHT": st.column_config.NumberColumn("HHT (Auto)", disabled=True),
        "Tasa Acc.": st.column_config.NumberColumn("TA Mes", disabled=True, format="%.2f%%"),
        "Tasa Sin.": st.column_config.NumberColumn("TS Mes", disabled=True, format="%.2f"),
        
        "Medidas Abiertas": st.column_config.NumberColumn("Hallazgos"),
        "Medidas Cerradas": st.column_config.NumberColumn("Cerrados"),
    }
    
    edited = st.data_editor(st.session_state['df_main'], num_rows="dynamic", column_config=cfg, use_container_width=True)
    
    if not edited.equals(st.session_state['df_main']):
        st.session_state['df_main'] = save_data(edited)
        st.rerun()
