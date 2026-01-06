import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil import relativedelta # Necesario para calcular años/meses/dias exactos
from fpdf import FPDF

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Reporte SST", layout="wide", page_icon="⛑️")

# --- ESTILOS CSS PERSONALIZADOS (PARA COPIAR EL DISEÑO DE LA FOTO) ---
st.markdown("""
    <style>
    /* Eliminar márgenes de arriba para que se vea como app */
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    
    /* Estilos para las cajas de KPIs (Cuadros de colores) */
    .kpi-box {
        color: white;
        padding: 10px;
        text-align: center;
        border-radius: 5px;
        font-family: Arial, sans-serif;
        height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .kpi-title { font-size: 14px; font-weight: bold; margin-bottom: 5px; }
    .kpi-value { font-size: 30px; font-weight: bold; }
    
    /* Colores específicos de la imagen */
    .bg-orange { background-color: #FFC000; color: black; } /* Actos Inseguros */
    .bg-blue-dark { background-color: #002060; } /* Condiciones */
    .bg-blue-light { background-color: #5B9BD5; } /* Severidad */
    .bg-green { background-color: #00B050; } /* Frecuencia */
    .bg-red { background-color: #C00000; } /* Gravedad / Header */
    
    /* Caja de Días sin Accidentes */
    .days-box {
        background-color: #164020; /* Verde oscuro */
        color: white;
        padding: 20px;
        text-align: center;
        border-radius: 5px;
        border: 2px solid #00B050;
    }
    
    /* Header Principal */
    .main-header {
        background-color: #C00000;
        color: white;
        padding: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 24px;
        margin-bottom: 20px;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CLASE PDF (Mantenida) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'REPORTE MENSUAL DE EVENTOS DE SST', 0, 1, 'C')
        self.ln(5)

# --- GESTIÓN DE DATOS (SESSION STATE) ---
if 'data_main' not in st.session_state:
    st.session_state['data_main'] = pd.DataFrame()

# --- BARRA LATERAL (Mantenida igual) ---
st.sidebar.title("Configuración")
uploaded_file = st.sidebar.file_uploader("📂 Cargar Base de Datos", type=["csv", "xlsx"])

# Función de carga
def load_data(file):
    df = pd.DataFrame()
    if file:
        try:
            if file.name.endswith('.csv'): df = pd.read_csv(file)
            else: df = pd.read_excel(file)
        except: pass
    else:
        # URL por defecto
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSHnEKxzb-M3T0PjzyA1zPv_h-awqQ0og6imzQ5uHJG8wk85-WBBgtoCWC9FnusngmDw72kL88tduR3/pub?gid=1349054762&single=true&output=csv"
        try: df = pd.read_csv(url)
        except: pass
    
    if not df.empty:
        df.columns = df.columns.str.strip()
        # Normalizar nombres
        mapa = {
            'Dias perdidos': 'Días perdidos', 'Accidentes': 'ACCIDENTES',
            'Actos Inseguros': 'ACTOS INSEGUROS', 'Condiciones Inseguras': 'CONDICIONES INSEGURAS',
            'Mes': 'MES', 'Indice de Frecuencia': 'IF', 'Indice de severidad': 'IS',
            'Indice de Gravedad': 'IG'
        }
        df = df.rename(columns=mapa)
        if 'MES' in df.columns: df['MES'] = pd.to_datetime(df['MES'])
        
        # Asegurar columnas numéricas
        cols_num = ['ACCIDENTES', 'ACTOS INSEGUROS', 'CONDICIONES INSEGURAS', 'IF', 'IS', 'IG', 
                   'INSPECCIONES PROGRAMADAS', 'INSPECCIONES EJECUTADAS', 
                   'CAPACITACIONES PROGRAMADAS', 'CAPACITACIONES EJECUTUDAS']
        for col in cols_num:
            if col not in df.columns: df[col] = 0
            
    return df

# Cargar datos
if uploaded_file or st.session_state['data_main'].empty:
    st.session_state['data_main'] = load_data(uploaded_file)
df = st.session_state['data_main']

# --- FORMULARIO DE INGRESO MANUAL ---
with st.sidebar.expander("📝 Ingresar Datos Manualmente"):
    f_fecha = st.date_input("Fecha")
    f_acc = st.number_input("Accidentes", 0)
    f_actos = st.number_input("Actos Inseguros", 0)
    f_cond = st.number_input("Condiciones Inseguras", 0)
    if st.button("Agregar"):
        new = pd.DataFrame([{'MES': pd.to_datetime(f_fecha), 'ACCIDENTES': f_acc, 
                           'ACTOS INSEGUROS': f_actos, 'CONDICIONES INSEGURAS': f_cond}])
        st.session_state['data_main'] = pd.concat([st.session_state['data_main'], new], ignore_index=True)
        st.rerun()

df = st.session_state['data_main']
if df.empty: st.stop()

# --- FILTRO DE FECHA (Como en la imagen: Mes y Año) ---
years = sorted(df['MES'].dt.year.unique(), reverse=True)
selected_year = st.sidebar.selectbox("Año", years)
df_year = df[df['MES'].dt.year == selected_year]

months = sorted(df_year['MES'].dt.month.unique())
month_names = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
               7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
selected_month_num = st.sidebar.selectbox("Mes", months, format_func=lambda x: month_names[x])

# Filtrar datos EXACTOS del mes seleccionado
df_month = df_year[df_year['MES'].dt.month == selected_month_num]

# Datos Acumulados hasta la fecha seleccionada
df_acumulado = df_year[df_year['MES'].dt.month <= selected_month_num]

# --- INTERFAZ GRÁFICA (AQUI EMPIEZA EL DISEÑO DE LA FOTO) ---

# 1. HEADER ROJO
st.markdown('<div class="main-header">REPORTE MENSUAL DE EVENTOS DE SST</div>', unsafe_allow_html=True)

# 2. FILA DE KPIS (CUADROS DE COLORES)
# Obtenemos valores. Si no hay datos, ponemos 0
val_actos = df_month['ACTOS INSEGUROS'].sum() if not df_month.empty else 0
val_cond = df_month['CONDICIONES INSEGURAS'].sum() if not df_month.empty else 0
val_sev = df_month['IS'].sum() if 'IS' in df_month.columns else 0
val_frec = df_month['IF'].sum() if 'IF' in df_month.columns else 0
val_grav = df_month['IG'].sum() if 'IG' in df_month.columns else 0

c1, c2, c3, c4, c5, c6 = st.columns([1.5, 2, 2, 2, 2, 2])

with c1:
    # Logo simulado y fecha
    st.image("https://cdn-icons-png.flaticon.com/512/1089/1089129.png", width=50) # Icono madera/construcción
    st.markdown(f"**{month_names[selected_month_num]}**")
    st.markdown(f"**{selected_year}**")

with c2:
    st.markdown(f"""<div class="kpi-box bg-orange"><div class="kpi-title">ACTOS INSEGUROS</div><div class="kpi-value">{int(val_actos)}</div></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="kpi-box bg-blue-dark"><div class="kpi-title">CONDICIONES INSEGURAS</div><div class="kpi-value">{int(val_cond)}</div></div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="kpi-box bg-blue-light"><div class="kpi-title">INDICE SEVERIDAD</div><div class="kpi-value">{val_sev:.0f}</div></div>""", unsafe_allow_html=True)
with c5:
    st.markdown(f"""<div class="kpi-box bg-green"><div class="kpi-title">INDICE FRECUENCIA</div><div class="kpi-value">{val_frec:.0f}</div></div>""", unsafe_allow_html=True)
with c6:
    st.markdown(f"""<div class="kpi-box bg-red"><div class="kpi-title">INDICE GRAVEDAD</div><div class="kpi-value">{val_grav:.2f}</div></div>""", unsafe_allow_html=True)

st.markdown("---")

# 3. FILA DE GRÁFICOS (CENTRO)
g1, g2, g3 = st.columns(3)

with g1:
    # GRÁFICO LINEA: ACTOS VS CONDICIONES (Todo el año)
    st.markdown("**Actos vs Condiciones (Anual)**")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df_year['MES'], y=df_year['ACTOS INSEGUROS'], name='Actos', line=dict(color='#FFC000')))
    fig1.add_trace(go.Scatter(x=df_year['MES'], y=df_year['CONDICIONES INSEGURAS'], name='Condiciones', line=dict(color='#C00000')))
    fig1.update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

with g2:
    # GRÁFICO BARRAS: ACCIDENTES (Acumulado)
    st.markdown("**ACUMULADO (Accidentes)**")
    total_acc = df_acumulado['ACCIDENTES'].sum()
    # Grafico simple
    fig2 = go.Figure(data=[go.Bar(x=['Accidentes'], y=[total_acc], marker_color='#5B9BD5')])
    fig2.update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig2, use_container_width=True)

with g3:
    # GRÁFICO BARRAS: INDICES (Mes)
    st.markdown("**MES (Índices)**")
    fig3 = go.Figure(data=[
        go.Bar(name='Frecuencia', x=['Indices'], y=[val_frec], marker_color='#5B9BD5'),
        go.Bar(name='Severidad', x=['Indices'], y=[val_sev], marker_color='#C00000')
    ])
    fig3.update_layout(height=250, barmode='group', margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig3, use_container_width=True)

# 4. SECCIÓN INFERIOR (TABLAS Y DIAS SIN ACCIDENTES)
st.markdown("---")
col_bottom_left, col_bottom_right = st.columns([2, 1.5])

with col_bottom_left:
    # Tablas de gestión (Estilo cabecera naranja)
    insp_prog = df_month['INSPECCIONES PROGRAMADAS'].sum() if 'INSPECCIONES PROGRAMADAS' in df_month.columns else 0
    insp_ejec = df_month['INSPECCIONES EJECUTADAS'].sum() if 'INSPECCIONES EJECUTADAS' in df_month.columns else 0
    
    cap_prog = df_month['CAPACITACIONES PROGRAMADAS'].sum() if 'CAPACITACIONES PROGRAMADAS' in df_month.columns else 0
    cap_ejec = df_month['CAPACITACIONES EJECUTUDAS'].sum() if 'CAPACITACIONES EJECUTUDAS' in df_month.columns else 0

    c_tbl1, c_tbl2 = st.columns(2)
    with c_tbl1:
        st.markdown("""<div style="background-color:orange; color:white; font-weight:bold; padding:2px;">INSPECCIONES</div>""", unsafe_allow_html=True)
        st.write(f"Programadas: **{insp_prog}**")
        st.write(f"Ejecutadas: **{insp_ejec}**")
        # Mini gráfico
        fig_i = go.Figure(data=[go.Bar(y=['Insp'], x=[insp_prog], name='Prog', orientation='h', marker_color='red'),
                                go.Bar(y=['Insp'], x=[insp_ejec], name='Ejec', orientation='h', marker_color='green')])
        fig_i.update_layout(height=100, barmode='group', margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
        st.plotly_chart(fig_i, use_container_width=True)

    with c_tbl2:
        st.markdown("""<div style="background-color:orange; color:white; font-weight:bold; padding:2px;">CAPACITACIONES</div>""", unsafe_allow_html=True)
        st.write(f"Programadas: **{cap_prog}**")
        st.write(f"Ejecutadas: **{cap_ejec}**")
        # Mini gráfico
        fig_c = go.Figure(data=[go.Bar(y=['Cap'], x=[cap_prog], name='Prog', orientation='h', marker_color='red'),
                                go.Bar(y=['Cap'], x=[cap_ejec], name='Ejec', orientation='h', marker_color='green')])
        fig_c.update_layout(height=100, barmode='group', margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
        st.plotly_chart(fig_c, use_container_width=True)

with col_bottom_right:
    # CÁLCULO DE DÍAS SIN ACCIDENTES
    # Buscamos la fecha del último accidente en TODA la base de datos histórica
    fecha_ultimo_accidente = datetime.now() # Por defecto hoy si no hay datos
    
    # Buscar el último registro donde ACCIDENTES > 0
    accidentes_reales = df[df['ACCIDENTES'] > 0]
    if not accidentes_reales.empty:
        fecha_ultimo_accidente = accidentes_reales['MES'].max()
    
    # Calcular diferencia
    hoy = datetime.now()
    diferencia = relativedelta.relativedelta(hoy, fecha_ultimo_accidente)
    
    # TEXTO GRANDE VERDE
    st.markdown("""<div style="background-color:#00B050; color:white; font-weight:bold; padding:5px;">DIAS SIN ACCIDENTES</div>""", unsafe_allow_html=True)
    
    html_dias = f"""
    <div class="days-box">
        <div style="font-size:40px;">📅</div>
        <div style="font-size:24px; margin-top:10px;">
            {diferencia.years} años, {diferencia.months} meses<br>y {diferencia.days} días.
        </div>
    </div>
    """
    st.markdown(html_dias, unsafe_allow_html=True)
    
    # Observaciones
    st.text_area("OBSERVACIONES", height=100, placeholder="Escribe aquí las observaciones del mes...")

# --- PDF ---
if st.sidebar.button("📄 Descargar PDF Layout"):
    st.toast("Generando PDF...")
    # (Aquí iría la lógica del PDF que ya tenías, simplificada para el ejemplo)
