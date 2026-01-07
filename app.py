import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil import relativedelta
from fpdf import FPDF
import os
import tempfile

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión SST", layout="wide", page_icon="⛑️")

# --- 2. ESTILOS CSS (LIMPIEZA DE SOLAPAMIENTOS) ---
st.markdown("""
    <style>
    /* Ajuste general limpio sin forzar posiciones */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 95%;
    }

    /* Estilo para las Cajas de KPIs */
    .kpi-container {
        background-color: white;
        border: 1px solid #ddd;
        padding: 0px;
        margin-bottom: 10px;
    }
    .kpi-header {
        font-size: 12px;
        font-weight: bold;
        text-align: center;
        padding: 5px;
        border-bottom: 1px solid #eee;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #f9f9f9;
        color: black;
    }
    .kpi-body {
        font-size: 30px;
        font-weight: bold;
        text-align: center;
        color: white;
        padding: 10px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Colores de Fondo */
    .bg-orange { background-color: #FFC000; }
    .bg-blue-dark { background-color: #002060; }
    .bg-blue-light { background-color: #5B9BD5; }
    .bg-green { background-color: #00B050; }
    .bg-red { background-color: #C00000; }

    /* Header Rojo Principal */
    .main-title {
        background-color: #C00000;
        color: white;
        text-align: center;
        font-weight: bold;
        font-size: 24px;
        padding: 10px;
        border: 2px solid black;
        margin-bottom: 20px;
        text-transform: uppercase;
    }
    
    /* Contenedor de Dias sin Accidentes */
    .days-box {
        background-color: #164020;
        border: 3px solid #00B050;
        color: white;
        text-align: center;
        padding: 15px;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. CLASE PDF AVANZADA (PARA REPLICAR EL DISEÑO) ---
class ReportePDF(FPDF):
    def __init__(self, orientation='L', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        self.logo_path = None

    def header(self):
        # Header Rojo simulando el de la App
        self.set_fill_color(192, 0, 0) # Rojo oscuro
        self.rect(0, 0, 297, 15, 'F') # Barra superior completa
        self.set_font('Arial', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, -5, 'REPORTE MENSUAL DE EVENTOS DE SST', 0, 1, 'C')
        self.ln(15)

    def draw_kpi_box(self, x, y, w, title, value, r, g, b):
        # Dibuja un cuadro KPI idéntico al de la pantalla
        # Título (Caja blanca/gris)
        self.set_fill_color(240, 240, 240)
        self.set_draw_color(0, 0, 0)
        self.rect(x, y, w, 12, 'DF')
        self.set_xy(x, y+2)
        self.set_font('Arial', 'B', 8)
        self.set_text_color(0, 0, 0)
        self.multi_cell(w, 4, title, 0, 'C')
        
        # Valor (Caja Color)
        self.set_fill_color(r, g, b)
        self.rect(x, y+12, w, 15, 'F')
        self.set_xy(x, y+12)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.cell(w, 15, str(value), 0, 0, 'C')

# --- 4. CARGA DE DATOS ---
if 'data_main' not in st.session_state:
    st.session_state['data_main'] = pd.DataFrame()

# Barra Lateral
st.sidebar.title("🛠️ Panel de Control")
uploaded_file = st.sidebar.file_uploader("📂 Cargar Datos", type=["xlsx", "csv"])
uploaded_logo = st.sidebar.file_uploader("🖼️ Cargar Logo", type=["png", "jpg", "jpeg"])

# Gestión del Logo (Guardar temporalmente para el PDF)
logo_path = "logo_temp.png"
if uploaded_logo:
    with open(logo_path, "wb") as f:
        f.write(uploaded_logo.getbuffer())
elif os.path.exists("logo-maderas-gd-1.png"):
    logo_path = "logo-maderas-gd-1.png"
else:
    logo_path = None

def load_data(file):
    df = pd.DataFrame()
    if file:
        try:
            if file.name.endswith('.csv'): df = pd.read_csv(file)
            else: df = pd.read_excel(file)
        except: pass
    else:
        # URL Respaldo
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSHnEKxzb-M3T0PjzyA1zPv_h-awqQ0og6imzQ5uHJG8wk85-WBBgtoCWC9FnusngmDw72kL88tduR3/pub?gid=1349054762&single=true&output=csv"
        try: df = pd.read_csv(url)
        except: pass
    
    if not df.empty:
        df.columns = df.columns.str.strip()
        mapa = {
            'Dias perdidos': 'Días perdidos', 'Accidentes': 'ACCIDENTES',
            'Actos Inseguros': 'ACTOS INSEGUROS', 'Condiciones Inseguras': 'CONDICIONES INSEGURAS',
            'Mes': 'MES', 'Indice de Frecuencia': 'IF', 'Indice de severidad': 'IS', 'Indice de Gravedad': 'IG'
        }
        df = df.rename(columns=mapa)
        if 'MES' in df.columns: df['MES'] = pd.to_datetime(df['MES'])
        
        # Rellenar ceros
        cols = ['ACCIDENTES', 'ACTOS INSEGUROS', 'CONDICIONES INSEGURAS', 'IF', 'IS', 'IG', 
                'INSPECCIONES PROGRAMADAS', 'INSPECCIONES EJECUTADAS', 
                'CAPACITACIONES PROGRAMADAS', 'CAPACITACIONES EJECUTUDAS']
        for c in cols:
            if c not in df.columns: df[c] = 0
            df[c] = df[c].fillna(0)
    return df

if uploaded_file: st.session_state['data_main'] = load_data(uploaded_file)
elif st.session_state['data_main'].empty: st.session_state['data_main'] = load_data(None)

# Editor
if st.sidebar.checkbox("Editar Datos", False):
    st.session_state['data_main'] = st.data_editor(st.session_state['data_main'], num_rows="dynamic")

df = st.session_state['data_main']
if df.empty: st.stop()

# --- 5. LOGICA DE FILTROS ---
try: df['MES'] = pd.to_datetime(df['MES'])
except: pass

years = sorted(df['MES'].dt.year.unique(), reverse=True)
sel_year = st.sidebar.selectbox("Año", years) if years else 2025
df_year = df[df['MES'].dt.year == sel_year]

months = sorted(df_year['MES'].dt.month.unique())
month_names = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
               7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}

if not months: st.stop()
sel_month = st.sidebar.selectbox("Mes", months, format_func=lambda x: month_names.get(x, x))
month_txt = month_names.get(sel_month, str(sel_month)).upper()

# Filtrar Dataframes
df_month = df_year[df_year['MES'].dt.month == sel_month]
df_acum = df_year[df_year['MES'].dt.month <= sel_month]

# --- 6. INTERFAZ GRÁFICA (DASHBOARD) ---

# --- HEADER Y LOGO ---
col_head, col_logo = st.columns([3, 1])
with col_head:
    st.markdown('<div class="main-title">REPORTE MENSUAL DE EVENTOS DE SST</div>', unsafe_allow_html=True)
with col_logo:
    if logo_path:
        st.image(logo_path, use_container_width=True)
    else:
        st.info("Logo")

# --- KPIs ---
v_actos = int(df_month['ACTOS INSEGUROS'].sum())
v_cond = int(df_month['CONDICIONES INSEGURAS'].sum())
v_sev = df_month['IS'].sum()
v_frec = df_month['IF'].sum()
v_grav = df_month['IG'].sum()

# Layout de KPIs (6 columnas: Fecha + 5 Indicadores)
cols_kpi = st.columns(6)

# Fecha (Columna 1)
with cols_kpi[0]:
    st.markdown(f"""
    <div style="border:1px solid black; text-align:center;">
        <div style="background:#FFC000; font-weight:bold;">MES / AÑO</div>
        <div style="background:white; font-weight:bold; padding:10px;">{month_txt}<br>{sel_year}</div>
    </div>
    """, unsafe_allow_html=True)

# Helper para renderizar KPI en HTML
def kpi_viz(title, val, bg_class):
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-header">{title}</div>
        <div class="kpi-body {bg_class}">{val}</div>
    </div>
    """, unsafe_allow_html=True)

