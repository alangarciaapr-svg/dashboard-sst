import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil import relativedelta
import os

# --- 1. CONFIGURACIÓN E INICIO ---
st.set_page_config(page_title="Gestión SST", layout="wide", page_icon="⛑️")

# --- 2. ESTILOS CSS (DISEÑO EXACTO) ---
st.markdown("""
    <style>
    /* Ajuste para que el Título Rojo no se corte */
    .block-container { 
        padding-top: 3.5rem; 
        padding-bottom: 2rem; 
    }
    
    /* Cajas de KPIs */
    .kpi-box {
        color: white;
        text-align: center;
        border: 1px solid #ddd;
        height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-bottom: 5px;
    }
    /* Clases de color */
    .bg-orange { background-color: #FFC000; } 
    .bg-blue-dark { background-color: #002060; } 
    .bg-blue-light { background-color: #5B9BD5; } 
    .bg-green { background-color: #00B050; } 
    .bg-red { background-color: #C00000; } 
    
    /* Header Rojo */
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
    .date-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 14px; margin-bottom: 10px; }
    .date-header { background-color: #FFC000; border: 1px solid black; font-weight: bold; font-size: 12px; }
    .date-cell { background-color: white; border: 1px solid black; font-weight: bold; }
    
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

# --- 3. GESTIÓN DE DATOS (SESSION STATE) ---
if 'data_main' not in st.session_state:
    st.session_state['data_main'] = pd.DataFrame()

# --- 4. BARRA LATERAL: CARGA Y DESCARGA ---
st.sidebar.title("Configuración")

# Carga de archivos
uploaded_file = st.sidebar.file_uploader("📂 Cargar Datos (Excel/CSV)", type=["csv", "xlsx"])
uploaded_logo = st.sidebar.file_uploader("🖼️ Cargar Logo (Opcional)", type=["png", "jpg", "jpeg"])

# Función de carga inicial
def load_data(file):
    df = pd.DataFrame()
    if file:
        try:
            if file.name.endswith('.csv'): df = pd.read_csv(file)
            else: df = pd.read_excel(file)
        except: pass
    else:
        # URL de respaldo
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSHnEKxzb-M3T0PjzyA1zPv_h-awqQ0og6imzQ5uHJG8wk85-WBBgtoCWC9FnusngmDw72kL88tduR3/pub?gid=1349054762&single=true&output=csv"
        try: df = pd.read_csv(url)
        except: pass
    
    if not df.empty:
        df.columns = df.columns.str.strip()
        # Normalizar nombres para evitar errores
        mapa = {
            'Dias perdidos': 'Días perdidos', 'Accidentes': 'ACCIDENTES',
            'Actos Inseguros': 'ACTOS INSEGUROS', 'Condiciones Inseguras': 'CONDICIONES INSEGURAS',
            'Mes': 'MES', 'Indice de Frecuencia': 'IF', 'Indice de severidad': 'IS', 'Indice de Gravedad': 'IG'
        }
        df = df.rename(columns=mapa)
        if 'MES' in df.columns: df['MES'] = pd.to_datetime(df['MES'])
        
        # Asegurar columnas numéricas (rellenar con 0)
        cols_num = ['ACCIDENTES', 'ACTOS INSEGUROS', 'CONDICIONES INSEGURAS', 'IF', 'IS', 'IG', 
                   'INSPECCIONES PROGRAMADAS', 'INSPECCIONES EJECUTADAS', 
                   'CAPACITACIONES PROGRAMADAS', 'CAPACITACIONES EJECUTUDAS']
        for col in cols_num:
            if col not in df.columns: df[col] = 0
            else: df[col] = df[col].fillna(0)
            
    return df

# Cargar datos a la sesión si está vacía o si suben archivo nuevo
if uploaded_file:
    st.session_state['data_main'] = load_data(uploaded_file)
elif st.session_state['data_main'].empty:
    st.session_state['data_main'] = load_data(None)

# --- 5. EDITOR DE DATOS (LA GRAN MEJORA) ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 📝 Editor de Datos")
modo_edicion = st.sidebar.checkbox("Mostrar Tabla Editable", value=False)

if st.session_state['data_main'].empty:
    st.warning("⚠️ No hay datos cargados. Sube un archivo Excel.")
    st.stop()

# Si el usuario activa la edición, mostramos el editor
if modo_edicion:
    st.subheader("📝 Edición de Base de Datos en Vivo")
    st.info("Haz clic en cualquier celda para editar. Puedes añadir filas abajo del todo.")
    
    # El editor devuelve el dataframe modificado
    edited_df = st.data_editor(
        st.session_state['data_main'],
        num_rows="dynamic", # Permite agregar/borrar filas
        use_container_width=True,
        key="editor_principal"
    )
    
    # Actualizamos la sesión con los cambios
    # (Streamlit lo hace al recargar, pero aseguramos la persistencia)
    st.session_state['data_main'] = edited_df

    # Botón para descargar lo editado
    st.markdown("### 💾 Guardar Cambios")
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar Excel Actualizado (CSV)",
        data=csv,
        file_name='base_datos_sst_editada.csv',
        mime='text/csv'
    )
    st.markdown("---")

# Usamos siempre los datos (posiblemente editados) para los gráficos
df = st.session_state['data_main']

# --- 6. FILTROS DEL DASHBOARD ---
# Convertir MES a fecha si se rompió en la edición
try:
    df['MES'] = pd.to_datetime(df['MES'])
except:
    pass

years = sorted(df['MES'].dt.year.unique(), reverse=True)
selected_year = st.sidebar.selectbox("Año Reporte", years) if len(years) > 0 else 2025
df_year = df[df['MES'].dt.year == selected_year]

months = sorted(df_year['MES'].dt.month.unique())
if len(months) > 0:
    month_names = {1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio", 
                   7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"}
    selected_month_num = st.sidebar.selectbox("Mes Reporte", months, format_func=lambda x: month_names.get(x, x))
    month_text = month_names.get(selected_month_num, str(selected_month_num))
    df_month = df_year[df_year['MES'].dt.month == selected_month_num]
    df_acumulado = df_year[df_year['MES'].dt.month <= selected_month_num]
else:
    st.warning("No hay datos para el año seleccionado.")
    st.stop()

# --- 7. DASHBOARD VISUAL (Igual que antes) ---

# HEADER
st.markdown('<div class="main-header">REPORTE MENSUAL DE EVENTOS DE SST</div>', unsafe_allow_html=True)

# LOGO Y KPIs
c1, c2, c3, c4, c5, c6 = st.columns([1.5, 2, 2, 2, 2, 2])

with c1:
    # Tabla Fecha
    html_date = f"""
    <table class="date-table">
        <tr><td class="date-header">MES</td><td class="date-header">AÑO</td></tr>
        <tr><td class="date-cell">{month_text}</td><td class="date-cell">{selected_year}</td></tr>
    </table>
    """
    st.markdown(html_date, unsafe_allow_html=True)
    # Logo
    if uploaded_logo: st.image(uploaded_logo, use_container_width=True)
    elif os.path.exists("logo-maderas-gd-1.png"): st.image("logo-maderas-gd-1.png", use_container_width=True)
    else: st.info("Falta Logo")

# Cálculos KPI
v_actos = int(df_month['ACTOS INSEGUROS'].sum())
v_cond = int(df_month['CONDICIONES INSEGURAS'].sum())
v_sev = df_month['IS'].sum()
v_frec = df_month['IF'].sum()
v_grav = df_month['IG'].sum()

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

# GRÁFICOS
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

# PIE DE PÁGINA (Tablas y Dias sin accidentes)
st.markdown("""
<div style="display:flex; width:100%;">
    <div style="width:33%; background-color:#FFC000; padding:2px 5px; font-weight:bold; font-style:italic; border:1px solid black;">INSPECCIONES EN EL MES</div>
    <div style="width:33%; background-color:#FFC000; padding:2px 5px; font-weight:bold; font-style:italic; border:1px solid black; margin-left:1%;">CAPACITACIONES EN EL MES</div>
    <div style="width:33%; background-color:#00B050; padding:2px 5px; font-weight:bold; font-style:italic; border:1px solid black; margin-left:1%; color:white;">DIAS SIN ACCIDENTES</div>
</div>
""", unsafe_allow_html=True)

col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
    insp_p = int(df_month['INSPECCIONES PROGRAMADAS'].sum())
    insp_e = int(df_month['INSPECCIONES EJECUTADAS'].sum())
    st.write(f"**PROGRAMADAS:** {insp_p}")
    st.write(f"**EJECUTADAS:** {insp_e}")
    fig_i = go.Figure(data=[
        go.Bar(name='Prog', x=[insp_p], y=[''], orientation='h', marker_color='#C00000'),
        go.Bar(name='Ejec', x=[insp_e], y=[''], orientation='h', marker_color='#00B050')
    ])
    fig_i.update_layout(height=100, margin=dict(l=0,r=0,t=0,b=0), showlegend=True, barmode='group', legend=dict(orientation="h", y=-0.5))
    st.plotly_chart(fig_i, use_container_width=True)

with col_b2:
    cap_p = int(df_month['CAPACITACIONES PROGRAMADAS'].sum())
    cap_e = int(df_month['CAPACITACIONES EJECUTUDAS'].sum())
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
    
    try:
        diff = relativedelta.relativedelta(datetime.now(), fecha_acc)
    except:
        diff = relativedelta.relativedelta(datetime.now(), datetime.now()) # Fallback
    
    st.markdown(f"""
    <div class="days-container">
        <div style="font-size:50px; margin-bottom:10px;">📅</div>
        <div style="font-size:26px; font-weight:bold; line-height:1.2;">
            {diff.years} años, {diff.months} meses<br>y {diff.days} días.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Se asume el departamento de PP.RR...")
