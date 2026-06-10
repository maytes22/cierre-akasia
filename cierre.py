import streamlit as st
import psycopg2  # Librería para conexión con PostgreSQL en la nube
import pandas as pd
from datetime import datetime
import plotly.express as px

# 1. CONFIGURACIÓN DEL FONDO IDEAL HONDURAS (L. 5,000.00)
FONDO_IDEAL = {500:0, 200:4, 100:20, 50:21, 20:25, 10:25, 5:50, 2:50, 1:50}

def far(monto):
    return f"L. {monto:,.2f}"

# --- CONEXIÓN COMPATIBLE CON SUPABASE EN LA NUBE (CON SSL REQUERIDO) ---
def conectar_db():
    conn = psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"],
        sslmode="require"  # <-- Protección SSL obligatoria para Supabase
    )
    cursor = conn.cursor()
    # Sintaxis estándar de PostgreSQL (SERIAL para ID incrementales)
    cursor.execute('''CREATE TABLE IF NOT EXISTS cierres 
                     (id SERIAL PRIMARY KEY, fecha TEXT, caja TEXT, efectivo DOUBLE PRECISION, 
                      t_credito DOUBLE PRECISION, t_debito DOUBLE PRECISION, transferencias DOUBLE PRECISION, 
                      total DOUBLE PRECISION, diferencia DOUBLE PRECISION, notas TEXT)''')
    conn.commit()
    return conn

# --- FUNCIÓN DE CONTROL DE SEGURIDAD (ANTI-DUPLICADOS) ---
def verificar_cierre_existente(caja):
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    conn = conectar_db()
    cursor = conn.cursor()
    # Marcador %s nativo para evitar inyecciones SQL en Postgres
    cursor.execute("SELECT id FROM cierres WHERE caja = %s AND fecha LIKE %s", (caja, f"{fecha_hoy}%"))
    resultado = cursor.fetchone()
    conn.close()
    return resultado

st.set_page_config(page_title="Akasia Cloud Suite 2026", layout="wide")

