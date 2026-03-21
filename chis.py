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
# FUNCIONES BASE
# =========================================
def decenas_ok(comb, min_decenas=3):
    return len(set(n // 10 for n in comb)) >= min_decenas

def pares_nones_ok(comb):
    pares = sum(n % 2 == 0 for n in comb)
    return pares in [2, 3]

def contar_consecutivos(comb):
    comb = sorted(comb)
    return sum(1 for i in range(len(comb)-1) if comb[i] + 1 == comb[i+1])

# =========================================
# GENERADOR GENERAL
# =========================================
def generar(pool_base, repeticiones):

    def generar_nivel(nivel):
        for _ in range(5000):

            pool = pool_base * repeticiones
            random.shuffle(pool)

            temp = []
            valido = True

            for i in range(6):
                comb = sorted(pool[i*5:(i+1)*5])

                # evitar repetidos dentro de la combinación
                if len(set(comb)) < 5:
                    valido = False
                    break

                # NIVEL 1 (estricto)
                if nivel == 1:
                    if not pares_nones_ok(comb): valido = False; break
                    if contar_consecutivos(comb) > 0: valido = False; break
                    if not decenas_ok(comb, 3): valido = False; break

                # NIVEL 2
                elif nivel == 2:
                    if contar_consecutivos(comb) > 0: valido = False; break
                    if not decenas_ok(comb, 3): valido = False; break

                # NIVEL 3
                elif nivel == 3:
                    if contar_consecutivos(comb) > 1: valido = False; break
                    if not decenas_ok(comb, 2): valido = False; break

                temp.append(comb)

            if valido and len(set(tuple(c) for c in temp)) == 6:
                return temp, nivel

        return None, None

    for nivel in [1, 2, 3]:
        r, n = generar_nivel(nivel)
        if r:
            return r, n

    return None, None

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
    # INPUT MANUAL
    # =========================================
    st.markdown("---")
    st.subheader("✍️ Agregar registro manual")

    col1, col2, col3, col4, col5 = st.columns(5)

    r1 = col1.number_input("R1", 1, 100, step=1)
    r2 = col2.number_input("R2", 1, 100, step=1)
    r3 = col3.number_input("R3", 1, 100, step=1)
    r4 = col4.number_input("R4", 1, 100, step=1)
    r5 = col5.number_input("R5", 1, 100, step=1)

    usar_manual = st.checkbox("Usar este registro en el cálculo")

    # =========================================
    # BOTÓN PRINCIPAL
    # =========================================
    if st.button("🔍 Calcular frecuencias"):

        df_calculo = df.copy()

        if usar_manual:
            nueva_fecha = df["fecha"].max() + timedelta(days=1)

            nuevo = pd.DataFrame([{
                "r1": r1, "r2": r2, "r3": r3,
                "r4": r4, "r5": r5,
                "fecha": nueva_fecha
            }])

            df_calculo = pd.concat([df_calculo, nuevo], ignore_index=True)

        fecha_base = df_calculo["fecha"].max()

        def calcular(df_bloque):
            nums = df_bloque[["r1","r2","r3","r4","r5"]]
            nums = nums.apply(pd.to_numeric, errors="coerce")
            nums = pd.Series(nums.values.flatten()).dropna().astype(int)
            return nums.value_counts().head(28)

        etiquetas = {
            "15 días": 15,
            "1 mes": 30,
            "2 meses": 60,
            "3 meses": 90
        }

        resultados = {}

        for et, d in etiquetas.items():
            datos = df_calculo[df_calculo["fecha"] >= fecha_base - timedelta(days=d)]
            if not datos.empty:
                resultados[et] = calcular(datos)

        st.session_state["resultados"] = resultados

        # =========================================
        # 15 DÍAS
        # =========================================
        if "15 días" in resultados:
            base = resultados["15 días"]

            st.session_state["i15"] = base.iloc[6:21].index.tolist()
            st.session_state["i10"] = base.iloc[8:18].index.tolist()

            st.session_state["c15"], st.session_state["n15"] = generar(st.session_state["i15"], 2)
            st.session_state["c10"], st.session_state["n10"] = generar(st.session_state["i10"], 3)

        # =========================================
        # 1 MES
        # =========================================
        if "1 mes" in resultados:
            base = resultados["1 mes"]

            st.session_state["i15_m"] = base.iloc[6:21].index.tolist()
            st.session_state["i10_m"] = base.iloc[8:18].index.tolist()

            st.session_state["c15_m"], st.session_state["n15_m"] = generar(st.session_state["i15_m"], 2)
            st.session_state["c10_m"], st.session_state["n10_m"] = generar(st.session_state["i10_m"], 3)

# =========================================
# TABLA RESULTADOS
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
            if i < len(r[col]):
                n = r[col].index[i]
                f = r[col].iloc[i]
                html += f"<td>{n} <span style='color:#888'>({f})</span></td>"
            else:
                html += "<td></td>"
        html += "</tr>"

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)

# =========================================
# FUNCIÓN DISPLAY
# =========================================
def mostrar(titulo, key_c, key_n, key_i, rep, boton):

    if key_c in st.session_state:

        st.markdown("---")
        st.subheader(titulo)

        if st.session_state[key_c]:
            st.info(f"Nivel: {st.session_state[key_n]}")
            for i, c in enumerate(st.session_state[key_c], 1):
                st.write(f"{i}: {c}")
        else:
            st.warning("No fue posible generar las combinaciones")

        if st.button(boton):
            c, n = generar(st.session_state[key_i], rep)
            st.session_state[key_c] = c
            st.session_state[key_n] = n

# =========================================
# BLOQUES
# =========================================

# 15 días
mostrar("🎯 15 números (15 días x2)", "c15","n15","i15",2,"🔄 Generar nuevas (15 días)")
mostrar("🎯 10 números (15 días x3)", "c10","n10","i10",3,"🔄 Generar nuevas (10 días)")

# 1 mes
mostrar("🎯 15 números (1 mes x2)", "c15_m","n15_m","i15_m",2,"🔄 Generar nuevas (15 números - 1 mes)")
mostrar("🎯 10 números (1 mes x3)", "c10_m","n10_m","i10_m",3,"🔄 Generar nuevas (10 números - 1 mes)")
