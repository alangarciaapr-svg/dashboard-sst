import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="SST Chile - Mutualidades", layout="wide", page_icon="🇨🇱")

# --- 2. SISTEMA DE AUTO-GUARDADO (PERSISTENCIA) ---
CSV_FILE = "base_datos_sst.csv"

def cargar_datos():
    """Carga los datos del archivo CSV si existe, sino crea la estructura base."""
    if os.path.exists(CSV_FILE):
        try:
            return pd.read_csv(CSV_FILE)
        except:
            pass # Si falla, creamos uno nuevo
    
    # ESTRUCTURA DE DATOS SEGÚN MUTUALIDADES (DS 67 / DS 40)
    # Masa Laboral: Promedio de trabajadores en el mes.
    # CTP: Con Tiempo Perdido (Licencias).
    # Dias Cargo: Penalización por invalidez o muerte (DS 40).
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

def guardar_cambios(df):
    """Escribe los datos en el disco duro inmediatamente."""
    df.to_csv(CSV_FILE, index=False)

# Cargar datos al inicio
if 'df_sst' not in st.session_state:
    st.session_state['df_sst'] = cargar_datos()

# --- 3. ESTILOS VISUALES (LIMPIO Y PROFESIONAL) ---
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
    
    /* Colores Específicos Prevención */
    .border-red { border-left-color: #D32F2F !important; }
    .border-orange { border-left-color: #F57C00 !important; }
    .border-blue { border-left-color: #1976D2 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. INTERFAZ PRINCIPAL ---
st.title("🛡️ Panel de Control SST - Normativa Chilena")
st.markdown("Cálculos basados en **D.S. 67** (Siniestralidad Efectiva) y **D.S. 40** (Estadísticas Mensuales).")

tab_dashboard, tab_editor = st.tabs(["📊 DASHBOARD DE INDICADORES", "📝 PLANILLA DE DATOS (EDITABLE)"])

# ==============================================================================
# PESTAÑA 1: DASHBOARD (CÁLCULOS AUTOMÁTICOS MUTUALIDAD)
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
    
    # LÓGICA DE CÁLCULO ACUMULADO (AÑO A LA FECHA)
    masa_total = df_year['Masa Laboral (Trabajadores)'].mean() # El promedio anual
    hht_total = df_year['HHT (Horas Hombre)'].sum()
    acc_ctp_total = df_year['Accidentes CTP'].sum()
    dias_perdidos_total = df_year['Días Perdidos (Licencias)'].sum()
    dias_cargo_total = df_year['Días Cargo (Inv/Muerte)'].sum()
    
    # --- FÓRMULAS CHILENAS (EXPLICADAS) ---
    
    # 1. TASA DE ACCIDENTABILIDAD (DS 40 / Mutual)
    # Fórmula: (Total Accidentes / Promedio Trabajadores) * 100
    if masa_total > 0:
        tasa_acc = (acc_ctp_total / masa_total) * 100
        tasa_sin = (dias_perdidos_total / masa_total) * 100 # Tasa Siniestralidad DS67 (Aprox Mensual)
    else:
        tasa_acc = 0
        tasa_sin = 0
        
    # 2. ÍNDICES TÉCNICOS (Base 1.000.000 HHT)
    if hht_total > 0:
        ind_frec = (acc_ctp_total * 1000000) / hht_total
        # Para gravedad sumamos días perdidos + días cargo (Norma ANSI utilizada en Chile)
        ind_grav = ((dias_perdidos_total + dias_cargo_total) * 1000000) / hht_total
    else:
        ind_frec = 0
        ind_grav = 0

    # VISUALIZACIÓN DE KPIs
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

    kpi_card(k1, "TASA ACCIDENTABILIDAD", f"{tasa_acc:.2f}%", "Acc. CTP / Masa Promedio", "border-red")
    kpi_card(k2, "TASA SINIESTRALIDAD", f"{tasa_sin:.2f}", "Días / Masa Promedio", "border-orange")
    kpi_card(k3, "ÍNDICE FRECUENCIA", f"{ind_frec:.2f}", "Acc. CTP x 1M / HHT", "border-blue")
    kpi_card(k4, "ÍNDICE GRAVEDAD", f"{ind_grav:.0f}", "Días Totales x 1M / HHT", "border-blue")
    
    st.markdown("---")
    
    # GRÁFICOS
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("📉 Curva de Tasas Mensuales")
        # Calculamos tasa mes a mes para el gráfico
        df_year['Tasa_Acc_Mes'] = (df_year['Accidentes CTP'] / df_year['Masa Laboral (Trabajadores)']) * 100
        
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
        st.subheader("🚑 Composición de la Siniestralidad")
        values = [dias_perdidos_total, dias_cargo_total]
        labels = ['Días Licencias Médicas', 'Días Cargo (Inv/Muerte)']
        
        if sum(values) > 0:
            fig2 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, 
                                        marker_colors=['#F57C00', '#333333'])])
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sin días perdidos registrados en el periodo.")

# ==============================================================================
# PESTAÑA 2: EDITOR (EL CAMBIO CLAVE)
# ==============================================================================
with tab_editor:
    st.subheader("📝 Ingreso y Modificación de Datos")
    st.info("💡 **Auto-Guardado Activo:** Cualquier cambio que hagas aquí se guarda en el archivo 'base_datos_sst.csv' automáticamente. Puedes refrescar la página y tus datos seguirán aquí.")
    
    # Configuración de columnas para que se vea profesional
    column_config = {
        "Mes": st.column_config.SelectboxColumn(
            "Mes", options=['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'], required=True
        ),
        "Masa Laboral (Trabajadores)": st.column_config.NumberColumn("Masa Laboral", help="Promedio de trabajadores contratados en el mes", min_value=1),
        "HHT (Horas Hombre)": st.column_config.NumberColumn("HHT", help="Total horas trabajadas (aprox Masa * 45 * 4)", min_value=0),
        "Accidentes CTP": st.column_config.NumberColumn("Acc. CTP", help="Accidentes del Trabajo Con Tiempo Perdido"),
        "Accidentes Trayecto": st.column_config.NumberColumn("Trayecto", help="No se suman a la Tasa de Accidentabilidad, pero se llevan por control"),
        "Días Cargo (Inv/Muerte)": st.column_config.NumberColumn("Días Cargo", help="6000 por Muerte, 4500 ITP, etc.")
    }

    # EDITOR DE DATOS
    edited_df = st.data_editor(
        st.session_state['df_sst'],
        num_rows="dynamic",
        column_config=column_config,
        use_container_width=True,
        key="editor_principal"
    )

    # LÓGICA DE GUARDADO AUTOMÁTICO
    # Comparamos si el editado es diferente al guardado en sesión
    # Si es diferente, actualizamos sesión y GUARDAMOS EN DISCO
    if not edited_df.equals(st.session_state['df_sst']):
        st.session_state['df_sst'] = edited_df
        guardar_cambios(edited_df)
        st.toast("✅ Datos guardados en disco exitosamente", icon="💾")
        st.rerun() # Recargamos para refrescar gráficos
