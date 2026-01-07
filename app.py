import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
from fpdf import FPDF

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="SGSST - Maderas Galvez", layout="wide", page_icon="🌲")

# --- 2. GESTIÓN DE DATOS ---
CSV_FILE = "base_datos_galvez_auto.csv"

def get_structure():
    return pd.DataFrame({
        'Año': [2026], 
        'Mes': ['Enero'],
        # DATOS DE ENTRADA
        'Masa Laboral': [100.0], 
        'Horas Extras': [0.0],
        'Horas Ausentismo': [0.0],
        'Accidentes CTP': [0.0], 
        'Días Perdidos': [0.0], 
        'Días Cargo': [0.0],
        # GESTIÓN
        'Insp. Programadas': [10.0], 'Insp. Ejecutadas': [8.0],
        'Cap. Programadas': [5.0], 'Cap. Ejecutadas': [5.0],
        'Medidas Abiertas': [5.0], 'Medidas Cerradas': [4.0],
        'Expuestos Silice/Ruido': [10.0], 'Vig. Salud Vigente': [10.0],
        # CALCULADOS
        'HHT': [18000.0],
        'Tasa Acc.': [0.0], 'Tasa Sin.': [0.0],
        'Indice Frec.': [0.0], 'Indice Grav.': [0.0]
    })

def limpiar_numeros(df):
    cols_numericas = [
        'Masa Laboral', 'Horas Extras', 'Horas Ausentismo', 'Accidentes CTP', 
        'Días Perdidos', 'Días Cargo', 'Insp. Programadas', 'Insp. Ejecutadas',
        'Cap. Programadas', 'Cap. Ejecutadas', 'Medidas Abiertas', 'Medidas Cerradas',
        'Expuestos Silice/Ruido', 'Vig. Salud Vigente', 'HHT', 'Tasa Acc.', 
        'Tasa Sin.', 'Indice Frec.', 'Indice Grav.'
    ]
    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def calcular_indices_mensuales(df):
    df = limpiar_numeros(df)
    # 1. HHT Mensual
    df['HHT'] = (df['Masa Laboral'] * 180) + df['Horas Extras'] - df['Horas Ausentismo']
    df['HHT'] = df['HHT'].apply(lambda x: x if x > 0 else 1)
    masa_segura = df['Masa Laboral'].apply(lambda x: x if x > 0 else 1)

    # 2. Tasas Mensuales
    df['Tasa Acc.'] = (df['Accidentes CTP'] / masa_segura) * 100
    df['Tasa Sin.'] = (df['Días Perdidos'] / masa_segura) * 100

    # 3. Índices Mensuales
    df['Indice Frec.'] = (df['Accidentes CTP'] * 1000000) / df['HHT']
    df['Indice Grav.'] = ((df['Días Perdidos'] + df['Días Cargo']) * 1000000) / df['HHT']
    
    return df

def load_data():
    if os.path.exists(CSV_FILE):
        try:
            df = pd.read_csv(CSV_FILE)
            ref = get_structure()
            for col in ref.columns:
                if col not in df.columns: df[col] = 0
            return calcular_indices_mensuales(df)
        except: return get_structure()
    return get_structure()

def save_data(df):
    df_calc = calcular_indices_mensuales(df)
    df_calc.to_csv(CSV_FILE, index=False)
    return df_calc

if 'df_main' not in st.session_state:
    st.session_state['df_main'] = load_data()

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.title("🌲 Configuración")
    uploaded_logo = st.file_uploader("Subir Logo", type=['png', 'jpg'])
    logo_path = "logo_temp.png"
    if uploaded_logo:
        with open(logo_path, "wb") as f: f.write(uploaded_logo.getbuffer())
    
    st.markdown("---")
    st.info("ℹ️ **Cálculo Automático:**\nSe calculan indicadores mensuales y ACUMULADOS según DS 67.")
    
    if st.button("♻️ Reiniciar Datos"):
        save_data(get_structure())
        st.rerun()

