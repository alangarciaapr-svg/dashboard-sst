import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
import shutil
from fpdf import FPDF
from io import BytesIO

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="SST - Maderas Galvez", layout="wide", page_icon="🌲")

# --- 2. GESTIÓN DE DATOS ---
CSV_FILE = "base_datos_galvez_v14.csv"
LOGO_FILE = "logo_empresa_persistente.png"
MESES_ORDEN = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

def get_structure_for_year(year):
    data = []
    for m in MESES_ORDEN:
        data.append({
            'Año': int(year), 'Mes': m,
            'Masa Laboral': 0.0, 'Horas Extras': 0.0, 'Horas Ausentismo': 0.0,
            'Accidentes CTP': 0.0, 'Días Perdidos': 0.0, 'Días Cargo': 0.0,
            'Insp. Programadas': 0.0, 'Insp. Ejecutadas': 0.0,
            'Cap. Programadas': 0.0, 'Cap. Ejecutadas': 0.0,
            'Medidas Abiertas': 0.0, 'Medidas Cerradas': 0.0,
            'Expuestos Silice/Ruido': 0.0, 'Vig. Salud Vigente': 0.0,
            'Observaciones': "",
            'HHT': 0.0, 'Tasa Acc.': 0.0, 'Tasa Sin.': 0.0, 'Indice Frec.': 0.0, 'Indice Grav.': 0.0
        })
    return pd.DataFrame(data)

def inicializar_db_completa():
    df_24 = get_structure_for_year(2024)
    df_25 = get_structure_for_year(2025)
    df_26 = get_structure_for_year(2026)
    return pd.concat([df_24, df_25, df_26], ignore_index=True)

def procesar_datos(df):
    cols_num = df.columns.drop(['Año', 'Mes', 'Observaciones'])
    for col in cols_num:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df['Año'] = df['Año'].fillna(2026).astype(int)
    if 'Observaciones' not in df.columns: df['Observaciones'] = ""
    df['Observaciones'] = df['Observaciones'].fillna("").astype(str)

    # CÁLCULOS
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
            if df.empty: return inicializar_db_completa()
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
    if os.path.exists(CSV_FILE):
        try: shutil.copy(CSV_FILE, f"{CSV_FILE}.bak")
        except: pass
    df_calc.to_csv(CSV_FILE, index=False)
    return df_calc

def generar_insight_automatico(row_mes, ta_acum, metas):
    insights = []
    if ta_acum > metas['meta_ta']:
        insights.append(f"⚠️ <b>ALERTA:</b> Tasa Acumulada ({ta_acum:.2f}%) sobre la meta ({metas['meta_ta']}%)")
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
    st.markdown("### 📅 Años Fiscales")
    years_present = st.session_state['df_main']['Año'].unique()
    c_y1, c_y2 = st.columns(2)
    new_year_input = c_y1.number_input("Año", 2000, 2050, 2024)
    if c_y2.button("Crear Año"):
        if new_year_input in years_present: st.warning("Ya existe.")
        else:
            df_new = get_structure_for_year(new_year_input)
            st.session_state['df_main'] = pd.concat([st.session_state['df_main'], df_new], ignore_index=True)
            save_data(st.session_state['df_main']); st.rerun()

    st.markdown("---")
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            cols = ['Año','Mes','Masa Laboral','Accidentes CTP','Días Perdidos','HHT','Tasa Acc.','Tasa Sin.','Indice Frec.','Observaciones']
            all_cols = cols + [c for c in df.columns if c not in cols]
            df[all_cols].to_excel(writer, index=False, sheet_name='SST_Data')
        return output.getvalue()
    
    excel_data = to_excel(st.session_state['df_main'])
    st.download_button("📊 Descargar Excel", data=excel_data, file_name="Base_SST_Completa.xlsx")

    st.markdown("---")
    meta_ta = st.slider("Meta Tasa Acc. (%)", 0.0, 5.0, 3.0)
    meta_gestion = st.slider("Meta Gestión (%)", 50, 100, 90)
    metas = {'meta_ta': meta_ta, 'meta_gestion': meta_gestion}

