import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Dashboard SST", layout="wide", page_icon="⛑️")

# --- 1. CARGA DE DATOS (Tus datos extraídos del CSV) ---
csv_data = """MES,CANTIDAD DE TRABAJADORES,ACTOS INSEGUROS,CONDICIONES INSEGURAS,Días perdidos,Total horas Trabajadas,ACCIDENTES,INCIDENTES,Indice de severidad,Indice de Frecuencia,Índice de Gravedad ,INSPECCIONES PROGRAMADAS,INSPECCIONES EJECUTADAS,CAPACITACIONES PROGRAMADAS,CAPACITACIONES EJECUTUDAS,Fecha del ultimo accidente
2025-01-01,22,0,0,0,3872.0,0,0,0,0,0,10,5,10,10,2025-10-09
2025-02-01,22,0,0,0,3872.0,0,0,0,0,0,10,5,10,10,2025-10-09
2025-03-01,22,0,0,0,3872.0,0,0,0,0,0,10,8,10,8,2025-10-09
2025-04-01,22,0,0,0,3872.0,0,0,0,0,0,10,2,10,10,2025-10-09
2025-05-01,22,0,0,0,3872.0,0,0,0,0,0,10,4,10,2,2025-10-09
2025-06-01,22,0,0,0,3872.0,0,0,0,0,0,10,1,10,10,2025-10-09
2025-07-01,22,0,0,5,3872.0,1,0,1291.32,258.26,1.29,10,5,10,5,2025-10-09
2025-08-01,22,0,0,0,3872.0,0,0,0,0,0,10,2,10,3,2025-10-09
2025-09-01,22,0,0,0,3872.0,0,0,0,0,0,10,8,10,8,2025-10-09
2025-10-01,22,0,0,0,3872.0,1,0,0,258.26,0,0,1,0,1,2025-10-09
2025-11-01,23,1,1,0,4048,0,0,0,0,0,5,5,5,5,2025-10-09
2025-12-01,21,0,0,0,3696,0,0,0,0,0,0,0,0,0,2025-10-09
"""

@st.cache_data
def load_data():
    df = pd.read_csv(StringIO(csv_data))
    df['MES'] = pd.to_datetime(df['MES'])
    # Calcular cumplimiento %
    df['% Cumplimiento Insp'] = (df['INSPECCIONES EJECUTADAS'] / df['INSPECCIONES PROGRAMADAS']).fillna(0) * 100
    df['% Cumplimiento Cap'] = (df['CAPACITACIONES EJECUTUDAS'] / df['CAPACITACIONES PROGRAMADAS']).fillna(0) * 100
    return df

df = load_data()

# --- TÍTULO ---
st.title("🛡️ App de Gestión SST - Tablero de Control")
st.markdown(f"**Última actualización:** {datetime.now().strftime('%d/%m/%Y')}")

# --- FILTROS SIDEBAR ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3050/3050523.png", width=100)
st.sidebar.header("Filtrar Datos")
years = df['MES'].dt.year.unique()
year_sel = st.sidebar.selectbox("Seleccionar Año", years, index=0)

df_filtered = df[df['MES'].dt.year == year_sel]

# --- CÁLCULO DE KPIs ---
total_acc = df_filtered['ACCIDENTES'].sum()
dias_perdidos = df_filtered['Días perdidos'].sum()
actos_ins = df_filtered['ACTOS INSEGUROS'].sum()
cond_ins = df_filtered['CONDICIONES INSEGURAS'].sum()

# Calcular días sin accidentes desde la última fecha registrada
try:
    last_acc_date = pd.to_datetime(df_filtered['Fecha del ultimo accidente'].iloc[-1])
    dias_sin_acc = (datetime.now() - last_acc_date).days
except:
    dias_sin_acc = "N/A"

# --- VISUALIZACIÓN KPIs (Top Row) ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("🗓️ Días sin Accidentes", f"{dias_sin_acc}", delta_color="normal")
col2.metric("🚑 Accidentes (Año)", int(total_acc), delta="Acumulado", delta_color="inverse")
col3.metric("⚠️ Actos Inseguros", int(actos_ins))
col4.metric("🏗️ Condiciones Inseguras", int(cond_ins))

st.markdown("---")

# --- GRÁFICOS ---

# Fila 1: Índices y Torta
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📈 Evolución de Índices (Frecuencia y Severidad)")
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=df_filtered['MES'], y=df_filtered['Indice de Frecuencia'], 
                    mode='lines+markers', name='Frecuencia', line=dict(color='orange')))
    fig_line.add_trace(go.Scatter(x=df_filtered['MES'], y=df_filtered['Indice de severidad'], 
                    mode='lines+markers', name='Severidad', line=dict(color='red')))
    fig_line.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_line, use_container_width=True)

with c2:
    st.subheader("🔍 Actos vs Condiciones")
    labels = ['Actos Inseguros', 'Condiciones Inseguras']
    values = [actos_ins, cond_ins]
    fig_pie = px.pie(names=labels, values=values, hole=0.4, color_discrete_sequence=['#FFA726', '#EF5350'])
    fig_pie.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_pie, use_container_width=True)

# Fila 2: Barras de Gestión
st.subheader("📊 Gestión Preventiva (Planificado vs Ejecutado)")
c3, c4 = st.columns(2)

with c3:
    # Gráfico Inspecciones
    fig_insp = go.Figure(data=[
        go.Bar(name='Programadas', x=df_filtered['MES'], y=df_filtered['INSPECCIONES PROGRAMADAS'], marker_color='#E0E0E0'),
        go.Bar(name='Ejecutadas', x=df_filtered['MES'], y=df_filtered['INSPECCIONES EJECUTADAS'], marker_color='#66BB6A')
    ])
    fig_insp.update_layout(title="Inspecciones", barmode='group', height=300)
    st.plotly_chart(fig_insp, use_container_width=True)

with c4:
    # Gráfico Capacitaciones
    fig_cap = go.Figure(data=[
        go.Bar(name='Programadas', x=df_filtered['MES'], y=df_filtered['CAPACITACIONES PROGRAMADAS'], marker_color='#E0E0E0'),
        go.Bar(name='Ejecutadas', x=df_filtered['MES'], y=df_filtered['CAPACITACIONES EJECUTUDAS'], marker_color='#42A5F5')
    ])
    fig_cap.update_layout(title="Capacitaciones", barmode='group', height=300)
    st.plotly_chart(fig_cap, use_container_width=True)

# --- TABLA DE DATOS ---
with st.expander("📂 Ver Base de Datos Completa"):
    st.dataframe(df_filtered.style.format({
        'Indice de Frecuencia': '{:.2f}',
        'Indice de severidad': '{:.2f}',
        '% Cumplimiento Insp': '{:.1f}%',
        '% Cumplimiento Cap': '{:.1f}%'
    }))

# --- BOTÓN DE ACCIÓN ---
st.sidebar.markdown("---")
st.sidebar.info("Para actualizar estos datos, edita el archivo fuente o conecta una base de datos en la nube.")