with cols_kpi[1]: kpi_viz("ACTOS INSEGUROS", v_actos, "bg-orange")
with cols_kpi[2]: kpi_viz("CONDICIONES INSEGURAS", v_cond, "bg-blue-dark")
with cols_kpi[3]: kpi_viz("ÍNDICE SEVERIDAD", f"{v_sev:.0f}", "bg-blue-light")
with cols_kpi[4]: kpi_viz("ÍNDICE FRECUENCIA", f"{v_frec:.0f}", "bg-green")
with cols_kpi[5]: kpi_viz("ÍNDICE GRAVEDAD", f"{v_grav:.2f}", "bg-red")

st.markdown("---")

# --- GRÁFICOS ---
c_g1, c_g2, c_g3 = st.columns(3)

# 1. Línea Anual
meses_num = list(range(1, 13))
y_actos = [df_year[df_year['MES'].dt.month == m]['ACTOS INSEGUROS'].sum() for m in meses_num]
y_cond = [df_year[df_year['MES'].dt.month == m]['CONDICIONES INSEGURAS'].sum() for m in meses_num]

fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=meses_num, y=y_actos, name='ACTOS', line=dict(color='#5B9BD5', width=3)))
fig1.add_trace(go.Scatter(x=meses_num, y=y_cond, name='CONDICIONES', line=dict(color='#C00000', width=3)))
fig1.update_layout(title="Evolución Anual", margin=dict(l=20,r=20,t=40,b=20), height=250, legend=dict(orientation="h", y=-0.2))