# --- 4. MOTOR PDF ---
class PDF_GALVEZ(FPDF):
    def header(self):
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 8, 30)
        
        self.set_xy(45, 10)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 5, 'SOCIEDAD MADERERA GALVEZ Y DI GENOVA LTDA', 0, 1, 'L')
        
        self.set_xy(45, 16)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(183, 28, 28)
        self.cell(0, 8, 'INFORME DE GESTIÓN SST (ACUMULADO DS 67)', 0, 1, 'L')
        
        self.set_xy(45, 24)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'Indicadores Acumulados y Mensuales', 0, 1, 'L')
        
        self.set_draw_color(200, 200, 200)
        self.line(10, 32, 285, 32)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def kpi_card(self, title, val_acum, val_mes, unit, x, y, w, h=30):
        # Fondo
        self.set_fill_color(248, 249, 250)
        self.set_draw_color(200, 200, 200)
        self.rect(x, y, w, h, 'DF')
        
        # Título
        self.set_xy(x, y + 2)
        self.set_font('Arial', 'B', 7)
        self.set_text_color(80, 80, 80)
        self.cell(w, 4, title, 0, 1, 'C')
        
        # Valor ACUMULADO (Grande)
        self.set_xy(x, y + 8)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 0, 0)
        self.cell(w, 8, str(val_acum), 0, 1, 'C')
        
        # Etiqueta Acumulado
        self.set_xy(x, y + 16)
        self.set_font('Arial', 'B', 6)
        self.set_text_color(183, 28, 28) # Rojo
        self.cell(w, 3, "ACUMULADO ANUAL", 0, 1, 'C')

        # Valor Mensual (Pequeño)
        self.set_xy(x, y + 22)
        self.set_font('Arial', '', 7)
        self.set_text_color(100, 100, 100)
        self.cell(w, 4, f"Mes: {val_mes} {unit}", 0, 1, 'C')

    def draw_progress_bar(self, label, percentage, x, y, w_total):
        self.set_xy(x, y)
        self.set_font('Arial', 'B', 9)
        self.set_text_color(0, 0, 0)
        self.cell(60, 5, label, 0, 0, 'L')
        bar_x = x; bar_y = y + 6; bar_h = 5
        self.set_fill_color(230, 230, 230)
        self.rect(bar_x, bar_y, w_total, bar_h, 'F')
        
        if percentage >= 90: self.set_fill_color(46, 125, 50)
        elif percentage >= 70: self.set_fill_color(255, 143, 0)
        else: self.set_fill_color(198, 40, 40)
        
        fill_w = (percentage / 100) * w_total
        if fill_w > w_total: fill_w = w_total
        if fill_w < 0: fill_w = 0
        
        self.rect(bar_x, bar_y, fill_w, bar_h, 'F')
        self.set_xy(bar_x + w_total + 2, bar_y - 1)
        self.set_font('Arial', '', 9)
        self.cell(15, 6, f"{percentage:.0f}%", 0, 0, 'L')

# --- 5. LÓGICA APP ---
df = st.session_state['df_main']
tab_dash, tab_editor = st.tabs(["📊 DASHBOARD (ACUMULADO)", "📝 EDITOR MENSUAL"])

