import streamlit as st
import pandas as pd
import io
from datetime import timedelta

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
    "📂 Selecciona el archivo CSV",
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

    # =========================================
    # DETECCIÓN DE FORMATO
    # =========================================
    columnas_r = {"r1", "r2", "r3", "r4", "r5"}
    columnas_f = {"f1", "f2", "f3", "f4", "f5", "f6", "f7"}

    if "fecha" not in df.columns:
        st.error("❌ El archivo debe contener la columna FECHA")
        st.stop()

    if columnas_r.issubset(df.columns):
        columnas_numeros = ["r1", "r2", "r3", "r4", "r5"]
    elif columnas_f.issubset(df.columns):
        columnas_numeros = ["f1", "f2", "f3", "f4", "f5", "f6", "f7"]
    else:
        st.error(
            "❌ El archivo debe contener:\n"
            "- R1 a R5 + FECHA  **o**\n"
            "- F1 a F7 + FECHA"
        )
        st.stop()

    # =========================================
    # PROCESAMIENTO DE FECHAS
    # =========================================
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
            nums = df_bloque[columnas_numeros]
            nums = nums.apply(pd.to_numeric, errors="coerce")
            nums = pd.Series(nums.values.flatten()).dropna().astype(int)
            return nums.value_counts().head(10)

        # =========================================
        # RANGOS EN MESES (ACTUALIZADO)
        # =========================================
        etiquetas = {
            "1 mes": 30,
            "2 meses": 60,
            "3 meses": 90,
            "4 meses": 120
        }

        resultados = {}

        for etiqueta, dias in etiquetas.items():
            fecha_inicio = fecha_base - timedelta(days=dias)
            datos_periodo = df[df["fecha"] >= fecha_inicio]

            if datos_periodo.empty:
                continue

            resultados[etiqueta] = calcular_top10(datos_periodo)

        # =========================================
        # TABLA HORIZONTAL (FRECUENCIA EN GRIS)
        # =========================================
        st.markdown("---")
        st.subheader("📊 Top 10 por periodo")

        html = "<table style='width:100%; border-collapse:collapse; text-align:center;'>"
        html += "<tr>"

        for col in resultados.keys():
            html += f"<th style='padding:4px; border-bottom:1px solid #ccc;'>{col}</th>"
        html += "</tr>"

        for i in range(10):
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
