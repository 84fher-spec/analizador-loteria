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

        datos_noche = datos.iloc[::2]
        datos_tarde = datos.iloc[1::2]

        # =========================================
        # CÁLCULO DE FRECUENCIAS
        # =========================================
        def calcular_frecuencia(df_bloque):
            nums = df_bloque[["r1", "r2", "r3", "r4", "r5"]]
            nums = nums.apply(pd.to_numeric, errors="coerce")
            nums = pd.Series(nums.values.flatten()).dropna().astype(int)
            frec = nums.value_counts().sort_values(ascending=False)
            return frec, frec.head(7).index.tolist()

        frec_noche, top7_noche = calcular_frecuencia(datos_noche)
        frec_tarde, top7_tarde = calcular_frecuencia(datos_tarde)
        frec_total, top7_total = calcular_frecuencia(datos)

        # =========================================
        # RESUMEN (JUSTO ABAJO DEL BOTÓN)
        # =========================================
        st.markdown("---")
        st.subheader("📌 Resumen de resultados")
        st.write("🌙 **Noche:**", top7_noche)
        st.write("☀️ **Tarde:**", top7_tarde)
        st.write("📊 **General:**", top7_total)

        # =========================================
        # TABLAS (SIN DUPLICADOS)
        # =========================================
        colA, colB = st.columns(2)

        with colA:
            st.subheader("🌙 Noche")
            st.table(frec_noche.rename("Frecuencia"))

        with colB:
            st.subheader("☀️ Tarde")
            st.table(frec_tarde.rename("Frecuencia"))

        st.markdown("---")
        st.subheader("📊 Frecuencias Generales (Día + Noche)")
        st.table(frec_total.rename("Frecuencia"))
