import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from fpdf import FPDF
import tempfile

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Dashboard SST", layout="wide", page_icon="⛑️")

# --- CLASE PARA GENERAR EL PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Reporte Mensual de Gestion SST', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def create_pdf(dataframe, year_selected, kpis):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # 1. Título y Fecha
    pdf.cell(200, 10, txt=f"Periodo Reportado: {year_selected}", ln=True, align='L')
    pdf.cell(200, 10, txt=f"Fecha de emision: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='L')
    pdf.ln(10)
    
    # 2. Resumen de KPIs (Sección Destacada)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Resumen de Indicadores (KPIs)", ln=True)
    pdf.set_font("Arial", size=12)
    
    # Dibujar una "caja" simple con texto para los KPIs
    for key, value in kpis.items():
        # Limpieza simple de caracteres para evitar errores en PDF básico
        clean_key = key.encode('latin-1', 'replace').decode('latin-1') 
        pdf.cell(0, 10, f"{clean_key}: {value}", ln=True)
        
    pdf.ln(10)

    # 3. Tabla de Datos
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Detalle de Registros Mensuales", ln=True)
    pdf.set_font("Arial", size=10)
    
    # Cabeceras de tabla (Simplificado para que quepa)
    cols_to_print = ['MES', 'ACCIDENTES', 'Días perdidos', 'ACTOS INSEGUROS']
    
    # Encabezado
    for col in cols_to_print:
        # Ajuste ancho columnas
        pdf.cell(45, 10, str(col)[:15], 1)
    pdf.ln()
    
    # Filas
    pdf.set_font("Arial", size=10)
    for index, row in dataframe.iterrows():
        try:
            # Formatear fecha
            fecha = row['MES'].strftime('%Y-%m-%d') if pd.notnull(row['MES']) else ""
            pdf.cell(45, 10, fecha, 1)
            pdf.cell(45, 10, str(row.get('ACCIDENTES', 0)), 1)
            pdf.cell(45, 10, str(row.get('Días perdidos', 0)), 1)
            pdf.cell(45, 10, str(row.get('ACTOS INSEGUROS', 0)), 1)
            pdf.ln()
        except:
            continue
            
    return pdf.output(dest='S').encode('latin-1')

# --- BARRA LATERAL: CARGA DE DATOS ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3050/3050523.png", width=100)
st.sidebar.title("Configuración")

uploaded_file = st.sidebar.file_uploader("Arrastra tu Excel o CSV aquí", type=["csv", "xlsx"])

# --- FUNCIÓN DE CARGA DE DATOS ---
@st.cache_data(ttl=60)
def load_data(file_uploaded):
    df = pd.DataFrame()
    if file_uploaded is not None:
        try:
            if file_uploaded.name.endswith('.csv'):
                df = pd.read_csv(file_uploaded)
            else:
                df = pd.read_excel(file_uploaded)
            st.toast("✅ Datos cargados desde archivo", icon="📂")
        except Exception as e:
            st.error(f"Error: {e}")
            return pd.DataFrame()
    else:
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSHnEKxzb-M3T0PjzyA1zPv_h-awqQ0og6imzQ5uHJG8wk85-WBBgtoCWC9FnusngmDw72kL88tduR3/pub?gid=1349054762&single=true&output=csv"
        try:
            df = pd.read_csv(url)
        except:
            st.warning("⚠️ No se pudo conectar a la nube.")
            return pd.DataFrame()

    if not df.empty:
        df.columns = df.columns.str.strip()
        correcciones = {
            'Dias perdidos': 'Días perdidos', 'dias perdidos': 'Días perdidos',
            'Días Perdidos': 'Días perdidos', 'DIAS PERDIDOS': 'Días perdidos',
            'Accidentes': 'ACCIDENTES', 'Actos Inseguros': 'ACTOS INSEGUROS',
            'Condiciones Inseguras': 'CONDICIONES INSEGURAS', 'Mes': 'MES'
        }
        df = df.rename(columns=correcciones)
        
        # Borrar columnas basura
        for c in ['Timestamp', 'Marca temporal']:
            if c in df.columns: df = df.drop(columns=[c])
            
        if 'MES' in df.columns:
            df['MES'] = pd.to_datetime(df['MES'])
        else:
            return pd.DataFrame()
            
    return df

df = load_data(uploaded_file)

if df.empty:
    st.info("👋 Sube tu archivo para comenzar.")
    st.stop()

# --- TÍTULO ---
st.title("🛡️ App de Gestión SST")
st.markdown(f"**Actualizado:** {datetime.now().strftime('%d/%m/%Y')}")

# --- FILTROS ---
st.sidebar.markdown("---")
st.sidebar.header("Filtros")
years = sorted(df['MES'].dt.year.unique(), reverse=True)
year_sel = st.sidebar.selectbox("Seleccionar Año", years, index=0)
df_filtered = df[df['MES'].dt.year == year_sel]

# --- CÁLCULOS KPI ---
def get_sum(col): return df_filtered[col].sum() if col in df_filtered.columns else 0

total_acc = int(get_sum('ACCIDENTES'))
dias_perdidos = int(get_sum('Días perdidos'))
actos_ins = int(get_sum('ACTOS INSEGUROS'))
cond_ins = int(get_sum('CONDICIONES INSEGURAS'))

# Calcular días sin accidentes
dias_sin_acc = "N/A"
if 'Fecha del ultimo accidente' in df_filtered.columns:
    try:
        last_acc_date = pd.to_datetime(df_filtered['Fecha del ultimo accidente'].iloc[-1])
        dias_sin_acc = (datetime.now() - last_acc_date).days
    except: pass

# --- VISUALIZACIÓN KPIs ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("🗓️ Días sin Accidentes", f"{dias_sin_acc}")
c2.metric("🚑 Accidentes", total_acc, delta_color="inverse")
c3.metric("⚠️ Actos Inseguros", actos_ins)
c4.metric("🏗️ Condiciones Inseguras", cond_ins)

st.markdown("---")

# --- GRÁFICOS ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 Índices")
    if 'Indice de Frecuencia' in df_filtered.columns:
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=df_filtered['MES'], y=df_filtered['Indice de Frecuencia'], name='Frecuencia'))
        fig_line.add_trace(go.Scatter(x=df_filtered['MES'], y=df_filtered['Indice de severidad'], name='Severidad'))
        fig_line.update_layout(height=300, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_line, use_container_width=True)