# --- CSS: DISEÑO RESPONSIVO INTELIGENTE (CERO DESBORDES) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    label { font-size: 20px !important; font-weight: 700 !important; color: #1E3A8A !important; }
    input { font-size: 24px !important; font-weight: bold !important; height: 55px !important; }
    
    .card-exec {
        background-color: #FFFFFF; padding: 25px; border-radius: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); margin-bottom: 25px; border-top: 6px solid #1E3A8A;
    }
    
    /* TOTALES ADAPTABLES CON CLAMP PARA PANTALLAS CHICAS */
    .hero-total, .dif-box {
        padding: 25px 15px; border-radius: 20px; text-align: center;
        display: flex; flex-direction: column; justify-content: center;
        min-height: 160px; height: auto; width: 100%; margin-bottom: 15px;
    }
    
    .hero-total { background-color: #1E3A8A; color: #F59E0B; }
    .hero-monto { 
        font-size: clamp(26px, 3.8vw, 46px) !important; 
        font-weight: 900; margin: 0; line-height: 1.2; 
        white-space: nowrap; 
    }
    .hero-label { color: #FFFFFF; font-size: clamp(14px, 1.5vw, 17px); font-weight: bold; text-transform: uppercase; margin-bottom: 8px; }

    /* CAJAS DE ALERTA DINÁMICAS */
    .dif-cuadra { background-color: #DCFCE7; color: #166534; border: 4px solid #22C55E; }
    .dif-error { background-color: #FEE2E2; color: #991B1B; border: 4px solid #EF4444; }
    .dif-sobra { background-color: #FEF3C7; color: #92400E; border: 4px solid #F59E0B; }

    /* BOTÓN GIGANTE */
    .stButton>button {
        width: 100%; height: 80px; background: #1E3A8A !important; color: white !important;
        font-size: 26px !important; font-weight: 900 !important; border-radius: 15px !important;
    }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:white;'>AKASIA</h1>", unsafe_allow_html=True)
    opcion = st.radio("MENÚ NUBE", ["📝 Registro de Cierre", "📊 Dashboard Cloud", "📅 Historial"])

# --- SECCIÓN: DASHBOARD CLOUD ---
if opcion == "📊 Dashboard Cloud":
    st.markdown("<h1 style='color:#1E3A8A;'>📊 Rendimiento en Tiempo Real</h1>", unsafe_allow_html=True)
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cierres ORDER BY id DESC")
    columnas = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(cursor.fetchall(), columns=columnas)
    conn.close()

    if not df.empty:
        df['fecha_dt'] = pd.to_datetime(df['fecha'], dayfirst=True)
        k1, k2, k3 = st.columns(3)
        k1.metric("Ventas Totales Nube", far(df['total'].sum()))
        k2.metric("Promedio Diario", far(df['total'].mean()))
        k3.metric("Balance de Descuadres", far(df['diferencia'].sum()), delta=far(df['diferencia'].sum()), delta_color="inverse")

        st.markdown("<div class='card-exec'>", unsafe_allow_html=True)
        fig = px.line(df, x='fecha_dt', y='total', title='📈 Histórico de Ventas Online', markers=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No hay transacciones registradas en la nube todavía.")

# --- SECCIÓN: REGISTRO DE CIERRE ---
elif opcion == "📝 Registro de Cierre":
    st.markdown("<h1 style='color:#1E3A8A; font-size:45px;'>Cierre Diario Akasia</h1>", unsafe_allow_html=True)
    caja_sel = st.selectbox("📍 PUNTO DE VENTA", ["CAJA DEL NEGOCIO", "CAJA DE LA CARPA"])

    # 1. BILLETES (3 COLUMNAS)
    st.markdown("<div class='card-exec'>", unsafe_allow_html=True)
    st.markdown("### 💵 1. CONTEO DE BILLETES")
    b1, b2, b3 = st.columns(3)
    ing = {}
    with b1:
        for d in [500, 200, 100]: ing[d] = st.number_input(f"L. {d}", min_value=0, step=1, key=f"n_{d}")
    with b2:
        for d in [50, 20, 10]: ing[d] = st.number_input(f"L. {d}", min_value=0, step=1, key=f"n_{d}")
    with b3:
        for d in [5, 2, 1]: ing[d] = st.number_input(f"L. {d}", min_value=0, step=1, key=f"n_{d}")
    
    total_ef = sum(d * cant for d, cant in ing.items())
    st.markdown(f"<div class='hero-total'><p class='hero-label'>Efectivo Contado</p><p class='hero-monto'>{far(total_ef)}</p></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 2 y 3. OTROS Y SISTEMA
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("<div class='card-exec'>", unsafe_allow_html=True)
        st.markdown("### 💳 2. OTROS PAGOS")
        t_cre = st.number_input("T. CRÉDITO", min_value=0.0)
        t_deb = st.number_input("T. DÉBITO", min_value=0.0)
        trans = st.number_input("TRANSFERENCIA", min_value=0.0)
        st.markdown("</div>", unsafe_allow_html=True)
    with col_b:
        st.markdown("<div class='card-exec'>", unsafe_allow_html=True)
        st.markdown("### 📄 3. SISTEMA")
        esp_ak = st.number_input("TOTAL SISTEMA AKASIA", min_value=0.0)
        notas = st.text_area("🗒️ Notas:")
        st.markdown("</div>", unsafe_allow_html=True)

    # 4. BALANCE FINAL (AJUSTE DINÁMICO)
    total_real_v = total_ef + t_cre + t_deb + trans
    dif_final = total_real_v - esp_ak
    st.markdown("### 📊 4. BALANCE FINAL DEL DÍA")
    c_res1, c_res2 = st.columns(2)
    with c_res1:
        st.markdown(f"<div class='hero-total' style='background-color:#0F172A;'><p class='hero-label'>VENTA TOTAL REAL</p><p class='hero-monto' style='color:#22C55E;'>{far(total_real_v)}</p></div>", unsafe_allow_html=True)
    with c_res2:
        if abs(dif_final) < 0.1: clase, msg = "dif-cuadra", "CAJA CUADRADA"
        elif dif_final > 0: clase, msg = "dif-sobra", "SOBRANTE EN CAJA"
        else: clase, msg = "dif-error", "FALTANTE EN CAJA"
        st.markdown(f"<div class='dif-box {clase}'><p class='hero-label' style='color:inherit;'>{msg}</p><p class='hero-monto'>{far(dif_final)}</p></div>", unsafe_allow_html=True)

    # 5. REPOSICIÓN
    st.divider()
    st.markdown("<div class='card-exec' style='border-top-color:#EF4444;'>", unsafe_allow_html=True)
    st.markdown("### 💰 5. REPOSICIÓN DE FONDO (L. 5,000)")
    fondo_act = sum(min(ing[d], FONDO_IDEAL[d]) * d for d in FONDO_IDEAL)
    falt_f = 5000 - fondo_act
    f1, f2 = st.columns(2)
    with f1:
        st.markdown(f"<h3 style='color:#B91C1C;'>Faltante: {far(falt_f)}</h3>", unsafe_allow_html=True)
        txt_wa = ""
        for d in [500, 200, 100, 50, 20, 10, 5, 2, 1]:
            tengo = min(ing[d], FONDO_IDEAL[d])
            if tengo < FONDO_IDEAL[d]:
                necesito = FONDO_IDEAL[d] - tengo
                st.write(f"❌ L. {d}: faltan {necesito}")
                txt_wa += f" · L. {d}: Faltan {necesito}\n"
    with f2:
        cambio = st.number_input("Cambio Tomado", min_value=0.0)
        rep_wa = f"📌 REPOSICIÓN FONDO - {caja_sel}\n❌ Faltante Total: {far(falt_f)}\n💵 Cambio Tomado: {far(cambio)}\n🔄 Vuelto: {far(cambio-falt_f)}\n------------------\nBilletes faltantes:\n{txt_wa if txt_wa else 'Fondo OK ✅'}"
        st.code(rep_wa, language="markdown")
    st.markdown("</div>", unsafe_allow_html=True)

    # 6. SOBRE (OBJETIVO CLARO)
    st.markdown("<div class='card-exec' style='border-top-color:#10B981;'>", unsafe_allow_html=True)
    st.markdown("### 🏦 6. SOBRE PARA DEPÓSITO")
    
    debe_haber_sobre = total_ef - 5000  # <--- Cálculo del dinero esperado en sobre
    
    st.markdown(f"""
        <div style='background-color:#ECFDF5; padding:20px; border-radius:15px; border:2px dashed #10B981; text-align:center; margin-bottom:20px;'>
            <p style='color:#065F46; font-size:18px; font-weight:bold; margin:0;'>MONTO QUE DEBE HABER EN EL SOBRE:</p>
            <h2 style='color:#10B981; font-size:40px; margin:5px;'>{far(debe_haber_sobre)}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    s1, s2, s3 = st.columns(3)
    dep_ing = {}
    with s1: 
        for d in [500, 200, 100]: dep_ing[d] = st.number_input(f"Sobre L. {d}", min_value=0, key=f"s_{d}")
    with s2: 
        for d in [50, 20, 10]: dep_ing[d] = st.number_input(f"Sobre L. {d}", min_value=0, key=f"s_{d}")
    with s3: 
        for d in [5, 2, 1]: dep_ing[d] = st.number_input(f"Sobre L. {d}", min_value=0, key=f"s_{d}")
    
    total_s = sum(d * cant for d, cant in dep_ing.items())
    st.markdown(f"<div class='hero-total' style='background:#F1F5F9; border-left:20px solid #10B981; min-height:140px;'><p style='color:#64748B; font-size:18px; font-weight:bold; margin:0;'>TOTAL FÍSICO EN SOBRE</p><p class='hero-monto' style='color:#10B981;'>{far(total_s)}</p></div>", unsafe_allow_html=True)
    
    if total_s > 0 and abs(total_s - debe_haber_sobre) < 0.1:
        st.balloons()
        st.success("✅ SOBRE CUADRADO CON ÉXITO")
    st.markdown("</div>", unsafe_allow_html=True)

    # BOTÓN GUARDAR CON FILTRO DE DUPLICADOS
    if st.button("💾 FINALIZAR Y GUARDAR CIERRE"):
        ya_existe = verificar_cierre_existente(caja_sel)
        if ya_existe:
            st.error(f"❌ El Cierre del Día ya está guardado para {caja_sel}. No se permiten duplicados.")
        else:
            fecha_h = datetime.now().strftime("%d/%m/%Y %H:%M")
            conn = conectar_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO cierres (fecha, caja, efectivo, t_credito, t_debito, transferencias, total, diferencia, notas) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                                 (fecha_h, caja_sel, total_ef, t_cre, t_deb, trans, total_real_v, dif_final, notas))
            conn.commit()
            conn.close()
            st.success("✅ Cierre guardado en la nube perfectamente.")

elif opcion == "📅 Historial":
    st.markdown("<h1 style='color:#1E3A8A;'>📅 Historial Online</h1>", unsafe_allow_html=True)
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cierres ORDER BY id DESC")
    columnas = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(cursor.fetchall(), columns=columnas)
    st.dataframe(df, width='stretch')
    
    st.divider()
    id_del = st.number_input("ID del registro a eliminar:", min_value=0, step=1)
    if st.button("🗑️ Eliminar Registro"):
        cursor.execute("DELETE FROM cierres WHERE id=%s", (id_del,))
        conn.commit()
        st.rerun()
    conn.close()
