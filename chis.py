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
# CARGA DEL CSV
# =========================================
archivo = st.file_uploader(
    "📂 Selecciona el archivo CSV (Lotería Nacional)",
    type=None,
    accept_multiple_files=False
)

if archivo is not None:

    try:
        df = pd.read_csv(
            io.BytesIO(archivo.read()),
            sep=",",
            encoding="latin-1",
            engine="python"
        )
    except Exception as e:
        st.error("❌ No se pudo leer el archivo CSV")
        st.code(str(e))
        st.stop()

    df.columns = df.columns.str.strip().str.lower()

    columnas_esperadas = {"concurso", "r1", "r2", "r3", "r4", "r5", "fecha"}
    if not columnas_esperadas.issubset(set(df.columns)):
        st.error(
            "❌ El archivo debe contener las columnas:\n"
            "CONCURSO, R1, R2, R3, R4, R5, FECHA"
        )
        st.stop()

    df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["fecha"])

    if df.empty:
        st.error("❌ No hay fechas válidas en el archivo.")
        st.stop()

    # =========================================
    # BOTÓN DE PROCESO
    # =========================================
    if st.button("🔍 Calcular frecuencias"):

        fecha_base = df["fecha"].max()

        def calcular_top10(df_bloque):
            nums = df_bloque[["r1", "r2", "r3", "r4", "r5"]]
            nums = nums.apply(pd.to_numeric, errors="coerce")
            nums = pd.Series(nums.values.flatten()).dropna().astype(int)
            frec = nums.value_counts().head(28)
            return frec

        etiquetas = {
            "15 días": 15,
            "1 mes": 30,
            "2 meses": 60,
            "3 meses": 90
        }

        resultados = {}

        for etiqueta, dias in etiquetas.items():
            fecha_inicio = fecha_base - timedelta(days=dias)
            datos_periodo = df[df["fecha"] >= fecha_inicio]

            if datos_periodo.empty:
                continue

            top10 = calcular_top10(datos_periodo)
            resultados[etiqueta] = top10

        # =========================================
        # TABLA
        # =========================================
        st.markdown("---")
        st.subheader("📊 Top 28 por periodo")

        html = "<table style='width:100%; border-collapse:collapse; text-align:center;'>"
        html += "<tr>"

        for col in resultados.keys():
            html += f"<th style='padding:4px; border-bottom:1px solid #ccc;'>{col}</th>"
        html += "</tr>"

        for i in range(28):
            html += "<tr>"
            for col in resultados.keys():
                if i < len(resultados[col]):
                    num = resultados[col].index[i]
                    freq = resultados[col].iloc[i]
                    html += (
                        "<td style='padding:4px;'>"
                        f"{num} <span style='color:#888;'>({freq})</span>"
                        "</td>"
                    )
                else:
                    html += "<td></td>"
            html += "</tr>"

        html += "</table>"

        st.markdown(html, unsafe_allow_html=True)

        # =========================================
        # GENERACIÓN DE COMBINACIONES (ROBUSTA)
        # =========================================
        st.markdown("---")
        st.subheader("🎯 Combinaciones generadas")

        if "15 días" in resultados:

            lista_15 = resultados["15 días"]
            intermedios = lista_15.iloc[6:21].index.tolist()

            def decenas_ok(comb, min_decenas=3):
                decenas = [n // 10 for n in comb]
                return len(set(decenas)) >= min_decenas

            def pares_nones_ok(comb):
                pares = sum(1 for n in comb if n % 2 == 0)
                return pares in [2, 3]

            def contar_consecutivos(comb):
                comb_sorted = sorted(comb)
                count = 0
                for i in range(len(comb_sorted) - 1):
                    if comb_sorted[i] + 1 == comb_sorted[i+1]:
                        count += 1
                return count

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

                        # NIVEL 1 (estricto)
                        if nivel == 1:
                            if not pares_nones_ok(comb):
                                valido = False
                                break
                            if contar_consecutivos(comb) > 0:
                                valido = False
                                break
                            if not decenas_ok(comb, 3):
                                valido = False
                                break

                        # NIVEL 2 (relaja pares/nones)
                        elif nivel == 2:
                            if contar_consecutivos(comb) > 0:
                                valido = False
                                break
                            if not decenas_ok(comb, 3):
                                valido = False
                                break

                        # NIVEL 3 (más flexible)
                        elif nivel == 3:
                            if contar_consecutivos(comb) > 1:
                                valido = False
                                break
                            if not decenas_ok(comb, 2):
                                valido = False
                                break

                        temp.append(comb)

                    if valido and len(set(tuple(c) for c in temp)) == 6:
                        return temp

                return None

            combinaciones = None

            for nivel in [1, 2, 3]:
                combinaciones = generar(nivel)
                if combinaciones:
                    st.info(f"Combinaciones generadas con nivel {nivel}")
                    break

            if combinaciones:
                for i, c in enumerate(combinaciones, 1):
                    st.write(f"Combinación {i}: {c}")
            else:
                st.warning("No se pudo generar combinaciones ni relajando restricciones.")
