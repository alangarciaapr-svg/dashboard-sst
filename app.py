import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
from fpdf import FPDF

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="SST - Maderas Galvez", layout="wide", page_icon="🌲")

# --- 2. GESTIÓN DE DATOS ---
CSV_FILE = "base_datos_galvez_pro.csv"

def get_structure():
    return pd.DataFrame({
        'Año': [2026], 'Mes': ['Enero'],
        # DATOS BASE
        'Masa Laboral': [100.0], 'Horas Extras': [0.0], 'Horas Ausentismo': [0.0],
        'Accidentes CTP': [0.0], 'Días Perdidos': [0.0], 'Días Cargo': [0.0],
        # GESTIÓN
        'Insp. Programadas': [10.0], 'Insp. Ejecutadas': [8.0],
        'Cap. Programadas': [5.0], 'Cap. Ejecutadas': [5.0],
        'Medidas Abiertas': [5.0], 'Medidas Cerradas': [4.0],
        'Expuestos Silice/Ruido': [10.0], 'Vig. Salud Vigente': [10.0],
        'Observaciones': ["Sin novedades relevantes."],
        # CALCULADOS
        'HHT': [18000.0], 'Tasa Acc.': [0.0], 'Tasa Sin.': [0.0],
        'Indice Frec.': [0.0], 'Indice Grav.': [0.0]
    })

def procesar_datos(df):
    cols_num = df.columns.drop(['Año', 'Mes', 'Observaciones'])
    for col in cols_num:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    if 'Observaciones' not in df.columns: df['Observaciones'] = ""

    df['HHT'] = (df['Masa Laboral'] * 180) + df['Horas Extras'] - df['Horas Ausentismo']
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
            ref = get_structure()
            for col in ref.columns:
                if col not in df.columns: 
                    if col == 'Observaciones': df[col] = ""
                    else: df[col] = 0
            return procesar_datos(df)
        except: return get_structure()
    return get_structure()

def save_data(df):
    df_calc = procesar_datos(df)
    df_calc.to_csv(CSV_FILE, index=False)
    return df_calc

# --- NUEVA FUNCIÓN: INTELIGENCIA AUTOMÁTICA ---
def generar_insight_automatico(row_mes, ta_acum, metas):
    insights = []
    
    # Análisis Accidentabilidad
    if ta_acum > metas['meta_ta']:
        insights.append(f"⚠️ <b>ALERTA CRÍTICA:</b> La Tasa Acumulada ({ta_acum:.2f}%) supera la meta establecida del {metas['meta_ta']}%. Se requiere plan de acción inmediato.")
    elif ta_acum > (metas['meta_ta'] * 0.8):
        insights.append(f"🔸 <b>PRECAUCIÓN:</b> La Tasa Acumulada está acercándose al límite ({ta_acum:.2f}%).")
    else:
        insights.append(f"✅ <b>EXCELENTE:</b> La accidentabilidad ({ta_acum:.2f}%) está bajo control y dentro de la meta.")

    # Análisis Gestión
    insp_cumpl = (row_mes['Insp. Ejecutadas'] / row_mes['Insp. Programadas'] * 100) if row_mes['Insp. Programadas'] > 0 else 0
    if insp_cumpl < metas['meta_gestion']:
        insights.append(f"📉 <b>GESTIÓN:</b> El cumplimiento de Inspecciones ({insp_cumpl:.0f}%) está bajo el estándar del {metas['meta_gestion']}%.")
    
    # Análisis Siniestralidad
    if row_mes['Tasa Sin.'] > 0:
        insights.append(f"🚑 <b>SINIESTRALIDAD:</b> Este mes se registraron {int(row_mes['Días Perdidos'])} días perdidos, impactando la productividad.")

    if not insights:
        return "El desempeño del mes se encuentra dentro de los parámetros normales."
    
    return "<br>".join(insights)

if 'df_main' not in st.session_state:
    st.session_state['df_main'] = load_data()

