import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
import io

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SST Chile - Mutualidades", layout="wide", page_icon="🇨🇱")

# --- 2. SISTEMA DE AUTO-GUARDADO (CON AUTOREPARACIÓN) ---
CSV_FILE = "base_datos_sst.csv"

def crear_estructura_nueva():
    """Crea la estructura de datos correcta según Norma Chilena."""
    return pd.DataFrame({
        'Año': [2024],
        'Mes': ['Enero'],
        'Masa Laboral (Trabajadores)': [100],
        'HHT (Horas Hombre)': [18000],
        'Accidentes CTP': [0],
        'Accidentes Trayecto': [0],
        'Días Perdidos (Licencias)': [0],
        'Días Cargo (Inv/Muerte)': [0]
    })

def cargar_datos():
    """Carga datos y REPARA el archivo si tiene columnas viejas."""
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            
            # --- CORRECCIÓN DE ERROR KEYERROR ---
            # Verificamos si existe la columna clave nueva. Si no existe, es un archivo viejo.
            if 'Masa Laboral (Trabajadores)' not in df.columns:
                st.toast("⚠️ Formato antiguo detectado. Actualizando estructura de datos...", icon="bUpdate")
                # Si quieres intentar salvar datos viejos, podrías renombrar, 
                # pero para empezar limpio y sin errores, recreamos la estructura:
                return crear_estructura_nueva()
            
            return df
        except Exception as e:
            # Si el archivo está corrupto, creamos uno nuevo
            return crear_estructura_nueva()
    else:
        return crear_estructura_nueva()

def guardar_cambios(df):
    """Escribe los datos en el disco duro inmediatamente."""
    df.to_csv(CSV_FILE, index=False)

# Cargar datos al inicio
if 'df_sst' not in st.session_state:
    st.session_state['df_sst'] = cargar_datos()

