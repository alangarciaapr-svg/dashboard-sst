import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil import relativedelta
from fpdf import FPDF
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Reporte SST", layout="wide", page_icon="⛑️")

# --- ESTILOS CSS (CORREGIDO PARA QUE NO SE CORTE EL TÍTULO) ---
st.markdown("""
    <style>
    /* AJUSTE CLAVE: Aumenté el padding-top a 3.5rem para bajar el contenido */
    .block-container { 
        padding-top: 3.5rem; 
        padding-bottom: 2rem; 
        padding-left: 2rem;
        padding-right: 2rem;
    }
    
    /* Opcional: Ocultar el menú hamburguesa y el footer de Streamlit para más limpieza */
    #MainMenu {visibility: visible;}
    footer {visibility: hidden;}
    
    /* Cajas de KPIs */
    .kpi-box {
        color: white;
        text-align: center;
        border-radius: 0px; 
        height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-bottom: 5px;
        border: 1px solid #ddd;
    }
    .kpi-title { font-size: 11px; font-weight: normal; margin-bottom: 0px; line-height: 1.2; color: black; }
    
    /* Colores exactos */
    .bg-orange { background-color: #FFC000; } 
    .bg-blue-dark { background-color: #002060; } 
    .bg-blue-light { background-color: #5B9BD5; } 
    .bg-green { background-color: #00B050; } 
    .bg-red { background-color: #C00000; } 
    
    /* Header Rojo - Aseguramos que tenga espacio */
    .main-header {
        background-color: #C00000;
        color: white;
        padding: 8px;
        text-align: center;
        font-weight: bold;
        font-size: 22px;
        margin-bottom: 20px;
        text-transform: uppercase;
        border: 1px solid black;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }

    /* Tabla Fecha */
    .date-table {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, sans-serif;
        text-align: center;
        font-size: 14px;
        margin-bottom: 10px;
    }
    .date-header {
        background-color: #FFC000; 
        border: 1px solid black;
        font-weight: bold;
        font-size: 12px;
    }
    .date-cell {
        background-color: white;
        border: 1px solid black;
        font-weight: bold;
    }

    /* Caja Verde Gigante */
    .days-container {
        background-color: #164020; 
        color: white;
        border: 3px solid #00B050; 
        padding: 15px;
        text-align: center;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE ESTADO ---
if 'data_main' not in st.session_state:
    st.session_state['data_main'] = pd.DataFrame()

# --- BARRA LATERAL ---
st.sidebar.title("Configuración")
uploaded_file = st.sidebar.file_uploader("📂 Cargar Datos (Excel/CSV)", type=["csv", "xlsx"])
uploaded_logo = st.sidebar.file_uploader("🖼️ Cargar Logo (Opcional)", type=["png", "jpg", "jpeg"])

def load_data(file):
    df = pd.DataFrame()
    if file:
        try:
            if file.name.endswith('.csv'): df = pd.read_csv(file)
            else: df = pd.read_excel(file)
        except: pass
    else:
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
        
        cols_num = ['ACCIDENTES', 'ACTOS INSEGUROS', 'CONDICIONES INSEGURAS', 'IF', 'IS', 'IG', 
                   'INSPECCIONES PROGRAMADAS', 'INSPECCIONES EJECUTADAS', 
                   'CAPACITACIONES PROGRAMADAS', 'CAPACITACIONES EJECUTUDAS']
        for col in cols_num:
            if col not in df.columns: df[col] = 0
            else: df[col] = df[col].fillna(0)
            
    return df

if uploaded_file or st.session_state['data_main'].empty:
    st.session_state['data_main'] = load_data(uploaded_file)
df = st.session_state['data_main']

# --- MANUAL INPUT ---
with st.sidebar.expander("📝 Ingreso Manual"):
    f_fecha = st.date_input("Fecha")
    f_acc = st.number_input("Accidentes", 0)
    f_actos = st.number_input("Actos", 0)
    f_cond = st.number_input("Condiciones", 0)
    if st.button("Agregar Registro"):
        new = pd.DataFrame([{'MES': pd.to_datetime(f_fecha), 'ACCIDENTES': f_acc, 
                           'ACTOS INSEGUROS': f_actos, 'CONDICIONES INSEGURAS': f_cond}])
        st.session_state['data_main'] = pd.concat([st.session_state['data_main'], new], ignore_index=True)
        st.rerun()

df = st.session_state['data_main']
if df.empty: st.stop()

# --- LOGICA FILTROS ---
years = sorted(df['MES'].dt.year.unique(), reverse=True)
selected_year = st.sidebar.selectbox("Año Reporte", years)
df_year = df[df['MES'].dt.year == selected_year]

months = sorted(df_year['MES'].dt.month.unique())
month_names = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
               7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
selected_month_num = st.sidebar.selectbox("Mes Reporte", months, format_func=lambda x: month_names[x])
month_text = month_names[selected_month_num]

df_month = df_year[df_year['MES'].dt.month == selected_month_num]
df_acumulado = df_year[df_year['MES'].dt.month <= selected_month_num]

# --- DASHBOARD ---

# 1. HEADER (Ahora con espacio seguro arriba)
st.markdown('<div class="main-header">REPORTE MENSUAL DE EVENTOS DE SST</div>', unsafe_allow_html=True)

# 2. LOGO Y KPIs
c1, c2, c3, c4, c5, c6 = st.columns([1.5, 2, 2, 2, 2, 2])

with c1:
    html_date = f"""
    <table class="date-table">
        <tr><td class="date-header">MES</td><td class="date-header">AÑO</td></tr>
        <tr><td class="date-cell">{month_text}</td><td class="date-cell">{selected_year}</td></tr>
    </table>
    """
    st.markdown(html_date, unsafe_allow_html=True)
    
    if uploaded_logo: st.image(uploaded_logo, use_container_width=True)
    elif os.path.exists("logo-maderas-gd-1.png"): st.image("logo-maderas-gd-1.png", use_container_width=True)
    else: st.info("Sube Logo")

v_actos = int(df_month['ACTOS INSEGUROS'].sum()) if not df_month.empty else 0
v_cond = int(df_month['CONDICIONES INSEGURAS'].sum()) if not df_month.empty else 0
v_sev = df_month['IS'].sum() if 'IS' in df_month.columns else 0
v_frec = df_month['IF'].sum() if 'IF' in df_month.columns else 0
v_grav = df_month['IG'].sum() if 'IG' in df_month.columns else 0

def kpi_html(title, value, color_class):
    return f"""
    <div style="display:flex; align-items:center; border:1px solid #ccc; margin-bottom:5px;">
        <div style="width:40%; padding:2px; font-size:10px; font-weight:bold; line-height:1.1; text-align:center;">{title}</div>
        <div class="{color_class}" style="width:60%; height:70px; display:flex; align-items:center; justify-content:center; color:white; font-size:28px; font-weight:bold;">
            {value}
        </div>
    </div>
    """

with c2: st.markdown(kpi_html("ACTOS INSEGUROS", v_actos, "bg-orange"), unsafe_allow_html=True)
with c3: st.markdown(kpi_html("CONDICIONES INSEGURAS", v_cond, "bg-blue-dark"), unsafe_allow_html=True)
with c4: st.markdown(kpi_html("Indice de severidad", f"{v_sev:.0f}", "bg-blue-light"), unsafe_allow_html=True)
with c5: st.markdown(kpi_html("Indice de Frecuencia", f"{v_frec:.0f}", "bg-green"), unsafe_allow_html=True)
with c6: st.markdown(kpi_html("Indice de Gravedad", f"{v_grav:.2f}".replace('.',','), "bg-red"), unsafe_allow_html=True)

st.markdown("---")

# 3. GRÁFICOS
g1, g2, g3 = st.columns(3)
meses_num = list(range(1, 13))

with g1:
    y_actos = [df_year[df_year['MES'].dt.month == m]['ACTOS INSEGUROS'].sum() for m in meses_num]
    y_cond = [df_year[df_year['MES'].dt.month == m]['CONDICIONES INSEGURAS'].sum() for m in meses_num]
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=meses_num, y=y_actos, name='ACTOS', line=dict(color='#5B9BD5', width=3)))
    fig1.add_trace(go.Scatter(x=meses_num, y=y_cond, name='CONDICIONES', line=dict(color='#C00000', width=3)))
    fig1.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=1), margin=dict(l=20,r=20,t=10,b=20), height=250, legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig1, use_container_width=True)

with g2:
    st.markdown("<div style='text-align:center; background-color:#002060; color:white; font-size:12px;'>ACUMULADO</div>", unsafe_allow_html=True)
    tot_acc = df_acumulado['ACCIDENTES'].sum()
    tot_inc = 0 
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=['ACCIDENTES'], y=[tot_acc], marker_color='#5B9BD5', width=0.3))
    fig2.add_trace(go.Bar(x=['INCIDENTES'], y=[tot_inc], marker_color='#C00000', width=0.3))
    fig2.update_layout(margin=dict(l=20,r=20,t=30,b=20), height=220)
    st.plotly_chart(fig2, use_container_width=True)

with g3:
    st.markdown("<div style='text-align:center; font-weight:bold; font-size:18px; color:gray;'>MES</div>", unsafe_allow_html=True)
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(name='IF', x=['Tasas'], y=[v_frec], marker_color='#5B9BD5'))
    fig3.add_trace(go.Bar(name='IS', x=['Tasas'], y=[v_sev], marker_color='#C00000'))
    fig3.update_layout(barmode='group', margin=dict(l=20,r=20,t=10,b=20), height=220, showlegend=True, legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# 4. TABLAS Y DIAS SIN ACCIDENTES
st.markdown("""
<div style="display:flex; width:100%;">
    <div style="width:33%; background-color:#FFC000; padding:2px 5px; font-weight:bold; font-style:italic; border:1px solid black;">INSPECCIONES EN EL MES</div>
    <div style="width:33%; background-color:#FFC000; padding:2px 5px; font-weight:bold; font-style:italic; border:1px solid black; margin-left:1%;">CAPACITACIONES EN EL MES</div>
    <div style="width:33%; background-color:#00B050; padding:2px 5px; font-weight:bold; font-style:italic; border:1px solid black; margin-left:1%; color:white;">DIAS SIN ACCIDENTES</div>
</div>
""", unsafe_allow_html=True)

col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
    insp_p = int(df_month['INSPECCIONES PROGRAMADAS'].sum()) if 'INSPECCIONES PROGRAMADAS' in df_month.columns else 0
    insp_e = int(df_month['INSPECCIONES EJECUTADAS'].sum()) if 'INSPECCIONES EJECUTADAS' in df_month.columns else 0
    st.write(f"**PROGRAMADAS:** {insp_p}")
    st.write(f"**EJECUTADAS:** {insp_e}")
    fig_i = go.Figure(data=[
        go.Bar(name='Prog', x=[insp_p], y=[''], orientation='h', marker_color='#C00000'),
        go.Bar(name='Ejec', x=[insp_e], y=[''], orientation='h', marker_color='#00B050')
    ])
    fig_i.update_layout(height=100, margin=dict(l=0,r=0,t=0,b=0), showlegend=True, barmode='group', legend=dict(orientation="h", y=-0.5))
    st.plotly_chart(fig_i, use_container_width=True)

with col_b2:
    cap_p = int(df_month['CAPACITACIONES PROGRAMADAS'].sum()) if 'CAPACITACIONES PROGRAMADAS' in df_month.columns else 0
    cap_e = int(df_month['CAPACITACIONES EJECUTUDAS'].sum()) if 'CAPACITACIONES EJECUTUDAS' in df_month.columns else 0
    st.write(f"**PROGRAMADAS:** {cap_p}")
    st.write(f"**EJECUTADAS:** {cap_e}")
    fig_c = go.Figure(data=[
        go.Bar(name='Prog', x=[cap_p], y=[''], orientation='h', marker_color='#002060'),
        go.Bar(name='Ejec', x=[cap_e], y=[''], orientation='h', marker_color='#00B050')
    ])
    fig_c.update_layout(height=100, margin=dict(l=0,r=0,t=0,b=0), showlegend=False, barmode='group')
    st.plotly_chart(fig_c, use_container_width=True)

with col_b3:
    fecha_acc = datetime.now()
    if not df.empty:
        accs = df[df['ACCIDENTES'] > 0]
        if not accs.empty: fecha_acc = accs['MES'].max()
    
    diff = relativedelta.relativedelta(datetime.now(), fecha_acc)
    
    st.markdown(f"""
    <div class="days-container">
        <div style="font-size:50px; margin-bottom:10px;">📅</div>
        <div style="font-size:26px; font-weight:bold; line-height:1.2;">
            {diff.years} años, {diff.months} meses<br>y {diff.days} días.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Se asume el departamento de PP.RR de la empresa con fecha 21/10/2025...")
