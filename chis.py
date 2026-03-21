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
# FUNCIONES
# =========================================
def generar_combinaciones(intermedios):

    def decenas_ok(comb, min_decenas=3):
        return len(set(n // 10 for n in comb)) >= min_decenas

    def pares_nones_ok(comb):
        pares = sum(n % 2 == 0 for n in comb)
        return pares in [2, 3]

    def contar_consecutivos(comb):
        comb = sorted(comb)
        return sum(1 for i in range(len(comb)-1) if comb[i]+1 == comb[i+1])

    def generar(nivel):
        for _ in range(5000):
            pool = intermedios * 2
            random.shuffle(pool)

            temp = []
            valido = True

            for i in range(6):
                comb = sorted(pool[i*5:(i+1)*5])

                if len(set(comb)) < 5:
                    valido = False
                    break

                if nivel == 1:
                    if not pares_nones_ok(comb): valido = False; break
                    if contar_consecutivos(comb) > 0: valido = False; break
                    if not decenas_ok(comb, 3): valido = False; break

                elif nivel == 2:
                    if contar_consecutivos(comb) > 0: valido = False; break
                    if not decenas_ok(comb, 3): valido = False; break

                elif nivel == 3:
                    if contar_consecutivos(comb) > 1: valido = False; break
                    if not decenas_ok(comb, 2): valido = False; break

                temp.append(comb)

            if valido and len(set(tuple(c) for c in temp)) == 6:
                return temp, nivel

        return None, None

    for nivel in [1, 2, 3]:
        res, lvl = generar(nivel)
        if res:
            return res, lvl

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

    if st.button("🔍 Calcular frecuencias"):

        fecha_base = df["fecha"].max()

        def calcular(df_bloque):
            nums = df_bloque[["r1","r2","r3","r4","r5"]]
            nums = nums.apply(pd.to_numeric, errors="coerce")
            nums = pd.Series(nums.values.flatten()).dropna().astype(int)
            return nums.value_counts().head(28)

        etiquetas = {"15 días":15,"1 mes":30,"2 meses":60,"3 meses":90}
        resultados = {}

        for et, d in etiquetas.items():
            datos = df[df["fecha"] >= fecha_base - timedelta(days=d)]
            if not datos.empty:
                resultados[et] = calcular(datos)

        # GUARDAR
        st.session_state["resultados"] = resultados

        if "15 días" in resultados:
            st.session_state["intermedios"] = resultados["15 días"].iloc[6:21].index.tolist()

            combs, nivel = generar_combinaciones(st.session_state["intermedios"])
            st.session_state["combinaciones"] = combs
            st.session_state["nivel"] = nivel


# =========================================
# MOSTRAR TABLA
# =========================================
if "resultados" in st.session_state:

    resultados = st.session_state["resultados"]

    st.markdown("---")
    st.subheader("📊 Top 28 por periodo")

    html = "<table style='width:100%; text-align:center;'>"
    html += "<tr>" + "".join(f"<th>{c}</th>" for c in resultados) + "</tr>"

    for i in range(28):
        html += "<tr>"
        for col in resultados:
            if i < len(resultados[col]):
                n = resultados[col].index[i]
                f = resultados[col].iloc[i]
                html += f"<td>{n} <span style='color:#888'>({f})</span></td>"
            else:
                html += "<td></td>"
        html += "</tr>"

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)


# =========================================
# MOSTRAR COMBINACIONES
# =========================================
if "combinaciones" in st.session_state:

    st.markdown("---")
    st.subheader("🎯 Combinaciones generadas")

    if st.session_state["combinaciones"]:
        st.info(f"Nivel usado: {st.session_state['nivel']}")
        for i, c in enumerate(st.session_state["combinaciones"], 1):
            st.write(f"Combinación {i}: {c}")
    else:
        st.warning("No fue posible generar las combinaciones")


# =========================================
# BOTÓN NUEVO (NO BORRA NADA)
# =========================================
if "intermedios" in st.session_state:

    if st.button("🔄 Generar nueva combinación"):

        combs, nivel = generar_combinaciones(st.session_state["intermedios"])
        st.session_state["combinaciones"] = combs
        st.session_state["nivel"] = nivel
