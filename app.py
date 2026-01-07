import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
from fpdf import FPDF

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="SST - Maderas Galvez", layout="wide", page_icon="🌲")

# --- 2. GESTIÓN DE DATOS ---
CSV_FILE = "base_datos_galvez_v3.csv"

def get_structure():
    return pd.DataFrame({
        'Año': [2026], 'Mes': ['Enero'],
        # DATOS BASE
        'Masa Laboral': [100.0], 'Horas Extras': [0.0], 'Horas Ausentismo': [0.0],
        'Accidentes CTP': [0.0], 'Días Perdidos': [0.0], 'Días Cargo': [0.0],
        # GESTIÓN
        'Insp. Programadas': [10.0], 'Insp. Ejecutadas': [8.0],
        'Cap. Programadas': [5.0], 'Cap. Ejecutadas': [5.0],
        'Medidas Abiertas': [5.0], 'Medidas Cerradas': [4.0],
        'Expuestos Silice/Ruido': [10.0], 'Vig. Salud Vigente': [10.0],
        # CALCULADOS
        'HHT': [18000.0], 'Tasa Acc.': [0.0], 'Tasa Sin.': [0.0],
        'Indice Frec.': [0.0], 'Indice Grav.': [0.0]
    })

def procesar_datos(df):
    # Asegurar tipos numéricos
    cols_num = df.columns.drop(['Año', 'Mes'])
    for col in cols_num:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 1. HHT Mensual (Base 180)
    df['HHT'] = (df['Masa Laboral'] * 180) + df['Horas Extras'] - df['Horas Ausentismo']
    df['HHT'] = df['HHT'].apply(lambda x: x if x > 0 else 1)
    masa = df['Masa Laboral'].apply(lambda x: x if x > 0 else 1)
    
    # 2. Índices Mensuales
    df['Tasa Acc.'] = (df['Accidentes CTP'] / masa) * 100
    df['Tasa Sin.'] = (df['Días Perdidos'] / masa) * 100
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
            return procesar_datos(df)
        except: return get_structure()
    return get_structure()

def save_data(df):
    df_calc = procesar_datos(df)
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
    if st.button("♻️ Reiniciar Base de Datos"):
        save_data(get_structure())
        st.rerun()

# --- 4. MOTOR PDF PROFESIONAL ---
class PDF_SST(FPDF):
    def header(self):
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 40)
        
        self.set_xy(55, 12)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 6, 'SOCIEDAD MADERERA GALVEZ Y DI GENOVA LTDA', 0, 1, 'L')
        
        self.set_xy(55, 19)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, 'SISTEMA DE GESTIÓN EN SST DS44', 0, 1, 'L')
        
        self.set_draw_color(183, 28, 28)
        self.set_line_width(0.5)
        self.line(10, 32, 285, 32)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def section_title(self, title, fill_color=(240, 240, 240)):
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(*fill_color)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, title, 1, 1, 'L', 1)
        self.ln(2)

    def kpi_row(self, label, val_mes, val_acum, unit):
        self.set_font('Arial', '', 10)
        self.cell(70, 8, label, 1)
        self.set_font('Arial', 'B', 10)
        self.cell(40, 8, f"{val_mes}", 1, 0, 'C')
        self.set_text_color(183, 28, 28) # Rojo para acumulado
        self.cell(40, 8, f"{val_acum}", 1, 0, 'C')
        self.set_text_color(0, 0, 0)
        self.set_font('Arial', 'I', 9)
        self.cell(40, 8, unit, 1, 1, 'C')

# --- 5. DASHBOARD ---
df = st.session_state['df_main']
tab_dash, tab_editor = st.tabs(["📊 DASHBOARD INTEGRAL", "📝 EDITOR DATOS"])

