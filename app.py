import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from fpdf import FPDF
import io

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Dashboard SST", layout="wide", page_icon="⛑️")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- CLASE PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Reporte de Gestion SST', 0, 1, 'C')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def create_pdf(dataframe, kpis):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=f"Fecha reporte: {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt="Resumen de Indicadores", ln=True)
    pdf.set_font("Arial", size=12)
    for key, value in kpis.items():
        clean_key = key.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 10, f"{clean_key}: {value}", ln=True)
    pdf.ln(10)
    return pdf.output(dest='S').encode('latin-1')

# --- 1. GESTIÓN DE ESTADO (Session State) ---
# Esto es vital para que los datos manuales no desaparezcan al tocar un botón
if 'data_main' not in st.session_state:
    st.session_state['data_main'] = pd.DataFrame()

# --- 2. BARRA LATERAL: CARGA Y DESCARGA ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3050/3050523.png", width=80)
st.sidebar.title("Menú")

# A) Cargar Archivo
uploaded_file = st.sidebar.file_uploader("1. Cargar Excel/CSV (Base Inicial)", type=["csv", "xlsx"])

# Función de carga inicial (Solo corre si se sube archivo o está vacío)
def load_initial_data(file_uploaded):
    df = pd.DataFrame()
    if file_uploaded is not None:
        try:
            if file_uploaded.name.endswith('.csv'):
                df = pd.read_csv(file_uploaded)
            else:
                df = pd.read_excel(file_uploaded)
        except: return pd.DataFrame()
    else:
        # Intento cargar nube si no hay archivo
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSHnEKxzb-M3T0PjzyA1zPv_h-awqQ0og6imzQ5uHJG8wk85-WBBgtoCWC9FnusngmDw72kL88tduR3/pub?gid=1349054762&single=true&output=csv"
        try: df = pd.read_csv(url)
        except: return pd.DataFrame()

    if not df.empty:
        # Normalización de columnas
        df.columns = df.columns.str.strip()
        correcciones = {
            'Dias perdidos': 'Días perdidos', 'dias perdidos': 'Días perdidos',
            'Días Perdidos': 'Días perdidos', 'Accidentes': 'ACCIDENTES',
            'Actos Inseguros': 'ACTOS INSEGUROS', 'Condiciones Inseguras': 'CONDICIONES INSEGURAS',
            'Mes': 'MES', 'Marca temporal': 'Timestamp'
        }
        df = df.rename(columns=correcciones)
        if 'Timestamp' in df.columns: df = df.drop(columns=['Timestamp'])
        if 'Marca temporal' in df.columns: df = df.drop(columns=['Marca temporal'])
        if 'MES' in df.columns: df['MES'] = pd.to_datetime(df['MES'])
    
    return df

# Solo cargar si la sesión está vacía o si el usuario subió un archivo nuevo
if st.session_state['data_main'].empty or uploaded_file is not None:
    # Truco: Si ya cargamos manual, no sobrescribir a menos que el usuario suba archivo
    if uploaded_file is not None:
        st.session_state['data_main'] = load_initial_data(uploaded_file)
    elif st.session_state['data_main'].empty:
        st.session_state['data_main'] = load_initial_data(None)

df = st.session_state['data_main']

# Si sigue vacío tras intentar todo, parar
if df.empty:
    st.warning("Esperando datos... Sube un archivo o ingresa datos manualmente.")
    # No paramos (stop) para permitir el ingreso manual abajo