with tab_dash:
    # Encabezado
    c1, c2 = st.columns([1, 5])
    with c1:
        if os.path.exists(logo_path): st.image(logo_path, width=120)
    with c2:
        st.title("SOCIEDAD MADERERA GALVEZ Y DI GENOVA LTDA")
        st.markdown("**Sistema de Gestión SST - Indicadores Acumulados DS 67**")

    # Filtros
    col_y, col_m = st.columns(2)
    years = sorted(df['Año'].unique(), reverse=True)
    sel_year = col_y.selectbox("Año", years)
    
    # Filtrar DF por año
    df_year = df[df['Año'] == sel_year]
    
    m_order = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    
    # Ordenar DF
    df_year['Mes_Num'] = df_year['Mes'].apply(lambda x: m_order.index(x) if x in m_order else 99)
    df_year = df_year.sort_values('Mes_Num')

    # Selector de Mes de CORTE
    months = df_year['Mes'].tolist()
    sel_month = col_m.selectbox("Mes de Corte (Acumulado hasta...)", months, index=len(months)-1 if months else 0)
    
    # --- LOGICA ACUMULADA (DS 67) ---
    # Filtramos desde Enero hasta el mes seleccionado
    idx_corte = m_order.index(sel_month)
    df_acum = df_year[df_year['Mes_Num'] <= idx_corte]
    
    # 1. Sumas y Promedios Acumulados
    sum_acc = df_acum['Accidentes CTP'].sum()
    sum_dias = df_acum['Días Perdidos'].sum()
    sum_dias_cargo = df_acum['Días Cargo'].sum()
    sum_hht = df_acum['HHT'].sum()
    avg_masa = df_acum['Masa Laboral'].mean()
    
    # 2. Índices Acumulados (Fórmulas DS67 aplicadas al periodo)
    # Tasa Acc Acumulada = (Total Accidentes / Promedio Masa) * 100
    tasa_acc_acum = (sum_acc / avg_masa * 100) if avg_masa > 0 else 0
    # Tasa Sin Acumulada = (Total Dias / Promedio Masa) * 100
    tasa_sin_acum = (sum_dias / avg_masa * 100) if avg_masa > 0 else 0
    # IF Acumulado
    if_acum = (sum_acc * 1000000 / sum_hht) if sum_hht > 0 else 0
    # IG Acumulado
    ig_acum = ((sum_dias + sum_dias_cargo) * 1000000 / sum_hht) if sum_hht > 0 else 0

    # 3. Datos del Mes Aislado (Para comparar)
    row_mes = df_year[df_year['Mes'] == sel_month].iloc[0]
    tasa_acc_mes = row_mes['Tasa Acc.']
    tasa_sin_mes = row_mes['Tasa Sin.']
    if_mes = row_mes['Indice Frec.']
    hht_mes = row_mes['HHT']

    # --- VISUALIZACIÓN ---
    st.markdown("---")
    st.markdown(f"### 📈 Desempeño Acumulado (Enero - {sel_month})")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tasa Accidentabilidad (Acum)", f"{tasa_acc_acum:.2f}%", f"Mes: {tasa_acc_mes:.2f}%", delta_color="inverse")
    k2.metric("Tasa Siniestralidad (Acum)", f"{tasa_sin_acum:.2f}", f"Mes: {tasa_sin_mes:.2f}", delta_color="inverse")
    k3.metric("Indice Frecuencia (Acum)", f"{if_acum:.2f}", f"Mes: {if_mes:.2f}", delta_color="inverse")
    k4.metric("HHT Totales (Acum)", f"{int(sum_hht)}", f"Mes: {int(hht_mes)}")

    # Gráficos Evolutivos
    st.markdown("---")
    c_g1, c_g2 = st.columns(2)
    with c_g1:
        st.markdown("**Evolución Tasa de Accidentabilidad (Mensual)**")
        fig_t = go.Figure()
        fig_t.add_trace(go.Scatter(x=df_acum['Mes'], y=df_acum['Tasa Acc.'], mode='lines+markers', name='Tasa Mensual', line=dict(color='red')))
        # Línea promedio acumulado
        fig_t.add_hline(y=tasa_acc_acum, line_dash="dash", annotation_text="Promedio Acum.", annotation_position="bottom right")
        st.plotly_chart(fig_t, use_container_width=True, key="g_tasa")
        
    with c_g2:
        st.markdown("**Acumulación de Días Perdidos**")
        fig_b = go.Figure(go.Bar(x=df_acum['Mes'], y=df_acum['Días Perdidos'], marker_color='orange', name='Días Mes'))
        st.plotly_chart(fig_b, use_container_width=True, key="g_dias")

    # Gestión (Tomamos del último mes o promedio? Usualmente gestión se ve del mes actual o promedio acumulado)
    # Mostraremos la del mes seleccionado para ver la "foto actual" de la gestión
    def safe_div(a, b): 
        try: return (a/b*100) if b > 0 else 0
        except: return 0
    
    p_insp = safe_div(row_mes['Insp. Ejecutadas'], row_mes['Insp. Programadas'])
    p_cap = safe_div(row_mes['Cap. Ejecutadas'], row_mes['Cap. Programadas'])
    p_medidas = safe_div(row_mes['Medidas Cerradas'], row_mes['Medidas Abiertas']) if row_mes['Medidas Abiertas'] > 0 else 100
    p_salud = safe_div(row_mes['Vig. Salud Vigente'], row_mes['Expuestos Silice/Ruido']) if row_mes['Expuestos Silice/Ruido'] > 0 else 100

    # --- PDF ---
    st.markdown("---")
    if st.button("📄 Descargar Reporte Acumulado PDF"):
        pdf = PDF_GALVEZ(orientation='L', format='A4')
        pdf.add_page()
        
        pdf.set_xy(10, 40)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 10, f"PERIODO ACUMULADO: ENERO - {sel_month.upper()} {sel_year}", 0, 1)
        
        # KPIs ACUMULADOS
        y_kpi = 55; w_kpi = 65; gap = 5
        pdf.kpi_card("TASA ACCIDENTABILIDAD", f"{tasa_acc_acum:.2f}%", f"{tasa_acc_mes:.2f}", "%", 10, y_kpi, w_kpi)
        pdf.kpi_card("TASA SINIESTRALIDAD", f"{tasa_sin_acum:.2f}", f"{tasa_sin_mes:.2f}", "Dias/Trab", 10 + w_kpi + gap, y_kpi, w_kpi)
        pdf.kpi_card("INDICE FRECUENCIA", f"{if_acum:.2f}", f"{if_mes:.2f}", "Acc/1M HHT", 10 + (w_kpi + gap)*2, y_kpi, w_kpi)
        pdf.kpi_card("HHT TOTALES", int(sum_hht), f"{int(hht_mes)}", "Horas", 10 + (w_kpi + gap)*3, y_kpi, w_kpi)
        
        # Barras Gestión (Mes Actual)
        y_bars = 95
        pdf.set_xy(10, y_bars)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, f"Gestión Preventiva (Mes: {sel_month})", 0, 1)
        
        y_start_bars = y_bars + 15
        pdf.draw_progress_bar("Plan Inspecciones", p_insp, 10, y_start_bars, 100)
        pdf.draw_progress_bar("Plan Capacitaciones", p_cap, 10, y_start_bars + 15, 100)
        pdf.draw_progress_bar("Cierre Medidas Corr.", p_medidas, 10, y_start_bars + 30, 100)
        pdf.draw_progress_bar("Vigilancia Salud", p_salud, 10, y_start_bars + 45, 100)
        
        # Tabla Resumen Acumulado
        x_tab = 140; y_tab = y_start_bars
        pdf.set_xy(x_tab, y_tab - 6)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(60, 6, "RESUMEN ACUMULADO", 0, 1, 'L')
        pdf.set_font('Arial', '', 9)
        def add_row(label, val, y_pos):
            pdf.set_xy(x_tab, y_pos)
            pdf.cell(80, 7, label, 1)
            pdf.cell(30, 7, str(val), 1, 1, 'C')
        
        add_row("Masa Laboral Promedio", f"{avg_masa:.1f}", y_tab)
        add_row("Total Accidentes CTP", int(sum_acc), y_tab + 7)
        add_row("Total Días Perdidos", int(sum_dias), y_tab + 14)
        add_row("Total Días Cargo", int(sum_dias_cargo), y_tab + 21)
        add_row("Total HHT", int(sum_hht), y_tab + 28)

        out = pdf.output(dest='S').encode('latin-1')
        st.download_button("📥 Descargar Reporte Acumulado", out, f"Reporte_Acumulado_{sel_month}.pdf", "application/pdf")

