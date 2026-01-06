import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Dashboard SST", layout="wide", page_icon="⛑️")

# --- BARRA LATERAL: CARGA DE DATOS ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3050/3050523.png", width=100)
st.sidebar.title("Configuración")

# 1. Botón para subir archivo (Lo nuevo)
st.sidebar.header("📂 Actualizar Datos")
uploaded_file = st.sidebar.file_uploader("Arrastra tu Excel o CSV aquí", type=["csv", "xlsx"])

st.sidebar.markdown("---")

# --- FUNCIÓN DE CARGA DE DATOS ---
@st.cache_data(ttl=60) # Actualiza caché cada 60 segundos si usa la nube
def load_data(file_uploaded):
    df = pd.DataFrame()
    
    # CASO 1: El usuario subió un archivo
    if file_uploaded is not None:
        try:
            if file_uploaded.name.endswith('.csv'):
                df = pd.read_csv(file_uploaded)
            else:
                df = pd.read_excel(file_uploaded)
            st.toast("✅ Datos cargados desde tu archivo", icon="📂")
        except Exception as e:
            st.error(f"Error leyendo el archivo subido: {e}")
            return pd.DataFrame()
            
    # CASO 2: No hay archivo, intentar cargar desde Google Sheets (Nube)
    else:
        # Tu URL de Google Sheets
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSHnEKxzb-M3T0PjzyA1zPv_h-awqQ0og6imzQ5uHJG8wk85-WBBgtoCWC9FnusngmDw72kL88tduR3/pub?gid=1349054762&single=true&output=csv"
        try:
            df = pd.read_csv(url)
            # st.toast("☁️ Usando datos de la nube (Google Sheets)", icon="☁️") # Opcional: avisar
        except Exception as e:
            st.warning("⚠️ No se pudo conectar a la nube y no has subido archivo.")
            return pd.DataFrame()

    # --- LIMPIEZA Y FORMATO ---
    if not df.empty:
        # Eliminar timestamp de Google Forms si existe
        if 'Marca temporal' in df.columns:
            df = df.drop(columns=['Marca temporal'])
        
        # Convertir columna MES a fecha
        if 'MES' in df.columns:
            df['MES'] = pd.to_datetime(df['MES'])
        else:
            st.error("Error: El archivo no tiene la columna 'MES'.")
            return pd.DataFrame()
            
    return df

# Ejecutar carga
df = load_data(uploaded_file)

# Detener si no hay datos
if df.empty:
    st.info("👋 ¡Hola! Para empezar, sube tu archivo Excel/CSV en el menú de la izquierda o verifica la conexión a internet.")
    st.stop()

# --- TÍTULO PRINCIPAL ---
st.title("🛡️ App de Gestión SST - Tablero de Control")
st.markdown(f"**Última actualización:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# --- FILTROS SIDEBAR ---
st.sidebar.header("Filtrar Datos")
if not df.empty:
    years = sorted(df['MES'].dt.year.unique(), reverse=True)
    year_sel = st.sidebar.selectbox("Seleccionar Año", years, index=0)
    
    # Filtrar el DataFrame
    df_filtered = df[df['MES'].dt.year == year_sel]
else:
    df_filtered = df

# --- CÁLCULO DE KPIs ---
total_acc = df_filtered['ACCIDENTES'].sum()
dias_perdidos = df_filtered['Días perdidos'].sum()
actos_ins = df_filtered['ACTOS INSEGUROS'].sum()
cond_ins = df_filtered['CONDICIONES INSEGURAS'].sum()

# Calcular días sin accidentes
try:
    if 'Fecha del ultimo accidente' in df_filtered.columns and not df_filtered.empty:
        last_acc_date = pd.to_datetime(df_filtered['Fecha del ultimo accidente'].iloc[-1])
        dias_sin_acc = (datetime.now() - last_acc_date).days
    else:
        dias_sin_acc = "N/A"
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
    if not df_filtered.empty:
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=df_filtered['MES'], y=df_filtered['Indice de Frecuencia'], 
                        mode='lines+markers', name='Frecuencia', line=dict(color='orange')))
        fig_line.add_trace(go.Scatter(x=df_filtered['MES'], y=df_filtered['Indice de severidad'], 
                        mode='lines+markers', name='Severidad', line=dict(color='red')))
        fig_line.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_line, use_container_width=True)

with c2:
    st.subheader("🔍 Actos vs Condiciones")
    if not df_filtered.empty:
        labels = ['Actos Inseguros', 'Condiciones Inseguras']
        values = [actos_ins, cond_ins]
        fig_pie = px.pie(names=labels, values=values, hole=0.4, color_discrete_sequence=['#FFA726', '#EF5350'])
        fig_pie.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

# Fila 2: Barras de Gestión
st.subheader("📊 Gestión Preventiva (Planificado vs Ejecutado)")
c3, c4 = st.columns(2)

with c3:
    if not df_filtered.empty:
        fig_insp = go.Figure(data=[
            go.Bar(name='Programadas', x=df_filtered['MES'], y=df_filtered['INSPECCIONES PROGRAMADAS'], marker_color='#E0E0E0'),
            go.Bar(name='Ejecutadas', x=df_filtered['MES'], y=df_filtered['INSPECCIONES EJECUTADAS'], marker_color='#66BB6A')
        ])
        fig_insp.update_layout(title="Inspecciones", barmode='group', height=300)
        st.plotly_chart(fig_insp, use_container_width=True)

with c4:
    if not df_filtered.empty:
        fig_cap = go.Figure(data=[
            go.Bar(name='Programadas', x=df_filtered['MES'], y=df_filtered['CAPACITACIONES PROGRAMADAS'], marker_color='#E0E0E0'),
            go.Bar(name='Ejecutadas', x=df_filtered['MES'], y=df_filtered['CAPACITACIONES EJECUTUDAS'], marker_color='#42A5F5')
        ])
        fig_cap.update_layout(title="Capacitaciones", barmode='group', height=300)
        st.plotly_chart(fig_cap, use_container_width=True)

# --- TABLA DE DATOS ---
with st.expander("📂 Ver Base de Datos Completa"):
    if not df_filtered.empty:
        # Formateo condicional para que se vea bonito
        st.dataframe(df_filtered.style.format({
            'Indice de Frecuencia': '{:.2f}',
            'Indice de severidad': '{:.2f}',
            # Agregar aquí más columnas si quieres formato específico
        }))
