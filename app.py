import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
import shutil
from fpdf import FPDF
from io import BytesIO
import numpy as np

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="SST - Maderas Galvez", layout="wide", page_icon="🌲")

# --- 2. GESTIÓN DE DATOS Y ARCHIVOS ---
CSV_FILE = "base_datos_galvez_v11.csv"
LOGO_FILE = "logo_empresa_persistente.png"
MESES_ORDEN = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

def get_structure_for_year(year):
    data = []
    for m in MESES_ORDEN:
        data.append({
            'Año': int(year), 'Mes': m,
            'Masa Laboral': 100.0, 'Horas Extras': 0.0, 'Horas Ausentismo': 0.0,
            'Accidentes CTP': 0.0, 'Días Perdidos': 0.0, 'Días Cargo': 0.0,
            'Insp. Programadas': 10.0, 'Insp. Ejecutadas': 8.0,
            'Cap. Programadas': 5.0, 'Cap. Ejecutadas': 5.0,
            'Medidas Abiertas': 5.0, 'Medidas Cerradas': 4.0,
            'Expuestos Silice/Ruido': 10.0, 'Vig. Salud Vigente': 10.0,
            'Observaciones': "Sin novedades.",
            'HHT': 18000.0, 'Tasa Acc.': 0.0, 'Tasa Sin.': 0.0, 'Indice Frec.': 0.0, 'Indice Grav.': 0.0
        })
    return pd.DataFrame(data)

def inicializar_db_completa():
    df_24 = get_structure_for_year(2024)
    df_25 = get_structure_for_year(2025)
    df_26 = get_structure_for_year(2026)
    return pd.concat([df_24, df_25, df_26], ignore_index=True)

def procesar_datos(df):
    # 1. Limpieza estricta de números
    cols_num = df.columns.drop(['Año', 'Mes', 'Observaciones'])
    for col in cols_num:
        # Convierte a numérico, errores a NaN, luego NaN a 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # 2. Limpieza de textos
    df['Año'] = df['Año'].fillna(2026).astype(int)
    if 'Observaciones' not in df.columns: 
        df['Observaciones'] = ""
    df['Observaciones'] = df['Observaciones'].fillna("").astype(str)

    # 3. Cálculos
    df['HHT'] = (df['Masa Laboral'] * 180) + df['Horas Extras'] - df['Horas Ausentismo']
    # Evitar división por cero poniendo 1 si es 0
    df['HHT'] = df['HHT'].apply(lambda x: x if x > 0 else 1)
    masa = df['Masa Laboral'].apply(lambda x: x if x > 0 else 1)
    
    df['Tasa Acc.'] = (df['Accidentes CTP'] / masa) * 100
    df['Tasa Sin.'] = (df['Días Perdidos'] / masa) * 100
    df['Indice Frec.'] = (df['Accidentes CTP'] * 1000000) / df['HHT']
    df['Indice Grav.'] = ((df['Días Perdidos'] + df['Días Cargo']) * 1000000) / df['HHT']
    
    return df

def load_data():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            if df.empty: return inicializar_db_completa()
            
            # Reparar columnas faltantes
            ref = get_structure_for_year(2026)
            for col in ref.columns:
                if col not in df.columns: 
                    if col == 'Observaciones': df[col] = ""
                    else: df[col] = 0
            
            return procesar_datos(df)
        except: return inicializar_db_completa()
    return inicializar_db_completa()

def save_data(df):
    df_calc = procesar_datos(df)
    # Backup de seguridad
    if os.path.exists(CSV_FILE):
        try: shutil.copy(CSV_FILE, f"{CSV_FILE}.bak")
        except: pass
    df_calc.to_csv(CSV_FILE, index=False)
    return df_calc

def generar_insight_automatico(row_mes, ta_acum, metas):
    insights = []
    if ta_acum > metas['meta_ta']:
        insights.append(f"⚠️ <b>ALERTA:</b> Tasa Acumulada ({ta_acum:.2f}%) sobre la meta.")
    elif ta_acum > (metas['meta_ta'] * 0.8):
        insights.append(f"🔸 <b>PRECAUCIÓN:</b> Tasa Acumulada al límite.")
    else:
        insights.append(f"✅ <b>EXCELENTE:</b> Accidentabilidad bajo control.")
    
    if row_mes['Tasa Sin.'] > 0:
        insights.append(f"🚑 <b>SINIESTRALIDAD:</b> {int(row_mes['Días Perdidos'])} días perdidos.")
    
    if not insights: return "Desempeño normal."
    return "<br>".join(insights)