# --- 3. FORMULARIO DE INGRESO MANUAL ---
with st.expander("📝 INGRESAR DATOS UNO POR UNO (Manual)", expanded=False):
    st.info("Ingresa los datos del mes y haz clic en 'Agregar Registro'.")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    
    with col_f1:
        input_fecha = st.date_input("Fecha (Mes)", datetime.now())
        input_acc = st.number_input("Accidentes", min_value=0, value=0)
    with col_f2:
        input_dias = st.number_input("Días Perdidos", min_value=0, value=0)
        input_actos = st.number_input("Actos Inseguros", min_value=0, value=0)
    with col_f3:
        input_cond = st.number_input("Condiciones Inseguras", min_value=0, value=0)
        # Puedes agregar más inputs aquí si necesitas (ej. Horas trabajadas)
    
    if st.button("➕ Agregar Registro al Tablero"):
        new_row = {
            'MES': pd.to_datetime(input_fecha),
            'ACCIDENTES': input_acc,
            'Días perdidos': input_dias,
            'ACTOS INSEGUROS': input_actos,
            'CONDICIONES INSEGURAS': input_cond,
            # Valores por defecto para que no falle el gráfico
            'Indice de Frecuencia': 0, 
            'Indice de severidad': 0,
            'INSPECCIONES PROGRAMADAS': 0,
            'INSPECCIONES EJECUTADAS': 0,
            'CAPACITACIONES PROGRAMADAS': 0,
            'CAPACITACIONES EJECUTUDAS': 0
        }
        
        # Agregar a la sesión
        new_df = pd.DataFrame([new_row])
        st.session_state['data_main'] = pd.concat([st.session_state['data_main'], new_df], ignore_index=True)
        st.rerun() # Recargar la página para ver el cambio

# Actualizar referencia local después del posible ingreso manual
df = st.session_state['data_main']

if df.empty:
    st.stop()

# --- 4. TÍTULO Y FILTROS ---
st.title("🛡️ App de Gestión SST")
st.markdown("---")

# Filtro Año
if 'MES' in df.columns:
    years = sorted(df['MES'].dt.year.unique(), reverse=True)
    year_sel = st.sidebar.selectbox("Filtrar Año", years)
    df_filtered = df[df['MES'].dt.year == year_sel]
else:
    df_filtered = df

# --- 5. KPIs y GRÁFICOS ---
def safe_sum(col): return df_filtered[col].sum() if col in df_filtered.columns else 0

kpis = {
    "Total Accidentes": int(safe_sum('ACCIDENTES')),
    "Días Perdidos": int(safe_sum('Días perdidos')),
    "Actos Inseguros": int(safe_sum('ACTOS INSEGUROS')),
    "Condiciones Inseguras": int(safe_sum('CONDICIONES INSEGURAS'))
}

c1, c2, c3, c4 = st.columns(4)
c1.metric("🗓️ Días Perdidos", kpis["Días Perdidos"], delta_color="inverse")
c2.metric("🚑 Accidentes", kpis["Total Accidentes"], delta="Acumulado", delta_color="inverse")
c3.metric("⚠️ Actos Inseguros", kpis["Actos Inseguros"])
c4.metric("🏗️ Condiciones Inseguras", kpis["Condiciones Inseguras"])

st.markdown("---")

col_g1, col_g2 = st.columns([2, 1])

with col_g1:
    st.subheader("Tendencia de Accidentes")
    # Agrupar por mes para que si metes varios datos en un mes se sumen
    if not df_filtered.empty:
        df_chart = df_filtered.groupby('MES')[['ACCIDENTES', 'ACTOS INSEGUROS']].sum().reset_index()
        fig = px.bar(df_chart, x='MES', y=['ACCIDENTES', 'ACTOS INSEGUROS'], barmode='group')
        st.plotly_chart(fig, use_container_width=True)

with col_g2:
    st.subheader("Distribución")
    if kpis["Actos Inseguros"] + kpis["Condiciones Inseguras"] > 0:
        fig_pie = px.pie(values=[kpis["Actos Inseguros"], kpis["Condiciones Inseguras"]], 
                         names=['Actos', 'Condiciones'], hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

# --- 6. TABLA DE DATOS Y EXPORTACIÓN ---
st.subheader("📋 Base de Datos (Incluye agregados manuales)")
st.dataframe(df_filtered)

st.sidebar.markdown("---")
st.sidebar.header("💾 Exportar")

# B) Botón PDF
if st.sidebar.button("Generar PDF Reporte"):
    try:
        pdf_bytes = create_pdf(df_filtered, kpis)
        st.sidebar.download_button("📥 Bajar PDF", pdf_bytes, "reporte_sst.pdf", "application/pdf")
    except Exception as e: st.error(f"Error PDF: {e}")

# C) Botón Guardar Excel (IMPORTANTE PARA LO MANUAL)
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df(st.session_state['data_main'])
st.sidebar.download_button(
    label="💾 Guardar Base de Datos (CSV)",
    data=csv,
    file_name='base_datos_actualizada.csv',
    mime='text/csv',
    help="Descarga esto para guardar los datos manuales que ingresaste."
)