# --- 4. MOTOR PDF ---
class PDF_SST(FPDF):
    def header(self):
        if os.path.exists(LOGO_FILE): self.image(LOGO_FILE, 10, 8, 40)
        self.set_xy(55, 12); self.set_font('Arial', 'B', 14)
        self.cell(0, 6, 'SOCIEDAD MADERERA GALVEZ Y DI GENOVA LTDA', 0, 1, 'L')
        self.set_xy(55, 19); self.set_font('Arial', 'B', 11); self.set_text_color(100)
        self.cell(0, 6, 'SISTEMA DE GESTIÓN EN SST DS44', 0, 1, 'L')
        self.set_draw_color(183, 28, 28); self.set_line_width(0.5)
        self.line(10, 50, 285, 50); self.ln(25)

    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8); self.set_text_color(128)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def section_title(self, title):
        self.set_font('Arial', 'B', 10); self.set_fill_color(240); self.set_text_color(0)
        self.cell(0, 8, title, 1, 1, 'L', 1); self.ln(4)

    def kpi_row(self, label, val_mes, val_acum, unit):
        def safe_fmt(val):
            try: return f"{float(val):.2f}"
            except: return "0.00"
        def safe_int(val):
            try: return f"{int(val)}"
            except: return "0"
        
        v_m = safe_int(val_mes) if "N" in unit or "Dias" in unit else safe_fmt(val_mes)
        v_a = safe_int(val_acum) if "N" in unit or "Dias" in unit else safe_fmt(val_acum)

        self.set_font('Arial', '', 10); self.cell(70, 8, label, 1)
        self.set_font('Arial', 'B', 10); self.cell(40, 8, v_m, 1, 0, 'C')
        self.set_text_color(183, 28, 28); self.cell(40, 8, v_a, 1, 0, 'C')
        self.set_text_color(0); self.set_font('Arial', 'I', 9); self.cell(40, 8, unit, 1, 1, 'C')

    def clean_text(self, text):
        replacements = {'\u2013': '-', '\u2014': '-', '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"', '\u2022': '*', '€': 'EUR'}
        for k, v in replacements.items(): text = text.replace(k, v)
        return text.encode('latin-1', 'replace').decode('latin-1')

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
    
    if not months_avail: st.warning("Sin datos."); st.stop()
    sel_month = col_m.selectbox("Mes de Cierre", months_avail, index=len(months_avail)-1 if months_avail else 0)
    
    # DATOS
    row_mes = df_year[df_year['Mes'] == sel_month].iloc[0]
    idx_corte = MESES_ORDEN.index(sel_month)
    df_acum = df_year[df_year['Mes_Idx'] <= idx_corte]
    
    sum_acc = df_acum['Accidentes CTP'].sum()
    sum_dias = df_acum['Días Perdidos'].sum()
    sum_hht = df_acum['HHT'].sum()
    
    df_masa_ok = df_acum[df_acum['Masa Laboral'] > 0]
    avg_masa = df_masa_ok['Masa Laboral'].mean() if not df_masa_ok.empty else 0

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
    
    # AUDITORÍA
    with st.expander("🔍 Auditoría de Datos"):
        st.markdown(f"**Datos Mes:** Masa: {row_mes['Masa Laboral']} | HHT: {row_mes['HHT']} | Acc: {row_mes['Accidentes CTP']}")
        st.dataframe(row_mes.to_frame().T)

    st.markdown("---")
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
    
    def donut(val, title, col_obj):
        color = "#66BB6A" if val >= metas['meta_gestion'] else "#EF5350"
        fig = go.Figure(go.Pie(values=[val, 100-val], hole=0.7, marker_colors=[color, '#eee'], textinfo='none'))
        fig.update_layout(height=120, margin=dict(t=0,b=0,l=0,r=0), annotations=[dict(text=f"{val:.0f}%", x=0.5, y=0.5, font_size=16, showarrow=False)])
        col_obj.markdown(f"<div style='text-align:center; font-size:13px;'>{title}</div>", unsafe_allow_html=True)
        col_obj.plotly_chart(fig, use_container_width=True, key=title)

    donut(p_insp, "Inspecciones", g1)
    donut(p_cap, "Capacitaciones", g2)
    donut(p_medidas, "Hallazgos", g3)
    donut(p_salud, "Salud", g4)

    st.markdown("---")
    if st.button("📄 Generar Reporte PDF"):
        try:
            pdf = PDF_SST(orientation='P', format='A4')
            pdf.add_page(); pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, f"PERIODO: {sel_month.upper()} {sel_year}", 0, 1, 'L'); pdf.ln(2)
            
            pdf.section_title("1. INDICADORES RESULTADO")
            pdf.set_fill_color(220); pdf.set_font('Arial', 'B', 9)
            pdf.cell(70, 8, "INDICADOR", 1, 0, 'C', 1); pdf.cell(40, 8, "MES", 1, 0, 'C', 1)
            pdf.cell(40, 8, "ACUMULADO", 1, 0, 'C', 1); pdf.cell(40, 8, "UNIDAD", 1, 1, 'C', 1)
            
            pdf.kpi_row("Tasa Accidentabilidad", row_mes['Tasa Acc.'], ta_acum, "%")
            pdf.kpi_row("Tasa Siniestralidad", row_mes['Tasa Sin.'], ts_acum, "Dias/Trab")
            pdf.kpi_row("Indice Frecuencia", row_mes['Indice Frec.'], if_acum, "Acc/1M HHT")
            pdf.kpi_row("Total Accidentes CTP", row_mes['Accidentes CTP'], sum_acc, "N Eventos")
            pdf.ln(5)
            
            pdf.section_title("2. GESTIÓN OPERATIVA")
            
            # --- MODIFICACIÓN: Mostrar "X de Y" ---
            # Preparamos los datos con el formato texto
            insp_txt = f"{int(row_mes['Insp. Ejecutadas'])} de {int(row_mes['Insp. Programadas'])}"
            cap_txt = f"{int(row_mes['Cap. Ejecutadas'])} de {int(row_mes['Cap. Programadas'])}"
            med_txt = f"{int(row_mes['Medidas Cerradas'])} de {int(row_mes['Medidas Abiertas'])}"
            salud_txt = f"{int(row_mes['Vig. Salud Vigente'])} de {int(row_mes['Expuestos Silice/Ruido'])}"
            
            data_gest = [
                ("Inspecciones", p_insp, insp_txt), 
                ("Capacitaciones", p_cap, cap_txt),
                ("Cierre Hallazgos", p_medidas, med_txt), 
                ("Salud Ocup.", p_salud, salud_txt)
            ]
            
            for label, val, txt_detail in data_gest:
                pdf.cell(60, 8, label, 0)
                
                # Barra
                x = pdf.get_x(); y = pdf.get_y()
                pdf.set_fill_color(230); pdf.rect(x, y+2, 60, 4, 'F')
                pdf.set_fill_color(76, 175, 80) if val >= metas['meta_gestion'] else pdf.set_fill_color(244, 67, 54)
                w_bar = (val/100)*60 if val <= 100 else 60
                pdf.rect(x, y+2, w_bar, 4, 'F')
                
                # Texto Porcentaje
                pdf.set_x(x + 65)
                pdf.cell(15, 8, f"{val:.0f}%", 0, 0)
                
                # Texto Detalle (X de Y)
                pdf.set_font('Arial', 'I', 8)
                pdf.set_text_color(100)
                pdf.cell(30, 8, f"({txt_detail})", 0, 1)
                
                # Reset fuente
                pdf.set_font('Arial', '', 10); pdf.set_text_color(0)

            pdf.ln(5); pdf.section_title("3. OBSERVACIONES")
            pdf.set_font('Arial', '', 10); pdf.set_draw_color(100)
            
            clean_insight = pdf.clean_text(insight_text.replace("<b>","").replace("</b>","").replace("<br>","\n").replace("⚠️","").replace("✅","").replace("🚑",""))
            obs_raw = str(row_mes['Observaciones'])
            if obs_raw.lower() in ["nan", "none", "0", "0.0", ""]: obs_raw = "Sin observaciones registradas para este periodo."
            clean_obs = pdf.clean_text(obs_raw)
            
            pdf.multi_cell(0, 6, f"ANALISIS SISTEMA:\n{clean_insight}\n\nCOMENTARIOS EXPERTO:\n{clean_obs}", 1, 'L')
            
            pdf.ln(15); pdf.line(110, pdf.get_y(), 190, pdf.get_y())
            pdf.set_xy(110, pdf.get_y()+2); pdf.set_font('Arial', 'B', 8)
            pdf.cell(80, 5, "Firma Experto", 0, 0, 'C')
            
            out = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Descargar", out, f"Reporte_{sel_month}_{sel_year}.pdf", "application/pdf")
        except Exception as e:
            st.error(f"Error al generar PDF: {e}")

with tab_editor:
    st.subheader("📝 Carga de Datos")
    c_y, c_m = st.columns(2)
    edit_year = c_y.selectbox("Año:", years, key="ed_y")
    
    m_list = df[df['Año'] == edit_year]['Mes'].tolist()
    m_list.sort(key=lambda x: MESES_ORDEN.index(x) if x in MESES_ORDEN else 99)
    edit_month = c_m.selectbox("Mes:", m_list, key="ed_m")
    
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
                st.