if 'df_main' not in st.session_state:
    st.session_state['df_main'] = load_data()

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.title("🌲 Panel de Control")
    st.markdown("### 🖼️ Imagen Corporativa")
    uploaded_logo = st.file_uploader("Actualizar Logo", type=['png', 'jpg'])
    if uploaded_logo:
        with open(LOGO_FILE, "wb") as f: f.write(uploaded_logo.getbuffer())
        st.success("Logo actualizado."); st.rerun()
    
    if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📅 Gestión de Años")
    
    years_present = st.session_state['df_main']['Año'].unique()
    if 2025 not in years_present:
        if st.button("⚠️ Activar Año 2025"):
            df_new = get_structure_for_year(2025)
            st.session_state['df_main'] = pd.concat([st.session_state['df_main'], df_new], ignore_index=True)
            save_data(st.session_state['df_main']); st.rerun()
            
    new_year_input = st.number_input("Agregar Año:", min_value=2000, max_value=2050, value=2024)
    if st.button("➕ Crear Año"):
        if new_year_input in years_present: st.warning("Año ya existe.")
        else:
            df_new = get_structure_for_year(new_year_input)
            st.session_state['df_main'] = pd.concat([st.session_state['df_main'], df_new], ignore_index=True)
            save_data(st.session_state['df_main']); st.success("Creado."); st.rerun()

    st.markdown("---")
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='SST_Data')
        return output.getvalue()
    
    excel_data = to_excel(st.session_state['df_main'])
    st.download_button("📊 Descargar Excel", data=excel_data, file_name="Base_SST_Completa.xlsx")

    st.markdown("---")
    meta_ta = st.slider("Meta Tasa Acc. (%)", 0.0, 5.0, 3.0)
    meta_gestion = st.slider("Meta Gestión (%)", 50, 100, 90)
    metas = {'meta_ta': meta_ta, 'meta_gestion': meta_gestion}

# --- 4. MOTOR PDF BLINDADO ---
class PDF_SST(FPDF):
    def header(self):
        if os.path.exists(LOGO_FILE): self.image(LOGO_FILE, 10, 8, 40)
        self.set_xy(55, 12); self.set_font('Arial', 'B', 14)
        self.cell(0, 6, 'SOCIEDAD MADERERA GALVEZ Y DI GENOVA LTDA', 0, 1, 'L')
        self.set_xy(55, 19); self.set_font('Arial', 'B', 11); self.set_text_color(100)
        self.cell(0, 6, 'SISTEMA DE GESTIÓN EN SST DS44', 0, 1, 'L')
        self.set_draw_color(183, 28, 28); self.set_line_width(0.5)
        self.line(10, 32, 285, 32); self.ln(15)

    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8); self.set_text_color(128)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def section_title(self, title):
        self.set_font('Arial', 'B', 10); self.set_fill_color(240); self.set_text_color(0)
        self.cell(0, 8, title, 1, 1, 'L', 1); self.ln(4)

    def kpi_row(self, label, val_mes, val_acum, unit):
        # Función de seguridad para evitar "None"
        def safe_fmt(val):
            try:
                if pd.isna(val) or val is None: return "0.00"
                return f"{float(val):.2f}"
            except: return "0.00"
            
        def safe_int(val):
            try:
                if pd.isna(val) or val is None: return "0"
                return f"{int(val)}"
            except: return "0"

        # Detectar si es entero o float para formato
        v_m = safe_int(val_mes) if "N" in unit or "Dias" in unit else safe_fmt(val_mes)
        v_a = safe_int(val_acum) if "N" in unit or "Dias" in unit else safe_fmt(val_acum)

        self.set_font('Arial', '', 10); self.cell(70, 8, label, 1)
        self.set_font('Arial', 'B', 10); self.cell(40, 8, v_m, 1, 0, 'C')
        self.set_text_color(183, 28, 28); self.cell(40, 8, v_a, 1, 0, 'C')
        self.set_text_color(0); self.set_font('Arial', 'I', 9); self.cell(40, 8, unit, 1, 1, 'C')