with tab_dash:
    # Encabezado
    c1, c2 = st.columns([1, 4])
    with c1:
        if os.path.exists(logo_path): st.image(logo_path, width=160)
    with c2:
        st.title("SOCIEDAD MADERERA GALVEZ Y DI GENOVA LTDA")
        st.markdown("### SISTEMA DE GESTIÓN EN SST DS44")

    # Filtros
    col_y, col_m = st.columns(2)
    years = sorted(df['Año'].unique(), reverse=True)
    sel_year = col_y.selectbox("Año Fiscal", years)
    
    # Preparar Datos
    df_year = df[df['Año'] == sel_year].copy()
    m_order = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    df_year['Mes_Idx'] = df_year['Mes'].apply(lambda x: m_order.index(x) if x in m_order else 99)
    df_year = df_year.sort_values('Mes_Idx')
    
    months = df_year['Mes'].tolist()
    sel_month = col_m.selectbox("Mes de Cierre", months, index=len(months)-1 if months else 0)
    
    # --- CÁLCULOS ---
    # 1. Mensuales (Del mes seleccionado)
    row_mes = df_year[df_year['Mes'] == sel_month].iloc[0]
    
    # 2. Acumulados (Enero - Mes Seleccionado)
    idx_corte = m_order.index(sel_month)
    df_acum = df_year[df_year['Mes_Idx'] <= idx_corte]
    
    sum_acc = df_acum['Accidentes CTP'].sum()
    sum_dias = df_acum['Días Perdidos'].sum()
    sum_hht = df_acum['HHT'].sum()
    avg_masa = df_acum['Masa Laboral'].mean()
    
    ta_acum = (sum_acc / avg_masa * 100) if avg_masa > 0 else 0
    ts_acum = (sum_dias / avg_masa * 100) if avg_masa > 0 else 0
    if_acum = (sum_acc * 1000000 / sum_hht) if sum_hht > 0 else 0
    ig_acum = ((sum_dias + df_acum['Días Cargo'].sum()) * 1000000 / sum_hht) if sum_hht > 0 else 0
    
    # Gestión
    def safe_div(a, b): return (a/b*100) if b > 0 else 0
    p_insp = safe_div(row_mes['Insp. Ejecutadas'], row_mes['Insp. Programadas'])
    p_cap = safe_div(row_mes['Cap. Ejecutadas'], row_mes['Cap. Programadas'])
    p_medidas = safe_div(row_mes['Medidas Cerradas'], row_mes['Medidas Abiertas']) if row_mes['Medidas Abiertas']>0 else 100
    p_salud = safe_div(row_mes['Vig. Salud Vigente'], row_mes['Expuestos Silice/Ruido']) if row_mes['Expuestos Silice/Ruido']>0 else 100

    # --- VISUALIZACIÓN ---
    
    # SECCIÓN 1: MENSUALES
    st.markdown("---")
    st.markdown(f"#### 🔵 INDICADORES DEL MES ({sel_month})")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tasa Accidentabilidad", f"{row_mes['Tasa Acc.']:.2f}%")
    k2.metric("Tasa Siniestralidad", f"{row_mes['Tasa Sin.']:.2f}")
    k3.metric("Indice Frecuencia", f"{row_mes['Indice Frec.']:.2f}")
    k4.metric("Indice Gravedad", f"{row_mes['Indice Grav.']:.0f}")

    # SECCIÓN 2: ACUMULADOS
    st.markdown(f"#### 🔴 ACUMULADO DS67 (Enero - {sel_month})")
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("T. Acc. Acumulada", f"{ta_acum:.2f}%", delta="Legal DS67", delta_color="off")
    a2.metric("T. Sin. Acumulada", f"{ts_acum:.2f}", delta="Legal DS67", delta_color="off")
    a3.metric("I. Frec. Acumulado", f"{if_acum:.2f}")
    a4.metric("I. Grav. Acumulado", f"{ig_acum:.0f}")
    
    # SECCIÓN 3: GRÁFICO TENDENCIA
    st.markdown("---")
    st.markdown("#### 📊 Evolución Mensual")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_year['Mes'], y=df_year['Accidentes CTP'], name='Nº Accidentes', marker_color='#90CAF9'))
    fig.add_trace(go.Scatter(x=df_year['Mes'], y=df_year['Tasa Acc.'], name='Tasa Accidentabilidad', yaxis='y2', line=dict(color='#B71C1C', width=3)))
    fig.update_layout(height=300, yaxis2=dict(overlaying='y', side='right', title='Tasa %'))
    st.plotly_chart(fig, use_container_width=True)

    # SECCIÓN 4: GESTIÓN
    st.markdown("#### 📋 Gestión Depto SST (Mes Actual)")
    g1, g2, g3, g4 = st.columns(4)
    def donut(val, title, color):
        fig = go.Figure(go.Pie(values=[val, 100-val], hole=0.7, marker_colors=[color, '#eee'], textinfo='none'))
        fig.update_layout(height=120, margin=dict(t=0,b=0,l=0,r=0), annotations=[dict(text=f"{val:.0f}%", x=0.5, y=0.5, font_size=16, showarrow=False)])
        st.markdown(f"<div style='text-align:center; font-size:13px;'>{title}</div>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, key=title)

    with g1: donut(p_insp, "Plan Inspecciones", "#42A5F5")
    with g2: donut(p_cap, "Plan Capacitaciones", "#66BB6A")
    with g3: donut(p_medidas, "Cierre Hallazgos", "#FFA726")
    with g4: donut(p_salud, "Salud Ocupacional", "#AB47BC")

    # --- PDF ---
    st.markdown("---")
    if st.button("📄 Generar Reporte Completo PDF"):
        pdf = PDF_SST(orientation='P', format='A4') # Vertical para mejor tabla
        pdf.add_page()
        
        # Título Reporte
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"PERIODO DE EVALUACIÓN: {sel_month.upper()} {sel_year}", 0, 1, 'L')
        pdf.ln(5)
        
        # 1. TABLA COMPARATIVA MENSUAL VS ACUMULADO
        pdf.section_title("1. INDICADORES DE RESULTADO (COMPARATIVO)")
        
        # Cabecera Tabla
        pdf.set_fill_color(220, 220, 220)
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(70, 8, "INDICADOR", 1, 0, 'C', 1)
        pdf.cell(40, 8, "MES ACTUAL", 1, 0, 'C', 1)
        pdf.cell(40, 8, "ACUMULADO DS67", 1, 0, 'C', 1)
        pdf.cell(40, 8, "UNIDAD", 1, 1, 'C', 1)
        
        # Filas
        pdf.kpi_row("Tasa Accidentabilidad", f"{row_mes['Tasa Acc.']:.2f}", f"{ta_acum:.2f}", "%")
        pdf.kpi_row("Tasa Siniestralidad", f"{row_mes['Tasa Sin.']:.2f}", f"{ts_acum:.2f}", "Dias/Trab")
        pdf.kpi_row("Indice Frecuencia", f"{row_mes['Indice Frec.']:.2f}", f"{if_acum:.2f}", "Acc/1M HHT")
        pdf.kpi_row("Indice Gravedad", f"{row_mes['Indice Grav.']:.0f}", f"{ig_acum:.0f}", "Dias/1M HHT")
        pdf.kpi_row("Total Accidentes CTP", int(row_mes['Accidentes CTP']), int(sum_acc), "N Eventos")
        pdf.kpi_row("Total Días Perdidos", int(row_mes['Días Perdidos']), int(sum_dias), "Dias")
        pdf.ln(10)
        
        # 2. GESTIÓN
        pdf.section_title("2. GESTIÓN OPERATIVA SST (MES ACTUAL)")
        pdf.set_font('Arial', '', 10)
        
        data_gest = [
            ("Cumplimiento Inspecciones", p_insp),
            ("Cumplimiento Capacitaciones", p_cap),
            ("Eficacia Cierre Hallazgos", p_medidas),
            ("Cobertura Vigilancia Salud", p_salud)
        ]
        
        for label, val in data_gest:
            pdf.cell(80, 8, label, 0)
            
            # Barra
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.set_fill_color(230, 230, 230)
            pdf.rect(x, y+2, 80, 4, 'F')
            
            if val >= 90: pdf.set_fill_color(76, 175, 80)
            elif val >= 70: pdf.set_fill_color(255, 152, 0)
            else: pdf.set_fill_color(244, 67, 54)
            
            w_fill = (val/100)*80
            pdf.rect(x, y+2, w_fill, 4, 'F')
            
            pdf.set_x(x + 85)
            pdf.cell(20, 8, f"{val:.0f}%", 0, 1)

        # 3. ESTADÍSTICA DETALLADA (TABLA MES A MES)
        pdf.ln(10)
        pdf.section_title("3. EVOLUCIÓN HISTÓRICA DEL PERIODO")
        
        pdf.set_font('Arial', 'B', 8)
        pdf.set_fill_color(50, 50, 50); pdf.set_text_color(255, 255, 255)
        pdf.cell(25, 6, "MES", 1, 0, 'C', 1)
        pdf.cell(25, 6, "HHT", 1, 0, 'C', 1)
        pdf.cell(20, 6, "ACC", 1, 0, 'C', 1)
        pdf.cell(20, 6, "DIAS", 1, 0, 'C', 1)
        pdf.cell(25, 6, "T. ACC", 1, 0, 'C', 1)
        pdf.cell(25, 6, "I. FREC", 1, 0, 'C', 1)
        pdf.cell(25, 6, "I. GRAV", 1, 1, 'C', 1)
        
        pdf.set_text_color(0, 0, 0); pdf.set_font('Arial', '', 8)
        
        # Iterar solo hasta el mes seleccionado
        for index, r in df_acum.iterrows():
            pdf.cell(25, 6, r['Mes'], 1, 0)
            pdf.cell(25, 6, f"{int(r['HHT'])}", 1, 0, 'C')
            pdf.cell(20, 6, f"{int(r['Accidentes CTP'])}", 1, 0, 'C')
            pdf.cell(20, 6, f"{int(r['Días Perdidos'])}", 1, 0, 'C')
            pdf.cell(25, 6, f"{r['Tasa Acc.']:.2f}", 1, 0, 'C')
            pdf.cell(25, 6, f"{r['Indice Frec.']:.2f}", 1, 0, 'C')
            pdf.cell(25, 6, f"{r['Indice Grav.']:.0f}", 1, 1, 'C')

        out = pdf.output(dest='S').encode('latin-1')
        st.download_button("📥 Descargar Informe Profesional", out, f"Reporte_SST_{sel_month}.pdf", "application/pdf")

with tab_editor:
    st.subheader("📝 Carga de Datos Mensual")
    st.info("Ingresa los datos. El sistema calcula HHT e Índices automáticamente.")
    
    cfg = {
        "Mes": st.column_config.SelectboxColumn("Mes", options=m_order, required=True),
        "Masa Laboral": st.column_config.NumberColumn("Trabajadores", min_value=1),
        "Horas Extras": st.column_config.NumberColumn("H. Extras", min_value=0),
        "Horas Ausentismo": st.column_config.NumberColumn("H. Ausentismo", min_value=0),
        "Accidentes CTP": st.column_config.NumberColumn("Accidentes CTP", min_value=0),
        "Días Perdidos": st.column_config.NumberColumn("Días Perdidos", min_value=0),
        
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
