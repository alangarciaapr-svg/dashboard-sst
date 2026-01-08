import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
import shutil
from fpdf import FPDF
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
import tempfile
import numpy as np

# Configuración Matplotlib
matplotlib.use('Agg')

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="SST - Maderas Galvez", layout="wide", page_icon="🌲")

# --- 2. GESTIÓN DE DATOS ---
CSV_FILE = "base_datos_galvez_v19.csv"
LOGO_FILE = "logo_empresa_persistente.png"
MESES_ORDEN = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

# COLORES
COLOR_PRIMARY = (183, 28, 28)
COLOR_SECONDARY = (50, 50, 50)
COLOR_GREEN = (46, 125, 50)
COLOR_RED = (198, 40, 40)

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
    df['HHT'] = df['HHT'].apply(lambda x: x if x > 0 else 0)
    
    def calc_row(row):
        masa = row['Masa Laboral']
        hht = row['HHT']
        if masa <= 0 or hht <= 0: return 0, 0, 0, 0
        ta = (row['Accidentes CTP'] / masa) * 100
        ts = (row['Días Perdidos'] / masa) * 100
        if_ = (row['Accidentes CTP'] * 1000000) / hht
        ig = ((row['Días Perdidos'] + row['Días Cargo']) * 1000000) / hht
        return ta, ts, if_, ig

    result = df.apply(calc_row, axis=1, result_type='expand')
    df['Tasa Acc.'] = result[0]
    df['Tasa Sin.'] = result[1]
    df['Indice Frec.'] = result[2]
    df['Indice Grav.'] = result[3]
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
        insights.append(f"⚠️ <b>ALERTA CRÍTICA:</b> Tasa Acumulada ({ta_acum:.2f}%) excede la meta ({metas['meta_ta']}%)")
    elif ta_acum > (metas['meta_ta'] * 0.8):
        insights.append(f"🔸 <b>PRECAUCIÓN:</b> Tasa Acumulada al límite.")
    else:
        insights.append(f"✅ <b>EXCELENTE:</b> Accidentabilidad bajo control.")
    
    if row_mes['Tasa Sin.'] > 0:
        insights.append(f"🚑 <b>DÍAS PERDIDOS:</b> {int(row_mes['Días Perdidos'])} días en este mes.")
    
    if not insights: return "Sin desviaciones significativas."
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
    meta_ta = st.slider("Meta Tasa Acc. (%)", 0.0, 8.0, 3.0)
    meta_gestion = st.slider("Meta Gestión (%)", 50, 100, 90)
    metas = {'meta_ta': meta_ta, 'meta_gestion': meta_gestion}