# --- 3. BARRA LATERAL (CON MEJORAS) ---
with st.sidebar:
    st.title("🌲 Configuración Pro")
    uploaded_logo = st.file_uploader("Subir Logo", type=['png', 'jpg'])
    logo_path = "logo_temp.png"
    if uploaded_logo:
        with open(logo_path, "wb") as f: f.write(uploaded_logo.getbuffer())
    
    st.markdown("---")
    st.markdown("### 🎯 Definición de Metas (KPIs)")
    meta_ta = st.slider("Meta Tasa Accidentabilidad (%)", 0.0, 5.0, 3.0, 0.1)
    meta_gestion = st.slider("Meta Cumplimiento Gestión (%)", 50, 100, 90, 5)
    
    metas = {'meta_ta': meta_ta, 'meta_gestion': meta_gestion}

    st.markdown("---")
    if st.button("♻️ Reiniciar Sistema"):
        save_data(get_structure())
        st.rerun()

# --- 4. MOTOR PDF ---
class PDF_SST(FPDF):
    def header(self):
        if os.path.exists(logo_path): self.image(logo_path, 10, 8, 40)
        self.set_xy(55, 12)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 6, 'SOCIEDAD MADERERA GALVEZ Y DI GENOVA LTDA', 0, 1, 'L')
        self.set_xy(55, 19)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, 'SISTEMA DE GESTIÓN EN SST DS44', 0, 1, 'L')
        self.set_draw_color(183, 28, 28)
        self.set_line_width(0.5)
        self.line(10, 32, 285, 32)
        self.ln(15)

    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8); self.set_text_color(128)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def section_title(self, title):
        self.set_font('Arial', 'B', 10); self.set_fill_color(240, 240, 240); self.set_text_color(0, 0, 0)
        self.cell(0, 8, title, 1, 1, 'L', 1); self.ln(4)

    def kpi_row(self, label, val_mes, val_acum, unit):
        self.set_font('Arial', '', 10)
        self.cell(70, 8, label, 1)
        self.set_font('Arial', 'B', 10)
        self.cell(40, 8, f"{val_mes}", 1, 0, 'C')
        self.set_text_color(183, 28, 28) 
        self.cell(40, 8, f"{val_acum}", 1, 0, 'C')
        self.set_text_color(0, 0, 0); self.set_font('Arial', 'I', 9)
        self.cell(40, 8, unit, 1, 1, 'C')

# --- 5. DASHBOARD ---
df = st.session_state['df_main']
tab_dash, tab_editor = st.tabs(["📊 DASHBOARD INTELIGENTE", "📝 EDITOR DATOS"])

# Prep Datos
years = sorted(df['Año'].unique(), reverse=True)
curr_year = years[0] if len(years)>0 else 2026
df_year = df[df['Año'] == curr_year].copy()
m_order = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
df_year['Mes_Idx'] = df_year['Mes'].apply(lambda x: m_order.index(x) if x in m_order else 99)
df_year = df_year.sort_values('Mes_Idx')
months_avail = df_year['Mes'].tolist()