with c_g1: st.plotly_chart(fig1, use_container_width=True)

# 2. Barras Acumuladas
tot_acc = df_acum['ACCIDENTES'].sum()
fig2 = go.Figure()
fig2.add_trace(go.Bar(x=['ACCIDENTES'], y=[tot_acc], marker_color='#5B9BD5', text=[tot_acc], textposition='auto'))
fig2.update_layout(title="Acumulado (Año)", margin=dict(l=20,r=20,t=40,b=20), height=250)
with c_g2: st.plotly_chart(fig2, use_container_width=True)

# 3. Barras Mes
fig3 = go.Figure()
fig3.add_trace(go.Bar(name='IF', x=['Indices'], y=[v_frec], marker_color='#5B9BD5', text=[f"{v_frec:.0f}"], textposition='auto'))
fig3.add_trace(go.Bar(name='IS', x=['Indices'], y=[v_sev], marker_color='#C00000', text=[f"{v_sev:.0f}"], textposition='auto'))
fig3.update_layout(title=f"Mes: {month_txt}", barmode='group', margin=dict(l=20,r=20,t=40,b=20), height=250)
with c_g3: st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# --- PIE DE PÁGINA ---
c_b1, c_b2, c_b3 = st.columns(3)

# Tablas Gestión
insp_p = int(df_month['INSPECCIONES PROGRAMADAS'].sum())
insp_e = int(df_month['INSPECCIONES EJECUTADAS'].sum())
cap_p = int(df_month['CAPACITACIONES PROGRAMADAS'].sum())
cap_e = int(df_month['CAPACITACIONES EJECUTUDAS'].sum())

with c_b1:
    st.info("**INSPECCIONES**")
    st.write(f"Prog: {insp_p} | Ejec: {insp_e}")
    fig_i = go.Figure(data=[go.Bar(y=['Insp'], x=[insp_p], orientation='h', name='Prog', marker_color='red'),
                            go.Bar(y=['Insp'], x=[insp_e], orientation='h', name='Ejec', marker_color='green')])
    fig_i.update_layout(height=80, margin=dict(l=0,r=0,t=0,b=0), barmode='group', showlegend=False)
    st.plotly_chart(fig_i, use_container_width=True)

with c_b2:
    st.info("**CAPACITACIONES**")
    st.write(f"Prog: {cap_p} | Ejec: {cap_e}")
    fig_c = go.Figure(data=[go.Bar(y=['Cap'], x=[cap_p], orientation='h', name='Prog', marker_color='#002060'),
                            go.Bar(y=['Cap'], x=[cap_e], orientation='h', name='Ejec', marker_color='green')])
    fig_c.update_layout(height=80, margin=dict(l=0,r=0,t=0,b=0), barmode='group', showlegend=False)
    st.plotly_chart(fig_c, use_container_width=True)

# Días sin accidentes
fecha_acc = datetime.now()
accs = df[df['ACCIDENTES'] > 0]
if not accs.empty: fecha_acc = accs['MES'].max()
try: diff = relativedelta.relativedelta(datetime.now(), fecha_acc)
except: diff = relativedelta.relativedelta(datetime.now(), datetime.now())

with c_b3:
    st.success("**DIAS SIN ACCIDENTES**")
    st.markdown(f"""
    <div style="text-align:center; font-size:24px; font-weight:bold; color:#164020;">
        {diff.years} años, {diff.months} meses<br>y {diff.days} días.
    </div>
    """, unsafe_allow_html=True)