# --- 4. MOTOR PDF EJECUTIVO ---
class PDF_SST(FPDF):
    def header(self):
        self.set_fill_color(245, 245, 245)
        self.rect(0, 0, 210, 40, 'F')
        if os.path.exists(LOGO_FILE): self.image(LOGO_FILE, 10, 8, 35)
        
        self.set_xy(50, 10)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(*COLOR_PRIMARY)
        self.cell(0, 8, 'SOCIEDAD MADERERA GALVEZ Y DI GENOVA LTDA', 0, 1, 'L')
        
        self.set_xy(50, 18)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(*COLOR_SECONDARY)
        self.cell(0, 6, 'INFORME EJECUTIVO DE GESTIÓN SST (DS 44)', 0, 1, 'L')
        
        self.set_draw_color(*COLOR_PRIMARY)
        self.set_line_width(1)
        self.line(10, 38, 200, 38)
        self.ln(30)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150)
        self.cell(0, 10, f'Documento Oficial SGSST - Pagina {self.page_no()}', 0, 0, 'C')

    def section_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(*COLOR_SECONDARY)
        self.set_text_color(255, 255, 255) # ESTO PONE LA TINTA EN BLANCO
        self.cell(0, 8, f"  {title}", 0, 1, 'L', 1)
        self.set_text_color(0, 0, 0) # BUGFIX: RESTAURAR TINTA NEGRA
        self.ln(4)

    def kpi_card_color(self, label, value, unit, x, y, w, h, is_good):
        self.set_fill_color(220, 220, 220)
        self.rect(x+1, y+1, w, h, 'F')
        color_bg = (232, 245, 233) if is_good else (255, 235, 238)
        self.set_fill_color(*color_bg)
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.2)
        self.rect(x, y, w, h, 'DF')
        color_side = COLOR_GREEN if is_good else COLOR_RED
        self.set_fill_color(*color_side)
        self.rect(x, y, 2, h, 'F')
        self.set_xy(x+4, y+3)
        self.set_font('Arial', 'B', 8)
        self.set_text_color(100, 100, 100)
        self.cell(w-5, 4, label, 0, 1, 'L')
        self.set_xy(x+2, y+10)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(*COLOR_SECONDARY)
        self.cell(w-5, 8, str(value), 0, 1, 'C')
        self.set_xy(x+2, y+20)
        self.set_font('Arial', '', 7)
        self.cell(w-5, 4, unit, 0, 1, 'C')
        self.set_text_color(0, 0, 0) # Reset

    def draw_trend_chart(self, df_hist, x, y, w, h):
        try:
            fig, ax = plt.subplots(figsize=(6, 3))
            months = df_hist['Mes'].str[:3]
            values = df_hist['Tasa Acc.']
            ax.plot(months, values, marker='o', color='#b71c1c', linewidth=2, label='Tasa Acc.')
            ax.fill_between(months, values, color='#b71c1c', alpha=0.1)
            ax.set_title('Tendencia Anual de Accidentabilidad', fontsize=10, color='#333333')
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.tick_params(axis='both', which='major', labelsize=8)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                plt.savefig(tmp.name, format='png', bbox_inches='tight', dpi=100)
                tmp_name = tmp.name
            plt.close(fig)
            self.image(tmp_name, x=x, y=y, w=w, h=h)
            os.unlink(tmp_name)
        except: pass

    def draw_donut_chart_image(self, val_pct, color_hex, x, y, size=30):
        try:
            val_plot = min(val_pct, 100); val_plot = max(val_plot, 0)
            fig, ax = plt.subplots(figsize=(2, 2))
            ax.pie([val_plot, 100-val_plot], colors=[color_hex, '#eeeeee'], startangle=90, counterclock=False, 
                   wedgeprops=dict(width=0.4, edgecolor='white'))
            ax.text(0, 0, f"{val_pct:.0f}%", ha='center', va='center', fontsize=12, fontweight='bold', color='#333333')
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                plt.savefig(tmp.name, format='png', transparent=True, dpi=100, bbox_inches='tight')
                tmp_name = tmp.name
            plt.close(fig)
            self.image(tmp_name, x=x, y=y, w=size, h=size)
            os.unlink(tmp_name)
        except: pass

    def clean_text(self, text):
        replacements = {'\u2013': '-', '\u2014': '-', '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"', '\u2022': '*', '€': 'EUR'}
        for k, v in replacements.items(): text = text.replace(k, v)
        return text.encode('latin-1', 'replace').decode('latin-1')

    def footer_signatures(self):
        y_pos = self.get_y() + 10
        if y_pos > 250:
            self.add_page()
            y_pos = self.get_y() + 20
        self.set_y(y_pos)
        
        # Firma Gerente
        self.line(20, y_pos, 90, y_pos)
        self.set_xy(20, y_pos + 2)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(0, 0, 0) # Asegurar Negro
        self.cell(70, 5, "RODRIGO GALVEZ REBOLLEDO", 0, 1, 'C')
        self.set_xy(20, y_pos + 7)
        self.set_font('Arial', '', 8)
        self.cell(70, 5, "Gerente General / Rep. Legal", 0, 1, 'C')
        
        # Firma Experto
        self.line(120, y_pos, 190, y_pos)
        self.set_xy(120, y_pos + 2)
        self.set_font('Arial', 'B', 9)
        self.cell(70, 5, "ALAN GARCIA VIDAL", 0, 1, 'C')
        self.set_xy(120, y_pos + 7)
        self.set_font('Arial', '', 8)
        self.cell(70, 5, "Ingeniero en Prevención de Riesgos", 0, 1, 'C')
        
        self.ln(15)
        self.set_font('Arial', 'I', 7)
        self.set_text_color(128)
        self.multi_cell(0, 4, "Este documento es parte integrante del SGSST. Confidencial.", 0, 'C')

# --- 5. DASHBOARD ---
df = st.session_state['df_main']
tab_dash, tab_editor = st.tabs(["📊 DASHBOARD EJECUTIVO", "📝 EDITOR DE DATOS"])

years = sorted(df['Año'].unique(), reverse=True)
if not years: years = [2026]