# --- 5. DASHBOARD ---
df = st.session_state['df_main']
tab_dash, tab_editor = st.tabs(["📊 DASHBOARD INTELIGENTE", "📝 EDITOR DE DATOS"])

years = sorted(df['Año'].unique(), reverse=True)
if not years: years = [2026]

with tab_dash:
    c1, c2 = st.columns([1, 4])
    with c1:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=160)
    with c2:
        st.title("SOCIEDAD MADERERA GALVEZ Y DI GENOVA LTDA")
        st.markdown("### SISTEMA DE GESTIÓN EN SST DS44")

    col_y, col_m = st.columns(2)
    sel_year = col_y.selectbox("Año Fiscal", years)
    
    df_year = df[df['Año'] == sel_year].copy()
    df_year['Mes_Idx'] = df_year['Mes'].apply(lambda x: MESES_ORDEN.index(x) if x in MESES_ORDEN else 99)
    df_year = df_year.sort_values('Mes_Idx')
    months_avail = df_year['Mes'].tolist()
    
    if not months_avail: st.warning("Año sin datos."); st.stop()
    sel_month = col_m.selectbox("Mes de Cierre", months_avail, index=len(months_avail)-1 if months_avail else 0)
    
    row_mes = df_year[df_year['Mes'] == sel_month].iloc[0]
    idx_corte = MESES_ORDEN.index(sel_month)
    df_acum = df_year[df_year['Mes_Idx'] <= idx_corte]
    
    sum_acc = df_acum['Accidentes CTP'].sum()
    sum_dias = df_acum['Días Perdidos'].sum()
    sum_hht = df_acum['HHT'].sum()
    avg_masa = df_acum['Masa Laboral'].mean()
    
    ta_acum = (sum_acc / avg_masa * 100) if avg_masa > 0 else 0
    ts_acum = (sum_dias / avg_masa * 100) if avg_masa > 0 else 0
    if_acum = (sum_acc * 1000000 / sum_hht) if sum_hht > 0 else 0
    ig_acum = ((sum_dias + df_acum['Días Cargo'].sum()) * 1000000 / sum_hht) if sum_hht > 0 else 0
    
    def safe_div(a, b): return (a/b*100) if b > 0 else 0
    p_insp = safe_div(row_mes['Insp. Ejecutadas'], row_mes['Insp. Programadas'])
    p_cap = safe_div(row_mes['Cap. Ejecutadas'], row_mes['Cap. Programadas'])
    p_medidas = safe_div(row_mes['Medidas Cerradas'], row_mes['Medidas Abiertas']) if row_mes['Medidas Abiertas']>0 else 100
    p_salud = safe_div(row_mes['Vig. Salud Vigente'], row_mes['Expuestos Silice/Ruido']) if row_mes['Expuestos Silice/Ruido']>0 else 100

    insight_text = generar_insight_automatico(row_mes, ta_acum, metas)
    st.info("💡 **ANÁLISIS INTELIGENTE:**")
    st.markdown(f"<div style='background-color:#e3f2fd; padding:10px; border-radius:5px;'>{insight_text}</div>", unsafe_allow_html=True)
    st.markdown("---")

    # KPIs
    st.markdown(f"#### 🔵 INDICADORES DEL MES ({sel_month})")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tasa Accidentabilidad", f"{row_mes['Tasa Acc.']:.2f}%")
    k2.metric("Tasa Siniestralidad", f"{row_mes['Tasa Sin.']:.2f}")
    k3.metric("Indice Frecuencia", f"{row_mes['Indice Frec.']:.2f}")
    k4.metric("Indice Gravedad", f"{row_mes['Indice Grav.']:.0f}")

    st.markdown(f"#### 🔴 ACUMULADO ANUAL ({sel_year})")
    a1, a2, a3, a4 = st.columns(4)
    delta_col = "normal" if ta_acum <= metas['meta_ta'] else "inverse"
    a1.metric("T. Acc. Acumulada", f"{ta_acum:.2f}%", f"Meta: {metas['meta_ta']}%", delta_color=delta_col)
    a2.metric("T. Sin. Acumulada", f"{ts_acum:.2f}")
    a3.metric("I. Frec. Acumulado", f"{if_acum:.2f}")
    a4.metric("I. Grav. Acumulado", f"{ig_acum:.0f}")

    st.markdown("#### 📋 Gestión")
    g1, g2, g3, g4 = st.columns(4)
    def donut(val, title):
        color = "#66BB6A" if val >= metas['meta_gestion'] else "#EF5350"
        fig = go.Figure(go.Pie(values=[val, 100-val], hole=0.7, marker_colors=[color, '#eee'], textinfo='none'))
        fig.update_layout(height=120, margin=dict(t=0,b=0,l=0,r=0), annotations=[dict(text=f"{val:.0f}%", x=0.5, y=0.5, font_size=16, showarrow=False)])
        st.markdown(f"<div style='text-align:center; font-size:13px;'>{title}</div>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, key=title)

    with g1: donut(p_insp, "Inspecciones")
    with g2: donut(p_cap, "Capacitaciones")
    with g3: donut(p_medidas, "Hallazgos")
    with g4: donut(p_salud, "Salud")

    # PDF
    st.markdown("---")
    if st.button("📄 Generar Reporte PDF"):
        pdf = PDF_SST(orientation='P', format='A4')
        pdf.add_page(); pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"PERIODO: {sel_month.upper()} {sel_year}", 0, 1, 'L'); pdf.ln(2)
        
        pdf.section_title("1. INDICADORES RESULTADO")
        pdf.set_fill_color(220); pdf.set_font('Arial', 'B', 9)
        pdf.cell(70, 8, "INDICADOR", 1, 0, 'C', 1); pdf.cell(40, 8, "MES", 1, 0, 'C', 1)
        pdf.cell(40, 8, "ACUMULADO", 1, 0, 'C', 1); pdf.cell(40, 8, "UNIDAD", 1, 1, 'C', 1)
        
        # Uso de datos crudos (se formatean dentro de kpi_row)
        pdf.kpi_row("Tasa Accidentabilidad", row_mes['Tasa Acc.'], ta_acum, "%")
        pdf.kpi_row("Tasa Siniestralidad", row_mes['Tasa Sin.'], ts_acum, "Dias/Trab")
        pdf.kpi_row("Indice Frecuencia", row_mes['Indice Frec.'], if_acum, "Acc/1M HHT")
        pdf.kpi_row("Indice Gravedad", row_mes['Indice Grav.'], ig_acum, "Dias/1M HHT")
        pdf.kpi_row("Total Accidentes CTP", row_mes['Accidentes CTP'], sum_acc, "N Eventos")
        pdf.kpi_row("Total Dias Perdidos", row_mes['Días Perdidos'], sum_dias, "Dias")
        pdf.ln(5)
        
        pdf.section_title("2. GESTIÓN OPERATIVA")
        data_gest = [("Inspecciones", p_insp), ("Capacitaciones", p_cap), ("Cierre Hallazgos", p_medidas), ("Salud Ocup.", p_salud)]
        for l, v in data_gest:
            pdf.cell(80, 8, l, 0); x=pdf.get_x(); y=pdf.get_y()
            pdf.set_fill_color(230); pdf.rect(x, y+2, 80, 4, 'F')
            pdf.set_fill_color(76, 175, 80) if v >= metas['meta_gestion'] else pdf.set_fill_color(244, 67, 54)
            pdf.rect(x, y+2, (v/100)*80, 4, 'F')
            pdf.set_x(x+85); pdf.cell(20, 8, f"{v:.0f}%", 0, 1)

        pdf.ln(5); pdf.section_title("3. OBSERVACIONES")
        pdf.set_font('Arial', '', 10); pdf.set_draw_color(100)
        clean_insight = insight_text.replace("<b>","").replace("</b>","").replace("<br>","\n").replace("⚠️","").replace("✅","").replace("🚑","")
        
        # Limpieza estricta de Observaciones
        obs = str(row_mes['Observaciones'])
        if obs.lower() in ["nan", "none", "0", "0.0", ""]: obs = "Sin observaciones registradas para este periodo."
        
        pdf.multi_cell(0, 6, f"ANALISIS SISTEMA:\n{clean_insight}\n\nCOMENTARIOS EXPERTO:\n{obs}", 1, 'L')
        
        pdf.ln(15); pdf.line(110, pdf.get_y(), 190, pdf.get_y())
        pdf.set_xy(110, pdf.get_y()+2); pdf.set_font('Arial', 'B', 8)
        pdf.cell(80, 5, "Firma Experto", 0, 0, 'C')
        
        out = pdf.output(dest='S').encode('latin-1')
        st.download_button("📥 Descargar", out, f"Reporte_{sel_month}_{sel_year}.pdf", "application/pdf")