# --- 3. ESTILOS VISUALES ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    .kpi-card {
        background-color: white; border-left: 5px solid #666;
        padding: 15px; border-radius: 5px; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
    }
    .kpi-title { font-size: 14px; font-weight: bold; color: #555; text-transform: uppercase;}
    .kpi-value { font-size: 28px; font-weight: bold; color: #222; }
    .kpi-sub { font-size: 12px; color: #888; font-style: italic; }
    
    .border-red { border-left-color: #D32F2F !important; }
    .border-orange { border-left-color: #F57C00 !important; }
    .border-blue { border-left-color: #1976D2 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. INTERFAZ PRINCIPAL ---
st.title("🛡️ Panel de Control SST - Normativa Chilena")
st.markdown("Cálculos basados en **D.S. 67** (Siniestralidad Efectiva) y **D.S. 40**.")

# Botón de emergencia para borrar todo si algo falla
with st.sidebar:
    st.markdown("### 🛠️ Opciones Avanzadas")
    if st.button("⚠️ Reiniciar Base de Datos a Cero"):
        df_reset = crear_estructura_nueva()
        st.session_state['df_sst'] = df_reset
        guardar_cambios(df_reset)
        st.rerun()

tab_dashboard, tab_editor = st.tabs(["📊 DASHBOARD DE INDICADORES", "📝 PLANILLA DE DATOS (EDITABLE)"])

# ==============================================================================
# PESTAÑA 1: DASHBOARD
# ==============================================================================
with tab_dashboard:
    df = st.session_state['df_sst']
    
    # Filtros
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        years = sorted(df['Año'].unique(), reverse=True)
        sel_year = st.selectbox("Seleccionar Año", years)
    
    # Filtrar por año
    df_year = df[df['Año'] == sel_year]
    
    # CÁLCULOS
    masa_total = df_year['Masa Laboral (Trabajadores)'].mean() 
    hht_total = df_year['HHT (Horas Hombre)'].sum()
    acc_ctp_total = df_year['Accidentes CTP'].sum()
    dias_perdidos_total = df_year['Días Perdidos (Licencias)'].sum()
    dias_cargo_total = df_year['Días Cargo (Inv/Muerte)'].sum()
    
    # Fórmulas
    if masa_total > 0:
        tasa_acc = (acc_ctp_total / masa_total) * 100
        tasa_sin = (dias_perdidos_total / masa_total) * 100 
    else:
        tasa_acc = 0; tasa_sin = 0
        
    if hht_total > 0:
        ind_frec = (acc_ctp_total * 1000000) / hht_total
        ind_grav = ((dias_perdidos_total + dias_cargo_total) * 1000000) / hht_total
    else:
        ind_frec = 0; ind_grav = 0

    # KPIs
    st.markdown("### 📌 Indicadores Acumulados (Año en Curso)")
    k1, k2, k3, k4 = st.columns(4)
    
    def kpi_card(col, title, value, sub, color):
        col.markdown(f"""
        <div class="kpi-card {color}">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """, unsafe_allow_html=True)

    kpi_card(k1, "TASA ACCIDENTABILIDAD", f"{tasa_acc:.2f}%", "Acc. CTP / Masa Prom.", "border-red")
    kpi_card(k2, "TASA SINIESTRALIDAD", f"{tasa_sin:.2f}", "Días / Masa Prom.", "border-orange")
    kpi_card(k3, "ÍNDICE FRECUENCIA", f"{ind_frec:.2f}", "Acc. CTP x 1M / HHT", "border-blue")
    kpi_card(k4, "ÍNDICE GRAVEDAD", f"{ind_grav:.0f}", "Días Totales x 1M / HHT", "border-blue")
    
    st.markdown("---")
    
    # GRÁFICOS
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("📉 Evolución Mensual")
        # Calculamos tasa mes a mes para visualización
        # Evitamos división por cero
        df_year['Tasa_Acc_Mes'] = df_year.apply(lambda x: (x['Accidentes CTP']/x['Masa Laboral (Trabajadores)']*100) if x['Masa Laboral (Trabajadores)'] > 0 else 0, axis=1)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_year['Mes'], y=df_year['Tasa_Acc_Mes'], 
                                mode='lines+markers', name='Tasa Accidentabilidad',
                                line=dict(color='#D32F2F', width=3)))
        fig.add_trace(go.Bar(x=df_year['Mes'], y=df_year['Accidentes CTP'], 
                             name='Nº Accidentes', opacity=0.3, yaxis='y2'))
        
        fig.update_layout(yaxis=dict(title='Tasa (%)'),
                          yaxis2=dict(title='Nº Eventos', overlaying='y', side='right'),
                          legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    with g2:
        st.subheader("🚑 Siniestralidad")
        values = [dias_perdidos_total, dias_cargo_total]
        labels = ['Días Licencias', 'Días Cargo']
        if sum(values) > 0:
            fig2 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker_colors=['#F57C00', '#333333'])])
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sin días perdidos registrados.")

# ==============================================================================
# PESTAÑA 2: EDITOR
# ==============================================================================
with tab_editor:
    st.subheader("📝 Ingreso y Modificación de Datos")
    st.info("💡 **Auto-Guardado:** Tus cambios se guardan automáticamente al editar.")
    
    column_config = {
        "Mes": st.column_config.SelectboxColumn("Mes", options=['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'], required=True),
        "Masa Laboral (Trabajadores)": st.column_config.NumberColumn("Masa Laboral", min_value=1),
        "HHT (Horas Hombre)": st.column_config.NumberColumn("HHT", min_value=0),
        "Accidentes CTP": st.column_config.NumberColumn("Acc. CTP"),
        "Accidentes Trayecto": st.column_config.NumberColumn("Trayecto"),
        "Días Cargo (Inv/Muerte)": st.column_config.NumberColumn("Días Cargo")
    }

    edited_df = st.data_editor(
        st.session_state['df_sst'],
        num_rows="dynamic",
        column_config=column_config,
        use_container_width=True,
        key="editor_principal"
    )

    if not edited_df.equals(st.session_state['df_sst']):
        st.session_state['df_sst'] = edited_df
        guardar_cambios(edited_df)
        st.rerun()