with tab_editor:
    st.subheader("📝 Editor Mensual")
    st.info("Ingresa los datos mes a mes. El sistema acumula automáticamente.")
    
    cfg = {
        "Mes": st.column_config.SelectboxColumn("Mes", options=m_order, required=True),
        "Masa Laboral": st.column_config.NumberColumn("Trabajadores", min_value=1),
        "Horas Extras": st.column_config.NumberColumn("Horas Extras", min_value=0),
        "Horas Ausentismo": st.column_config.NumberColumn("Ausentismo", min_value=0),
        
        "HHT": st.column_config.NumberColumn("HHT (Mes)", disabled=True),
        "Tasa Acc.": st.column_config.NumberColumn("Tasa Acc (Mes)", disabled=True, format="%.2f%%"),
        "Tasa Sin.": st.column_config.NumberColumn("Tasa Sin (Mes)", disabled=True, format="%.2f"),
        
        "Medidas Abiertas": st.column_config.NumberColumn("Hallazgos"),
        "Medidas Cerradas": st.column_config.NumberColumn("Cerrados"),
    }
    
    edited = st.data_editor(st.session_state['df_main'], num_rows="dynamic", column_config=cfg, use_container_width=True)
    
    if not edited.equals(st.session_state['df_main']):
        st.session_state['df_main'] = save_data(edited)
        st.rerun()
