import streamlit as st
import pandas as pd
import io
from datetime import timedelta
import random

# =========================================
# CONFIGURACIÓN GENERAL
# =========================================
st.set_page_config(
    page_title="Analizador de Frecuencias",
    layout="centered"
)

st.title("📊 Analizador de Frecuencias por Sorteo")

# =========================================
# FUNCIONES DE VALIDACIÓN
# =========================================
def pares_nones_ok(comb):
    pares = sum(n % 2 == 0 for n in comb)
    return pares in [2, 3]

def contar_consecutivos(comb):
    comb = sorted(comb)
    return sum(1 for i in range(len(comb) - 1) if comb[i] + 1 == comb[i + 1])

def decenas_ok(comb, min_decenas=3):
    return len(set(n // 10 for n in comb)) >= min_decenas

# =========================================
# GENERADOR
# =========================================
def generar_combinaciones(top6, bottom6, intermedios):

    base_nums = list(range(1, 29))

    def construir_base(repetidos):
        combs = [[] for _ in range(6)]

        restantes = [n for n in top6 if n not in repetidos]
        tops_final = repetidos + random.sample(restantes, 4)
        random.shuffle(tops_final)

        for i in range(6):
            combs[i].append(tops_final[i])

        bottoms = random.sample(bottom6, 6)
        for i in range(6):
            combs[i].append(bottoms[i])

        mids = random.sample(intermedios, 12)
        idx = 0
        for i in range(6):
            for _ in range(2):
                combs[i].append(mids[idx])
                idx += 1

        usados = set(n for c in combs for n in c)
        libres = [n for n in base_nums if n not in usados]

        if len(libres) < 6:
            faltan = 6 - len(libres)
            libres.extend(random.sample(base_nums, faltan))

        random.shuffle(libres)

        for i in range(6):
            combs[i].append(libres[i])

        return [sorted(c) for c in combs]

    def validar_suave(comb, nivel):
        if nivel == 1:
            if not pares_nones_ok(comb): return False
            if contar_consecutivos(comb) > 0: return False
            if not decenas_ok(comb, 3): return False
        elif nivel == 2:
            if contar_consecutivos(comb) > 1: return False
            if not decenas_ok(comb, 2): return False
        elif nivel == 3:
            if contar_consecutivos(comb) > 2: return False
        return True

    def validar_global(combs):
        plano = [n for c in combs for n in c]
        conteo = pd.Series(plano).value_counts()
        return len(conteo) == 28 and sum(v == 2 for v in conteo) == 2

    for nivel in [1, 2, 3]:
        for _ in range(2000):
            repetidos = random.sample(top6, 2)
            combs = construir_base(repetidos)

            if not validar_global(combs):
                continue

            validas = [c for c in combs if validar_suave(c, nivel)]

            if len(validas) >= 4:
                return combs, nivel

    return construir_base(random.sample(top6, 2)), 3

# =========================================
# CARGA CSV
# =========================================
archivo = st.file_uploader("📂 Selecciona el archivo CSV")

if archivo is not None:
    df = pd.read_csv(io.BytesIO(archivo.read()), encoding="latin-1")
    df.columns = df.columns.str.strip().str.lower()

    df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["fecha"])

    if df.empty:
        st.error("❌ No hay fechas válidas en el archivo.")
        st.stop()

    # =========================================
    # REGISTRO MANUAL (RESTAURADO)
    # =========================================
    st.markdown("---")
    st.subheader("✍️ Agregar registro manual")

    col1, col2, col3, col4, col5 = st.columns(5)

    r1 = col1.number_input("R1", 1, 28)
    r2 = col2.number_input("R2", 1, 28)
    r3 = col3.number_input("R3", 1, 28)
    r4 = col4.number_input("R4", 1, 28)
    r5 = col5.number_input("R5", 1, 28)

    usar_manual = st.checkbox("Usar este registro en el cálculo")

    if st.button("🔍 Calcular frecuencias"):
        df_calculo = df.copy()

        if usar_manual:
            nueva_fecha = df["fecha"].max() + timedelta(days=1)

            nuevo = pd.DataFrame([{
                "r1": r1,
                "r2": r2,
                "r3": r3,
                "r4": r4,
                "r5": r5,
                "fecha": nueva_fecha
            }])

            df_calculo = pd.concat([df_calculo, nuevo], ignore_index=True)

        fecha_base = df_calculo["fecha"].max()

        def calcular(df_bloque):
            nums = df_bloque[["r1","r2","r3","r4","r5"]]
            nums = pd.Series(nums.values.flatten()).dropna().astype(int)
            conteo = nums.value_counts()
            conteo = conteo.reindex(range(1,29), fill_value=0)
            return conteo.sort_values(ascending=False)

        resultados = {}

        for et, d in {"15 días":15, "1 mes":30, "2 meses":60, "3 meses":90}.items():
            datos = df_calculo[df_calculo["fecha"] >= fecha_base - timedelta(days=d)]
            if not datos.empty:
                resultados[et] = calcular(datos)

        st.session_state["resultados"] = resultados

# =========================================
# TABLA ORIGINAL
# =========================================
if "resultados" in st.session_state:
    r = st.session_state["resultados"]

    st.markdown("---")
    st.subheader("📊 Top 28 por periodo")

    html = "<table style='width:100%; text-align:center;'>"
    html += "<tr>" + "".join(f"<th>{c}</th>" for c in r) + "</tr>"

    for i in range(28):
        html += "<tr>"
        for col in r:
            n = r[col].index[i]
            f = r[col].iloc[i]
            html += f"<td>{n} ({f})</td>"
        html += "</tr>"

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

    # ===== 15 DÍAS =====
    if "15 días" in r:
        base = r["15 días"]
        top6 = base.head(6).index.tolist()
        bottom6 = base.tail(6).index.tolist()
        inter = base.iloc[6:-6].index.tolist()

        st.markdown("---")
        st.markdown("<h4>📅 Análisis 15 días</h4>", unsafe_allow_html=True)

        st.write(f"Top 6 frecuentes: {top6}")
        st.write(f"Top 6 menos frecuentes: {bottom6}")
        st.write(f"Intermedios (16): {inter}")

        st.markdown("---")
        st.markdown("<h4>🎯 6 combinaciones (15 días)</h4>", unsafe_allow_html=True)

        if "c15" not in st.session_state:
            c,n = generar_combinaciones(top6,bottom6,inter)
            st.session_state["c15"], st.session_state["n15"] = c,n

        st.info(f"Nivel: {st.session_state['n15']}")
        for i,c in enumerate(st.session_state["c15"],1):
            st.write(f"{i}: {c}")

        if st.button("🔄 Generar nuevas (15 días)"):
            st.session_state["c15"], st.session_state["n15"] = generar_combinaciones(top6,bottom6,inter)

    # ===== 1 MES =====
    if "1 mes" in r:
        base = r["1 mes"]
        top6 = base.head(6).index.tolist()
        bottom6 = base.tail(6).index.tolist()
        inter = base.iloc[6:-6].index.tolist()

        st.markdown("---")
        st.markdown("<h4>📅 Análisis 1 mes</h4>", unsafe_allow_html=True)

        st.write(f"Top 6 frecuentes: {top6}")
        st.write(f"Top 6 menos frecuentes: {bottom6}")
        st.write(f"Intermedios (16): {inter}")

        st.markdown("---")
        st.markdown("<h4>🎯 6 combinaciones (1 mes)</h4>", unsafe_allow_html=True)

        if "c1m" not in st.session_state:
            c,n = generar_combinaciones(top6,bottom6,inter)
            st.session_state["c1m"], st.session_state["n1m"] = c,n

        st.info(f"Nivel: {st.session_state['n1m']}")
        for i,c in enumerate(st.session_state["c1m"],1):
            st.write(f"{i}: {c}")

        if st.button("🔄 Generar nuevas (1 mes)"):
            st.session_state["c1m"], st.session_state["n1m"] = generar_combinaciones(top6,bottom6,inter)