with tab_dash:
    c1, c2 = st.columns([1, 4])
    with c1:
        if os.path.exists(logo_path): st.image(logo_path, width=160)
    with c2:
        st.title("SOCIEDAD MADERERA GALVEZ Y DI GENOVA LTDA")
        st.markdown("### SISTEMA DE GESTIÓN EN SST DS44")

    col_y, col_m = st.columns(2)
    sel_year = col_y.selectbox("Año Fiscal", years)
    sel_month = col_m.selectbox("Mes de Cierre", months_avail, index=len(months_avail)-1 if months_avail else 0)
    
    # CÁLCULOS
    row_mes = df_year[df_year['Mes'] == sel_month].iloc[0]
    idx_corte = m_order.index(sel_month)
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

    # --- MEJORA 1: TARJETA DE INTELIGENCIA AUTOMÁTICA ---
    insight_text = generar_insight_automatico(row_mes, ta_acum, metas)
    st.info("💡 **ANÁLISIS INTELIGENTE DEL PERIODO:**")
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 5px solid #007bff;">
        {insight_text}
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # KPIs
    st.markdown(f"#### 🔵 INDICADORES DEL MES ({sel_month})")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tasa Accidentabilidad", f"{row_mes['Tasa Acc.']:.2f}%")
    k2.metric("Tasa Siniestralidad", f"{row_mes['Tasa Sin.']:.2f}")
    k3.metric("Indice Frecuencia", f"{row_mes['Indice Frec.']:.2f}")
    k4.metric("Indice Gravedad", f"{row_mes['Indice Grav.']:.0f}")

    st.markdown(f"#### 🔴 ACUMULADO DS67 (Enero - {sel_month})")
    a1, a2, a3, a4 = st.columns(4)
    # --- MEJORA 2: USO DE DELTA DINÁMICO SEGÚN META CONFIGURABLE ---
    delta_color = "normal" if ta_acum <= metas['meta_ta'] else "inverse"
    a1.metric("T. Acc. Acumulada", f"{ta_acum:.2f}%", f"Meta: {metas['meta_ta']}%", delta_color=delta_color)
    a2.metric("T. Sin. Acumulada", f"{ts_acum:.2f}", delta="Legal DS67", delta_color="off")
    a3.metric("I. Frec. Acumulado", f"{if_acum:.2f}")
    a4.metric("I. Grav. Acumulado", f"{ig_acum:.0f}")

    st.markdown("---")
    st.markdown("#### 📋 Gestión Depto SST")
    g1, g2, g3, g4 = st.columns(4)
    def donut(val, title, color):
        fig = go.Figure(go.Pie(values=[val, 100-val], hole=0.7, marker_colors=[color, '#eee'], textinfo='none'))
        fig.update_layout(height=120, margin=dict(t=0,b=0,l=0,r=0), annotations=[dict(text=f"{val:.0f}%", x=0.5, y=0.5, font_size=16, showarrow=False)])
        st.markdown(f"<div style='text-align:center; font-size:13px;'>{title}</div>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, key=title)

    # Colores dinámicos según meta de gestión
    c_insp = "#66BB6A" if p_insp >= metas['meta_gestion'] else "#EF5350"
    c_cap = "#66BB6A" if p_cap >= metas['meta_gestion'] else "#EF5350"

    with g1: donut(p_insp, "Plan Inspecciones", c_insp)
    with g2: donut(p_cap, "Plan Capacitaciones", c_cap)
    with g3: donut(p_medidas, "Cierre Hallazgos", "#FFA726")
    with g4: donut(p_salud, "Salud Ocupacional", "#AB47BC")

    # PDF
    st.markdown("---")
    if st.button("📄 Generar Reporte Completo PDF"):
        pdf = PDF_SST(orientation='P', format='A4')
        pdf.add_page()
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"PERIODO DE EVALUACIÓN: {sel_month.upper()} {sel_year}", 0, 1, 'L')
        pdf.ln(2)
        
        # TABLA
        pdf.section_title("1. INDICADORES DE RESULTADO")
        pdf.set_fill_color(220, 220, 220); pdf.set_font('Arial', 'B', 9)
        pdf.cell(70, 8, "INDICADOR", 1, 0, 'C', 1); pdf.cell(40, 8, "MES ACTUAL", 1, 0, 'C', 1)
        pdf.cell(40, 8, "ACUMULADO DS67", 1, 0, 'C', 1); pdf.cell(40, 8, "UNIDAD", 1, 1, 'C', 1)
        
        pdf.kpi_row("Tasa Accidentabilidad", f"{row_mes['Tasa Acc.']:.2f}", f"{ta_acum:.2f}", "%")
        pdf.kpi_row("Tasa Siniestralidad", f"{row_mes['Tasa Sin.']:.2f}", f"{ts_acum:.2f}", "Dias/Trab")
        pdf.kpi_row("Indice Frecuencia", f"{row_mes['Indice Frec.']:.2f}", f"{if_acum:.2f}", "Acc/1M HHT")
        pdf.kpi_row("Total Accidentes CTP", int(row_mes['Accidentes CTP']), int(sum_acc), "N Eventos")
        pdf.ln(8)
        
        # GESTIÓN
        pdf.section_title("2. GESTIÓN OPERATIVA SST")
        pdf.set_font('Arial', '', 10)
        data_gest = [("Cumplimiento Inspecciones", p_insp), ("Cumplimiento Capacitaciones", p_cap),
                     ("Eficacia Cierre Hallazgos", p_medidas), ("Cobertura Vigilancia Salud", p_salud)]
        
        for label, val in data_gest:
            pdf.cell(80, 8, label, 0)
            x = pdf.get_x(); y = pdf.get_y()
            pdf.set_fill_color(230, 230, 230); pdf.rect(x, y+2, 80, 4, 'F')
            if val >= metas['meta_gestion']: pdf.set_fill_color(76, 175, 80)
            elif val >= (metas['meta_gestion']-20): pdf.set_fill_color(255, 152, 0)
            else: pdf.set_fill_color(244, 67, 54)
            w_fill = (val/100)*80
            pdf.rect(x, y+2, w_fill, 4, 'F')
            pdf.set_x(x + 85)
            pdf.cell(20, 8, f"{val:.0f}%", 0, 1)

        # OBSERVACIONES + INSIGHT AUTOMATICO EN PDF
        pdf.ln(10)
        pdf.section_title("3. OBSERVACIONES Y CONCLUSIONES")
        pdf.set_font('Arial', '', 10)
        pdf.set_draw_color(100, 100, 100)
        
        # Limpiamos tags HTML para el PDF
        insight_clean = insight_text.replace("<b>", "").replace("</b>", "").replace("<br>", "\n").replace("⚠️", "").replace("✅", "").replace("📉", "")
        
        obs_text = str(row_mes['Observaciones'])
        if obs_text == "0" or obs_text == "nan" or obs_text == "": obs_text = "Sin observaciones manuales."
        
        final_text = f"ANÁLISIS AUTOMÁTICO:\n{insight_clean}\n\nOBSERVACIONES EXPERTO:\n{obs_text}"
        pdf.multi_cell(0, 6, final_text, 1, 'L')
        
        # Firma
        pdf.ln(20)
        pdf.line(110, pdf.get_y(), 190, pdf.get_y())
        pdf.set_xy(110, pdf.get_y()+2)
        pdf.set_font('Arial', 'B', 8)
        pdf.cell(80, 5, "Firma Experto en Prevención", 0, 0, 'C')

        out = pdf.output(dest='S').encode('latin-1')
        st.download_button("📥 Descargar Informe Profesional", out, f"Reporte_SST_{sel_month}.pdf", "application/pdf")

