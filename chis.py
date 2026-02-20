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
            frec = nums.value_counts().head(10)
            return frec

        etiquetas = {
            "1 semana": 7,
            "2 semanas": 14,
            "1 mes": 30,
            "2 meses": 60
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
        # TABLA HTML HORIZONTAL (FRECUENCIA EN GRIS)
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