with tab_dash:
    c1, c2 = st.columns([1, 4])
    with c1:
        if os.path.exists(LOGO_FILE): st.image(LOGO_FILE, width=160)
    with c2:
        st.title("SOCIEDAD MADERERA GALVEZ Y DI GENOVA LTDA")
        st.markdown("### 🛡️ CONTROL DE MANDO EJECUTIVO (SGSST)")

    col_y, col_m = st.columns(2)
    sel_year = col_y.selectbox("Año Fiscal", years)
    
    df_year = df[df['Año'] == sel_year].copy()
    df_year['Mes_Idx'] = df_year['Mes'].apply(lambda x: MESES_ORDEN.index(x) if x in MESES_ORDEN else 99)
    df_year = df_year.sort_values('Mes_Idx')
    months_avail = df_year['Mes'].tolist()
    
    if not months_avail: st.warning("Sin datos."); st.stop()
    sel_month = col_m.selectbox("Mes de Corte", months_avail, index=len(months_avail)-1 if months_avail else 0)
    
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
    st.info("💡 **ANÁLISIS INTELIGENTE DEL SISTEMA:**")
    st.markdown(f"<div style='background-color:#e3f2fd; padding:10px; border-radius:5px;'>{insight_text}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f"#### 🚀 DESEMPEÑO ACUMULADO")
    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    def plot_gauge(value, title, max_val, threshold, inverse=False):
        colors = {'good': '#2E7D32', 'bad': '#C62828'}
        bar_color = colors['good'] if (value <= threshold if inverse else value >= threshold) else colors['bad']
        fig = go.Figure(go.Indicator(mode = "gauge+number", value = value, title = {'text': title, 'font': {'size': 14}},
            gauge = {'axis': {'range': [0, max_val]}, 'bar': {'color': bar_color}}))
        fig.update_layout(height=200, margin=dict(t=30,b=10,l=20,r=20))
        return fig

    with col_g1: st.plotly_chart(plot_gauge(ta_acum, "Tasa Acc. Acum", 8, metas['meta_ta'], True), use_container_width=True)
    with col_g2: st.plotly_chart(plot_gauge(ts_acum, "Tasa Sin. Acum", 50, 10, True), use_container_width=True)
    with col_g3: st.plotly_chart(plot_gauge(if_acum, "Ind. Frecuencia", 50, 10, True), use_container_width=True)
    
    meses_transcurridos = idx_corte + 1
    proyeccion = int((sum_acc / meses_transcurridos) * 12) if meses_transcurridos > 0 else 0
    with col_g4:
        st.markdown("<br>", unsafe_allow_html=True)
        st.metric("Total Accidentes", int(sum_acc))
        st.metric("Proyección Año", proyeccion, delta=f"{proyeccion - int(sum_acc)} estimados", delta_color="inverse")

    st.markdown("---")
    g1, g2, g3, g4 = st.columns(4)
    def donut(val, title, col_obj):
        color = "#66BB6A" if val >= metas['meta_gestion'] else "#EF5350"
        fig = go.Figure(go.Pie(values=[val, 100-val], hole=0.7, marker_colors=[color, '#eee'], textinfo='none'))
        fig.update_layout(height=140, margin=dict(t=0,b=0,l=0,r=0), annotations=[dict(text=f"{val:.0f}%", x=0.5, y=0.5, font_size=20, showarrow=False)])
        col_obj.markdown(f"<div style='text-align:center; font-size:13px;'>{title}</div>", unsafe_allow_html=True)
        col_obj.plotly_chart(fig, use_container_width=True, key=title)

    donut(p_insp, "Inspecciones", g1)
    donut(p_cap, "Capacitaciones", g2)
    donut(p_medidas, "Cierre Hallazgos", g3)
    donut(p_salud, "Salud Ocupacional", g4)

    st.markdown("---")
    if st.button("📄 Generar Reporte Ejecutivo PDF"):
        try:
            pdf = PDF_SST(orientation='P', format='A4')
            pdf.add_page()
            
            # PÁGINA 1
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 10, f"PERIODO: {sel_month.upper()} {sel_year}", 0, 1, 'R')
            
            pdf.section_title("1. INDICADORES CLAVE DE DESEMPEÑO (ACUMULADO)")
            y_cards = pdf.get_y(); card_w = 45; card_h = 30; gap = 5
            
            pdf.kpi_card_color("TASA ACCIDENTABILIDAD", f"{ta_acum:.2f}", "%", 10, y_cards, card_w, card_h, ta_acum <= metas['meta_ta'])
            pdf.kpi_card_color("TASA SINIESTRALIDAD", f"{ts_acum:.2f}", "Dias/Trab", 10+card_w+gap, y_cards, card_w, card_h, True)
            pdf.kpi_card_color("INDICE FRECUENCIA", f"{if_acum:.2f}", "Acc/1M HHT", 10+(card_w+gap)*2, y_cards, card_w, card_h, True)
            pdf.kpi_card_color("TOTAL ACCIDENTES", f"{int(sum_acc)}", "Eventos Reales", 10+(card_w+gap)*3, y_cards, card_w, card_h, sum_acc == 0)
            
            pdf.set_y(y_cards + card_h + 10)
            pdf.section_title("2. TENDENCIA ANUAL DE ACCIDENTABILIDAD")
            pdf.draw_trend_chart(df_acum, 10, pdf.get_y(), 190, 60)
            pdf.set_y(pdf.get_y() + 65)
            
            pdf.section_title("3. CUMPLIMIENTO PROGRAMA GESTIÓN")
            insp_txt = f"{int(row_mes['Insp. Ejecutadas'])} de {int(row_mes['Insp. Programadas'])}"
            cap_txt = f"{int(row_mes['Cap. Ejecutadas'])} de {int(row_mes['Cap. Programadas'])}"
            med_txt = f"{int(row_mes['Medidas Cerradas'])} de {int(row_mes['Medidas Abiertas'])}"
            salud_txt = f"{int(row_mes['Vig. Salud Vigente'])} de {int(row_mes['Expuestos Silice/Ruido'])}"
            
            data_gest = [
                ("Inspecciones", p_insp, insp_txt), ("Capacitaciones", p_cap, cap_txt),
                ("Hallazgos", p_medidas, med_txt), ("Salud Ocup.", p_salud, salud_txt)
            ]
            y_circles = pdf.get_y()
            for i, (label, val, txt) in enumerate(data_gest):
                x_pos = 15 + (i * 48)
                color_hex = '#4CAF50' if val >= metas['meta_gestion'] else '#F44336'
                pdf.draw_donut_chart_image(val, color_hex, x_pos, y_circles, size=30)
                
                # BUGFIX: Forzar color negro
                pdf.set_text_color(0, 0, 0)
                pdf.set_xy(x_pos - 5, y_circles + 32)
                pdf.set_font('Arial', 'B', 8); pdf.cell(40, 4, label, 0, 1, 'C')
                pdf.set_xy(x_pos - 5, y_circles + 36)
                pdf.set_font('Arial', '', 7); pdf.set_text_color(100); pdf.cell(40, 4, txt, 0, 1, 'C')
                pdf.set_text_color(0)

            # PÁGINA 2
            pdf.add_page()
            pdf.section_title("4. DETALLE ESTADÍSTICO MENSUAL")
            pdf.set_fill_color(230); pdf.set_font('Arial', 'B', 8)
            pdf.set_text_color(0, 0, 0) # BUGFIX: Forzar negro
            
            cols = [("MES", 25), ("M. LAB", 20), ("ACC", 15), ("DIAS P", 20), ("T. ACC", 20), ("T. SIN", 20), ("I. FREC", 20), ("I. GRAV", 20)]
            for c_name, c_w in cols: pdf.cell(c_w, 6, c_name, 1, 0, 'C', 1)
            pdf.ln()
            
            pdf.set_font('Arial', '', 8)
            for _, r in df_acum.iterrows():
                pdf.cell(25, 6, r['Mes'], 1)
                pdf.cell(20, 6, f"{int(r['Masa Laboral'])}", 1, 0, 'C')
                pdf.cell(15, 6, f"{int(r['Accidentes CTP'])}", 1, 0, 'C')
                pdf.cell(20, 6, f"{int(r['Días Perdidos'])}", 1, 0, 'C')
                pdf.cell(20, 6, f"{r['Tasa Acc.']:.2f}", 1, 0, 'C')
                pdf.cell(20, 6, f"{r['Tasa Sin.']:.2f}", 1, 0, 'C')
                pdf.cell(20, 6, f"{r['Indice Frec.']:.2f}", 1, 0, 'C')
                pdf.cell(20, 6, f"{r['Indice Grav.']:.0f}", 1, 0, 'C')
                pdf.ln()

            pdf.ln(10)
            pdf.section_title("5. OBSERVACIONES DEL EXPERTO")
            pdf.set_font('Arial', '', 10)
            pdf.set_text_color(0, 0, 0) # BUGFIX
            
            obs_raw = str(row_mes['Observaciones'])
            if obs_raw.lower() in ["nan", "none", "0", "0.0", ""]: obs_raw = "Sin observaciones registradas."
            clean_obs = pdf.clean_text(obs_raw)
            pdf.multi_cell(0, 6, clean_obs, 1, 'L')
            
            # FIRMAS Y LEGAL
            pdf.ln(20)
            pdf.footer_signatures()
            
            out = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Descargar Reporte Ejecutivo", out, f"Reporte_SST_{sel_month}.pdf", "application/pdf")
        except Exception as e: st.error(f"Error PDF: {e}")

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
            c_obs = str(df.at[row_idx, 'Observaciones'])
            if c_obs.lower() in ["nan", "none", "0", ""]: c_obs = ""
            val_obs = st.text_area("Texto del Reporte:", value=c_obs, height=100)

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