with tab_editor:
    st.subheader("📝 Carga de Datos y Observaciones")
    edit_month = st.selectbox("Seleccionar Mes para Editar:", months_avail, key="editor_selector")
    row_idx = df.index[df['Mes'] == edit_month].tolist()[0]
    
    with st.form("edit_form"):
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            st.markdown("##### 👷 Datos Laborales")
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
            val_insp_p = st.number_input("Insp. Programadas", value=float(df.at[row_idx, 'Insp. Programadas']))
            val_insp_e = st.number_input("Insp. Ejecutadas", value=float(df.at[row_idx, 'Insp. Ejecutadas']))
            val_cap_p = st.number_input("Cap. Programadas", value=float(df.at[row_idx, 'Cap. Programadas']))
            val_cap_e = st.number_input("Cap. Ejecutadas", value=float(df.at[row_idx, 'Cap. Ejecutadas']))
            val_med_ab = st.number_input("Medidas Abiertas", value=float(df.at[row_idx, 'Medidas Abiertas']))
            val_med_ce = st.number_input("Medidas Cerradas", value=float(df.at[row_idx, 'Medidas Cerradas']))
            val_exp = st.number_input("Expuestos Silice/Ruido", value=float(df.at[row_idx, 'Expuestos Silice/Ruido']))
            val_vig = st.number_input("Vigilancia Vigente", value=float(df.at[row_idx, 'Vig. Salud Vigente']))

        st.markdown("##### 📝 Observaciones (Manuales)")
        curr_obs = df.at[row_idx, 'Observaciones']
        if pd.isna(curr_obs) or curr_obs == 0: curr_obs = ""
        val_obs = st.text_area("Conclusiones del experto:", value=str(curr_obs), height=100)

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