with tab_editor:
    st.subheader("📝 Carga de Datos")
    c_y, c_m = st.columns(2)
    edit_year = c_y.selectbox("Año:", years, key="ed_y")
    
    months_in_year = df[df['Año'] == edit_year]['Mes'].tolist()
    months_in_year.sort(key=lambda x: MESES_ORDEN.index(x) if x in MESES_ORDEN else 99)
    edit_month = c_m.selectbox("Mes:", months_in_year, key="ed_m")
    
    try:
        row_idx = df.index[(df['Año'] == edit_year) & (df['Mes'] == edit_month)].tolist()[0]
        
        with st.form("edit_form"):
            st.info(f"Editando: **{edit_month} {edit_year}**")
            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1:
                st.markdown("##### 👷 Datos")
                val_masa = st.number_input("Masa Laboral", value=float(df.at[row_idx, 'Masa Laboral']))
                val_extras = st.number_input("Horas Extras", value=float(df.at[row_idx, 'Horas Extras']))
                val_aus = st.number_input("Horas Ausentismo", value=float(df.at[row_idx, 'Horas Ausentismo']))
            with col_e2:
                st.markdown("##### 🚑 Siniestralidad")
                val_acc = st.number_input("Accidentes CTP", value=float(df.at[row_idx, 'Accidentes CTP']))
                val_dias = st.number_input("Días Perdidos", value=float(df.at[row_idx, 'Días Perdidos']))
                val_cargo = st.number_input("Días Cargo", value=float(df.at[row_idx, 'Días Cargo']))
            with col_e3:
                st.markdown("##### 📋 Gestión")
                val_insp_p = st.number_input("Insp. Prog", value=float(df.at[row_idx, 'Insp. Programadas']))
                val_insp_e = st.number_input("Insp. Ejec", value=float(df.at[row_idx, 'Insp. Ejecutadas']))
                val_cap_p = st.number_input("Cap. Prog", value=float(df.at[row_idx, 'Cap. Programadas']))
                val_cap_e = st.number_input("Cap. Ejec", value=float(df.at[row_idx, 'Cap. Ejecutadas']))
                val_med_ab = st.number_input("Hallazgos", value=float(df.at[row_idx, 'Medidas Abiertas']))
                val_med_ce = st.number_input("Cerrados", value=float(df.at[row_idx, 'Medidas Cerradas']))
                val_exp = st.number_input("Expuestos", value=float(df.at[row_idx, 'Expuestos Silice/Ruido']))
                val_vig = st.number_input("Vigilancia", value=float(df.at[row_idx, 'Vig. Salud Vigente']))

            st.markdown("##### 📝 Observaciones")
            # Cargar observación limpia
            curr_obs = str(df.at[row_idx, 'Observaciones'])
            if curr_obs.lower() in ["nan", "none", "0", "0.0"]: curr_obs = ""
            val_obs = st.text_area("Texto del Reporte:", value=curr_obs, height=100)

            if st.form_submit_button("💾 GUARDAR CAMBIOS"):
                df.at[row_idx, 'Masa Laboral'] = val_masa
                df.at[row_idx, 'Horas Extras'] = val_extras
                df.at[row_idx, 'Horas Ausentismo'] = val_aus
                df.at[row_idx, 'Accidentes CTP'] = val_acc
                df.at[row_idx, 'Días Perdidos'] = val_dias
                df.at[row_idx, 'Días Cargo'] = val_cargo
                df.at[row_idx, 'Insp. Programadas'] = val_insp_p
                df.at[row_idx, 'Insp. Ejecutadas'] = val_insp_e
                df.at[row_idx, 'Cap. Programadas'] = val_cap_p
                df.at[row_idx, 'Cap. Ejecutadas'] = val_cap_e
                df.at[row_idx, 'Medidas Abiertas'] = val_med_ab
                df.at[row_idx, 'Medidas Cerradas'] = val_med_ce
                df.at[row_idx, 'Expuestos Silice/Ruido'] = val_exp
                df.at[row_idx, 'Vig. Salud Vigente'] = val_vig
                df.at[row_idx, 'Observaciones'] = val_obs
                
                st.session_state['df_main'] = save_data(df)
                st.success("Guardado.")
                st.rerun()
    except: st.error("Seleccione un Año/Mes válido.")
