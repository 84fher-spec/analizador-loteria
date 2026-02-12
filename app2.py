import streamlit as st
import pandas as pd
import io

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

    # Normalizar columnas
    df.columns = df.columns.str.strip().str.lower()

    # Validar columnas obligatorias
    columnas_esperadas = {
        "nproducto", "concurso",
        "f1", "f2", "f3", "f4", "f5", "f6", "f7",
        "bolsa", "fecha"
    }

    if not columnas_esperadas.issubset(set(df.columns)):
        st.error(
            "❌ El archivo debe contener las columnas:\n"
            "NPRODUCTO, CONCURSO, F1, F2, F3, F4, F5, F6, F7, BOLSA, FECHA"
        )
        st.stop()

    # Convertir fecha
    df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["fecha"])

    if df.empty:
        st.error("❌ No hay fechas válidas en el archivo.")
        st.stop()

    # =========================================
    # SELECCIÓN DE FECHAS
    # =========================================
    fecha_min = df["fecha"].min().date()
    fecha_max = df["fecha"].max().date()

    col1, col2 = st.columns(2)
    with col1:
        inicio = st.date_input(
            "📅 Fecha inicial",
            value=fecha_min,
            min_value=fecha_min,
            max_value=fecha_max
        )
    with col2:
        fin = st.date_input(
            "📅 Fecha final",
            value=fecha_max,
            min_value=fecha_min,
            max_value=fecha_max
        )

    if inicio > fin:
        st.warning("⚠️ La fecha inicial no puede ser mayor que la final.")
        st.stop()

    # =========================================
    # PROCESAR DATOS
    # =========================================
    if st.button("🔍 Calcular frecuencias"):

        datos = df[
            (df["fecha"] >= pd.to_datetime(inicio)) &
            (df["fecha"] <= pd.to_datetime(fin))
        ].reset_index(drop=True)

        if datos.empty:
            st.warning("⚠️ No hay sorteos en ese rango.")
            st.stop()

        # =========================================
        # CÁLCULO GENERAL
        # =========================================
        nums = datos[["f1", "f2", "f3", "f4", "f5", "f6", "f7"]]
        nums = nums.apply(pd.to_numeric, errors="coerce")

        nums = pd.Series(nums.values.flatten()).dropna().astype(int)

        if nums.empty:
            st.warning("⚠️ No hay números para calcular.")
            st.stop()

        frec = nums.value_counts().sort_values(ascending=False)
        top10 = frec.head(10).index.tolist()

        # =========================================
        # RESUMEN
        # =========================================
        st.markdown("---")
        st.subheader("📌 Resumen de resultados")
        st.write("🔝 **Top 10 números más frecuentes:**", top10)

        # =========================================
        # TABLA GENERAL
        # =========================================
        st.markdown("---")
        st.subheader("📊 Frecuencias Generales")
        st.table(frec.rename("Frecuencia"))
