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

# 1. Botón para subir archivo
st.sidebar.header("📂 Actualizar Datos")
uploaded_file = st.sidebar.file_uploader("Arrastra tu Excel o CSV aquí", type=["csv", "xlsx"])

st.sidebar.markdown("---")

# --- FUNCIÓN DE CARGA DE DATOS ---
@st.cache_data(ttl=60)
def load_data(file_uploaded):
    df = pd.DataFrame()
    
    # CASO A: Usuario sube un archivo
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
            
    # CASO B: Cargar desde la Nube (Google Sheets) si no hay archivo
    else:
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSHnEKxzb-M3T0PjzyA1zPv_h-awqQ0og6imzQ5uHJG8wk85-WBBgtoCWC9FnusngmDw72kL88tduR3/pub?gid=1349054762&single=true&output=csv"
        try:
            df = pd.read_csv(url)
        except Exception as e:
            st.warning("⚠️ No se pudo conectar a la nube y no has subido archivo.")
            return pd.DataFrame()

    # --- LIMPIEZA Y CORRECCIÓN DE NOMBRES (SOLUCIÓN AL ERROR) ---
    if not df.empty:
        # 1. Quitar espacios extra en los nombres de las columnas
        df.columns = df.columns.str.strip()
        
        # 2. Diccionario de corrección: Mapea como debería llamarse vs como podría venir
        # Esto soluciona el KeyError de tildes o mayúsculas
        correcciones = {
            'Dias perdidos': 'Días perdidos',
            'dias perdidos': 'Días perdidos',
            'Días Perdidos': 'Días perdidos',
            'DIAS PERDIDOS': 'Días perdidos',
            'Accidentes': 'ACCIDENTES',
            'Actos Inseguros': 'ACTOS INSEGUROS',
            'Condiciones Inseguras': 'CONDICIONES INSEGURAS',
            'Mes': 'MES',
            'Marca temporal': 'Timestamp'
        }
        df = df.rename(columns=correcciones)

        # 3. Eliminar columnas basura de Google Forms
        columnas_a_borrar = ['Timestamp', 'Marca temporal']
        for col in columnas_a_borrar:
            if col in df.columns:
                df = df.drop(columns=[col])
        
        # 4. Convertir MES a fecha
        if 'MES' in df.columns:
            df['MES'] = pd.to_datetime(df['MES'])
        else:
            st.error(f"⚠️ El archivo no tiene la columna 'MES'. Columnas detectadas: {list(df.columns)}")
            return pd.DataFrame()
            
    return df

# Ejecutar carga
df = load_data(uploaded_file)

# Si no hay datos, detener la app
if df.empty:
    st.info("👋 Sube tu archivo Excel/CSV para comenzar.")
    st.stop()

# --- TÍTULO PRINCIPAL ---
st.title("🛡️ App de Gestión SST - Tablero de Control")
st.markdown(f"**Última actualización:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# --- FILTROS ---
st.sidebar.header("Filtrar Datos")
years = sorted(df['MES'].dt.year.unique(), reverse=True)
year_sel = st.sidebar.selectbox("Seleccionar Año", years, index=0)

df_filtered = df[df['MES'].dt.year == year_sel]

# --- HELPER PARA SUMAS SEGURAS ---
# Esta función evita que la app se caiga si falta una columna
def get_sum(col_name):
    if col_name in df_filtered.columns:
        return df_filtered[col_name].sum()
    return 0

# --- CÁLCULO DE KPIs ---
total_acc = get_sum('ACCIDENTES')
dias_perdidos = get_sum('Días perdidos') # Ahora funcionará aunque venga sin tilde
actos_ins = get_sum('ACTOS INSEGUROS')
cond_ins = get_sum('CONDICIONES INSEGURAS')

# Calcular días sin accidentes
dias_sin_acc = "N/A"
if 'Fecha del ultimo accidente' in df_filtered.columns:
    try:
        last_acc_date = pd.to_datetime(df_filtered['Fecha del ultimo accidente'].iloc[-1])
        dias_sin_acc = (datetime.now() - last_acc_date).days
    except:
        pass

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
    st.subheader("📈 Evolución de Índices")
    # Verificamos si existen las columnas antes de graficar
    if 'Indice de Frecuencia' in df_filtered.columns and 'Indice de severidad' in df_filtered.columns:
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=df_filtered['MES'], y=df_filtered['Indice de Frecuencia'], 
                        mode='lines+markers', name='Frecuencia', line=dict(color='orange')))
        fig_line.add_trace(go.Scatter(x=df_filtered['MES'], y=df_filtered['Indice de severidad'], 
                        mode='lines+markers', name='Severidad', line=dict(color='red')))
        fig_line.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No se encontraron columnas de Índices para graficar.")

with c2:
    st.subheader("🔍 Actos vs Condiciones")
    labels = ['Actos Inseguros', 'Condiciones Inseguras']
    values = [actos_ins, cond_ins]
    if sum(values) > 0:
        fig_pie = px.pie(names=labels, values=values, hole=0.4, color_discrete_sequence=['#FFA726', '#EF5350'])
        fig_pie.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.write("Sin datos registrados.")

# Fila 2: Barras de Gestión
st.subheader("📊 Gestión Preventiva")
c3, c4 = st.columns(2)

# Función para graficar barras de forma segura
def plot_bar_chart(title, col_prog, col_ejec, color_bar):
    if col_prog in df_filtered.columns and col_ejec in df_filtered.columns:
        fig = go.Figure(data=[
            go.Bar(name='Programadas', x=df_filtered['MES'], y=df_filtered[col_prog], marker_color='#E0E0E0'),
            go.Bar(name='Ejecutadas', x=df_filtered['MES'], y=df_filtered[col_ejec], marker_color=color_bar)
        ])
        fig.update_layout(title=title, barmode='group', height=300)
        st.plotly_chart(fig, use_container_width=True)

with c3:
    plot_bar_chart("Inspecciones", 'INSPECCIONES PROGRAMADAS', 'INSPECCIONES EJECUTADAS', '#66BB6A')

with c4:
    plot_bar_chart("Capacitaciones", 'CAPACITACIONES PROGRAMADAS', 'CAPACITACIONES EJECUTUDAS', '#42A5F5')

# --- TABLA DE DATOS ---
with st.expander("📂 Ver Base de Datos Completa"):
    st.dataframe(df_filtered)