# --- 7. GENERACIÓN DEL PDF (MAGIA FINAL) ---
st.sidebar.markdown("---")
if st.sidebar.button("📄 Descargar PDF Reporte"):
    with st.spinner("Generando PDF de alta fidelidad..."):
        try:
            # 1. Crear instancia PDF Landscape
            pdf = ReportePDF(orientation='L', format='A4')
            pdf.add_page()
            
            # 2. Logo (Posicionado a la derecha)
            if logo_path:
                pdf.image(logo_path, x=240, y=20, w=40)
            
            # 3. Fecha (Cuadro estilo tabla)
            pdf.set_xy(10, 20)
            pdf.set_fill_color(255, 192, 0) # Naranja
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(30, 8, "MES", 1, 0, 'C', True)
            pdf.cell(20, 8, "AÑO", 1, 1, 'C', True)
            pdf.set_xy(10, 28)
            pdf.set_fill_color(255, 255, 255)
            pdf.cell(30, 10, month_txt, 1, 0, 'C', True)
            pdf.cell(20, 10, str(sel_year), 1, 1, 'C', True)

            # 4. KPIs (Dibujar los cuadros de colores manualmente en PDF)
            start_x = 70
            gap = 35
            pdf.draw_kpi_box(start_x, 25, 30, "ACTOS\nINSEGUROS", v_actos, 255, 192, 0) # Naranja
            pdf.draw_kpi_box(start_x + gap, 25, 30, "CONDICIONES\nINSEGURAS", v_cond, 0, 32, 96) # Azul Osc
            pdf.draw_kpi_box(start_x + gap*2, 25, 30, "INDICE\nSEVERIDAD", f"{v_sev:.0f}", 91, 155, 213) # Azul Claro
            pdf.draw_kpi_box(start_x + gap*3, 25, 30, "INDICE\nFRECUENCIA", f"{v_frec:.0f}", 0, 176, 80) # Verde
            pdf.draw_kpi_box(start_x + gap*4, 25, 30, "INDICE\nGRAVEDAD", f"{v_grav:.2f}", 192, 0, 0) # Rojo

            # 5. Exportar Gráficos a Imágenes Temporales
            # Esto requiere 'kaleido' instalado
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp1:
                fig1.write_image(tmp1.name, width=500, height=300)
                path_g1 = tmp1.name
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp2:
                fig2.write_image(tmp2.name, width=400, height=300)
                path_g2 = tmp2.name
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp3:
                fig3.write_image(tmp3.name, width=400, height=300)
                path_g3 = tmp3.name

            # 6. Insertar Gráficos en PDF
            y_charts = 65
            pdf.image(path_g1, x=10, y=y_charts, w=90)
            pdf.image(path_g2, x=105, y=y_charts, w=80)
            pdf.image(path_g3, x=190, y=y_charts, w=80)

            # 7. Sección Inferior (Manual en PDF)
            y_bottom = 130
            # Barras Naranja/Verde Titulos
            pdf.set_xy(10, y_bottom)
            pdf.set_fill_color(255, 192, 0)
            pdf.cell(80, 8, "INSPECCIONES", 1, 0, 'C', True)
            pdf.cell(80, 8, "CAPACITACIONES", 1, 0, 'C', True)
            pdf.set_fill_color(0, 176, 80)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(100, 8, "DIAS SIN ACCIDENTES", 1, 1, 'C', True)

            # Textos inferiores
            pdf.set_text_color(0, 0, 0)
            pdf.set_xy(10, y_bottom + 10)
            pdf.cell(80, 10, f"Prog: {insp_p} | Ejec: {insp_e}", 0, 0, 'C')
            pdf.cell(80, 10, f"Prog: {cap_p} | Ejec: {cap_e}", 0, 0, 'C')
            
            # Texto Grande Dias
            pdf.set_font('Arial', 'B', 20)
            pdf.set_text_color(0, 100, 0)
            pdf.set_xy(170, y_bottom + 15)
            pdf.cell(100, 10, f"{diff.years} anios, {diff.months} meses", 0, 1, 'C')
            pdf.set_xy(170, y_bottom + 25)
            pdf.cell(100, 10, f"y {diff.days} dias", 0, 1, 'C')

            # Generar bytes
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            
            st.sidebar.download_button("💾 Guardar PDF", pdf_bytes, f"Reporte_{month_txt}_{sel_year}.pdf", "application/pdf")
            st.toast("PDF Generado con éxito", icon="✅")

        except Exception as e:
            st.error(f"Error generando PDF: {e}")
            st.warning("Asegúrate de tener 'kaleido' instalado en requirements.txt")
