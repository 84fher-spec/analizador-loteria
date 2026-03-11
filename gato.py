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

    columnas_esperadas = {
        "nproducto","concurso",
        "f1","f2","f3","f4","f5","f6","f7","f8",
        "bolsa","fecha"
    }

    if not columnas_esperadas.issubset(set(df.columns)):
        st.error(
            "❌ El archivo debe contener las columnas:\n"
            "NPRODUCTO, CONCURSO, F1, F2, F3, F4, F5, F6, F7, F8, BOLSA, FECHA"
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

        def calcular_top5_por_posicion(df_bloque):

            posiciones = ["f1","f2","f3","f4","f5","f6","f7","f8"]
            resultado = {}

            for pos in posiciones:

                nums = pd.to_numeric(df_bloque[pos], errors="coerce")
                nums = nums.dropna().astype(int)

                frec = nums.value_counts().head(5)

                resultado[pos.upper()] = frec

            return resultado


        etiquetas = {
            "2 meses": 60,
            "4 meses": 120,
            "6 meses": 180,
            "8 meses": 240
        }

        resultados = {}

        for etiqueta, dias in etiquetas.items():

            fecha_inicio = fecha_base - timedelta(days=dias)
            datos_periodo = df[df["fecha"] >= fecha_inicio]

            if datos_periodo.empty:
                continue

            resultados[etiqueta] = calcular_top5_por_posicion(datos_periodo)


        # =========================================
        # MOSTRAR RESULTADOS
        # =========================================
        st.markdown("---")
        st.subheader("📊 Top 5 por posición")

        for periodo, datos in resultados.items():

            st.markdown(f"### {periodo}")

            html = "<table style='width:100%; border-collapse:collapse; text-align:center;'>"
            html += "<tr>"

            for pos in datos.keys():
                html += f"<th style='padding:4px;border-bottom:1px solid #ccc;'>{pos}</th>"

            html += "</tr>"

            for i in range(5):

                html += "<tr>"

                for pos in datos.keys():

                    if i < len(datos[pos]):

                        num = datos[pos].index[i]
                        freq = datos[pos].iloc[i]

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