with col2:
    st.subheader("🔍 Actos vs Cond.")
    if actos_ins + cond_ins > 0:
        fig_pie = px.pie(names=['Actos', 'Condiciones'], values=[actos_ins, cond_ins], hole=0.4)
        fig_pie.update_layout(height=300, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_pie, use_container_width=True)

# --- BOTÓN DE DESCARGA PDF (NUEVO) ---
st.sidebar.markdown("---")
st.sidebar.header("🖨️ Exportar")

# Preparar datos para el PDF
kpis_reporte = {
    "Total Accidentes": total_acc,
    "Dias Perdidos": dias_perdidos,
    "Actos Inseguros": actos_ins,
    "Condiciones Inseguras": cond_ins,
    "Dias sin Accidentes": dias_sin_acc
}

# Botón Generador
if st.sidebar.button("Generar PDF"):
    try:
        pdf_bytes = create_pdf(df_filtered, year_sel, kpis_reporte)
        st.sidebar.download_button(
            label="💾 Descargar PDF Ahora",
            data=pdf_bytes,
            file_name=f"Reporte_SST_{year_sel}.pdf",
            mime="application/pdf"
        )
        st.toast("PDF Generado exitosamente", icon="✅")
    except Exception as e:
        st.error(f"Error generando PDF: {e}")

# --- TABLA ---
with st.expander("📂 Ver Datos"):
    st.dataframe(df_filtered)
