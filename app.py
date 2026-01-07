import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# --- 1. CONFIGURACIÓN INICIAL DE LA APP ---
st.set_page_config(
    page_title="Sistema de Gestión SST",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

# --- 2. GESTIÓN DE ESTADO (MEMORIA TEMPORAL) ---
# Inicializamos la base de datos vacía si no existe
if 'df_sst' not in st.session_state:
    # Estructura PROFESIONAL de datos para Prevención de Riesgos
    data_structure = {
        'Fecha': [datetime.today().date()],
        'Mes': ['Enero'],
        'Año': [2024],
        'Dotación (Trabajadores)': [100],
        'Horas Hombre (HHT)': [18000],
        'Accidentes CTP': [0], # Con Tiempo Perdido
        'Accidentes STP': [0], # Sin Tiempo Perdido
        'Días Perdidos': [0],
        'Actos Inseguros': [0],
        'Condiciones Inseguras': [0],
        'Insp. Programadas': [10],
        'Insp. Ejecutadas': [10],
        'Cap. Programadas': [5],
        'Cap. Ejecutadas': [5]
    }
    st.session_state['df_sst'] = pd.DataFrame(data_structure)

# --- 3. BARRA LATERAL (CONTROL) ---
st.sidebar.title("🛡️ Panel de Control")
st.sidebar.markdown("---")

# Carga de respaldo (Para no perder datos al cerrar)
uploaded_file = st.sidebar.file_uploader("📂 Cargar Respaldo (Excel/CSV)", type=["xlsx", "csv"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_loaded = pd.read_csv(uploaded_file)
        else:
            df_loaded = pd.read_excel(uploaded_file)
        
        # Convertir columna Fecha a datetime para evitar errores
        if 'Fecha' in df_loaded.columns:
            df_loaded['Fecha'] = pd.to_datetime(df_loaded['Fecha']).dt.date
            
        st.session_state['df_sst'] = df_loaded
        st.sidebar.success("✅ Datos cargados correctamente")
    except Exception as e:
        st.sidebar.error(f"Error al cargar: {e}")

st.sidebar.markdown("### 💾 Guardar Avance")
st.sidebar.info("⚠️ La app se reinicia si cierras la pestaña. Descarga tus datos regularmente.")

# Botón de descarga universal
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

csv_data = convert_df(st.session_state['df_sst'])
st.sidebar.download_button(
    "📥 Descargar Base de Datos (CSV)",
    csv_data,
    "Respaldo_SST.csv",
    "text/csv"
)

# --- 4. INTERFAZ PRINCIPAL (PESTAÑAS) ---
st.title("🛡️ Dashboard Integral de Prevención de Riesgos")
tab1, tab2 = st.tabs(["📝 INGRESO Y EDICIÓN DE DATOS", "📊 DASHBOARD Y REPORTES"])

# ==========================================
# PESTAÑA 1: EDITOR DE DATOS (TIPO EXCEL)
# ==========================================
with tab1:
    st.subheader("Base de Datos Maestra")
    st.markdown("Edita directamente las celdas, agrega filas al final o borra seleccionando la izquierda.")
    
    # EL CORAZÓN DE LA APP: st.data_editor
    # Esto permite editar la tabla como si fuera un Excel
    edited_df = st.data_editor(
        st.session_state['df_sst'],
        num_rows="dynamic", # Permite agregar/borrar filas
        use_container_width=True,
        column_config={
            "Fecha": st.column_config.DateColumn("Fecha de Cierre", format="DD/MM/YYYY"),
            "Horas Hombre (HHT)": st.column_config.NumberColumn("HHT", help="Horas Hombre Trabajadas Totales"),
            "Accidentes CTP": st.column_config.NumberColumn("Acc. CTP", help="Con Tiempo Perdido"),
            "Accidentes STP": st.column_config.NumberColumn("Acc. STP", help="Sin Tiempo Perdido"),
        },
        key="editor_sst" # Clave única
    )
    
    # Actualizar la sesión con los cambios
    st.session_state['df_sst'] = edited_df
    
    # Métricas rápidas de la base de datos
    st.caption(f"Registros totales: {len(edited_df)} | Última actualización: {datetime.now().strftime('%H:%M:%S')}")

# ==========================================
# PESTAÑA 2: DASHBOARD (VISUALIZACIÓN)
# ==========================================
with tab2:
    # 1. Preparación de Datos
    df = st.session_state['df_sst'].copy()
    
    # Filtros
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        years = sorted(df['Año'].unique(), reverse=True)
        sel_year = st.selectbox("Seleccionar Año", years)
    
    # Filtrar DF
    df_filtered = df[df['Año'] == sel_year]
    
    if df_filtered.empty:
        st.warning("No hay datos para el año seleccionado.")
        st.stop()

    # 2. CÁLCULO DE ÍNDICES NORMATIVOS (Standard OSHA / ISO / Local)
    # IF = (Accidentes CTP * 1.000.000) / HHT
    # IS = (Días Perdidos * 1.000.000) / HHT
    
    total_acc_ctp = df_filtered['Accidentes CTP'].sum()
    total_dias = df_filtered['Días Perdidos'].sum()
    total_hht = df_filtered['Horas Hombre (HHT)'].sum()
    
    if total_hht > 0:
        if_anual = (total_acc_ctp * 1000000) / total_hht
        is_anual = (total_dias * 1000000) / total_hht
    else:
        if_anual = 0
        is_anual = 0

    # 3. KPIs PRINCIPALES (Header)
    st.markdown("### 📈 Indicadores Globales (Acumulado Anual)")
    k1, k2, k3, k4 = st.columns(4)
    
    k1.metric("Accidentes CTP", int(total_acc_ctp), delta="Eventos Críticos", delta_color="inverse")
    k2.metric("Días Perdidos", int(total_dias), delta="Severidad", delta_color="inverse")
    k3.metric("Índice Frecuencia (IF)", f"{if_anual:.2f}", help="Accidentes CTP por millón de horas")
    k4.metric("Índice Severidad (IS)", f"{is_anual:.2f}", help="Días perdidos por millón de horas")
    
    st.markdown("---")

    # 4. GRÁFICOS DE GESTIÓN
    row1_1, row1_2 = st.columns(2)
    
    with row1_1:
        st.subheader("📊 Cumplimiento de Programa (Preventivo)")
        # Sumas para gráficos
        insp_prog = df_filtered['Insp. Programadas'].sum()
        insp_ejec = df_filtered['Insp. Ejecutadas'].sum()
        cap_prog = df_filtered['Cap. Programadas'].sum()
        cap_ejec = df_filtered['Cap. Ejecutadas'].sum()
        
        # Calcular %
        perc_insp = (insp_ejec / insp_prog * 100) if insp_prog > 0 else 0
        perc_cap = (cap_ejec / cap_prog * 100) if cap_prog > 0 else 0
        
        fig_cumplimiento = go.Figure(data=[
            go.Bar(name='Programado', x=['Inspecciones', 'Capacitaciones'], y=[insp_prog, cap_prog], marker_color='#E0E0E0'),
            go.Bar(name='Ejecutado', x=['Inspecciones', 'Capacitaciones'], y=[insp_ejec, cap_ejec], marker_color='#00B050')
        ])
        fig_cumplimiento.update_layout(title=f"Cumplimiento: Insp ({perc_insp:.0f}%) | Cap ({perc_cap:.0f}%)")
        st.plotly_chart(fig_cumplimiento, use_container_width=True)

    with row1_2:
        st.subheader("⚠️ Hallazgos: Actos vs Condiciones")
        # Datos mensuales para línea de tendencia
        # Agrupamos por Mes para asegurar orden
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=df_filtered['Mes'], y=df_filtered['Actos Inseguros'], name='Actos', line=dict(color='#FFC000', width=3)))
        fig_trend.add_trace(go.Scatter(x=df_filtered['Mes'], y=df_filtered['Condiciones Inseguras'], name='Condiciones', line=dict(color='#002060', width=3)))
        fig_trend.update_layout(title="Tendencia de Hallazgos")
        st.plotly_chart(fig_trend, use_container_width=True)

    # 5. ANÁLISIS MENSUAL DETALLADO
    st.markdown("---")
    st.subheader("🔍 Detalle Mensual de Índices")
    
    # Calcular IF e IS por mes para graficar
    df_filtered['IF_Mes'] = (df_filtered['Accidentes CTP'] * 1000000) / df_filtered['Horas Hombre (HHT)']
    df_filtered['IS_Mes'] = (df_filtered['Días Perdidos'] * 1000000) / df_filtered['Horas Hombre (HHT)']
    # Limpiar divisiones por cero
    df_filtered = df_filtered.fillna(0)

    fig_indices = go.Figure()
    fig_indices.add_trace(go.Bar(x=df_filtered['Mes'], y=df_filtered['IF_Mes'], name='Indice Frecuencia', marker_color='#5B9BD5'))
    fig_indices.add_trace(go.Scatter(x=df_filtered['Mes'], y=df_filtered['IS_Mes'], name='Indice Severidad (Línea)', yaxis='y2', line=dict(color='red')))
    
    fig_indices.update_layout(
        title="Evolución IF vs IS",
        yaxis=dict(title="Frecuencia"),
        yaxis2=dict(title="Severidad", overlaying='y', side='right')
    )
    st.plotly_chart(fig_indices, use_container_width=True)
