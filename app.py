import streamlit as st
import pandas as pd

# ==================================================
# CONFIGURACIÓN GENERAL
# ==================================================
st.set_page_config(
    page_title="Analizador de Frecuencias",
    layout="centered"
)

st.title("📊 Analizador de Frecuencias por Sorteo")

# ==================================================
# CARGA DEL CSV
# ==================================================
archivo = st.file_uploader("📂 Selecciona el archivo CSV", type=["csv"])

if archivo is not None:
    df = pd.read_csv(archivo, sep=None, engine="python")
    df.columns = df.columns.str.strip().str.lower()

    if "fecha" not in df.columns:
        st.error("❌ No se encontró la columna 'fecha'")
        st.stop()

    # Conversión de fechas
    df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["fecha"])

    if df.empty:
        st.error("❌ No hay fechas válidas en el archivo")
        st.stop()

    # Rango de fechas
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

    # ==================================================
    # CÁLCULO DE FRECUENCIAS
    # ==================================================
    if st.button("🔍 Calcular frecuencias"):
        datos = df[
            (df["fecha"] >= pd.to_datetime(inicio)) &
            (df["fecha"] <= pd.to_datetime(fin))
        ].reset_index(drop=True)

        if datos.empty:
            st.warning("⚠️ No hay sorteos en ese rango.")
            st.stop()

        # Índice par = Noche | índice impar = Tarde
        datos_noche = datos.iloc[::2]
        datos_tarde = datos.iloc[1::2]

        def mostrar_frecuencias(nombre, datos):
            st.subheader("🌙 Noche" if nombre == "Noche" else "☀️ Tarde")

            nums = datos.iloc[:, 1:6].values.flatten()
            nums = pd.to_numeric(nums, errors="coerce")
            nums = pd.Series(nums).dropna().astype(int)

            if nums.empty:
                st.warning("No hay números en este bloque.")
                return

            frec = nums.value_counts().sort_values(ascending=False)

            # 🔧 ALTURA DINÁMICA PARA EVITAR SCROLL
            altura = (len(frec) + 1) * 35  # 35px por fila aprox

            st.dataframe(
                frec.rename("Frecuencia"),
                height=altura
            )

        colA, colB = st.columns(2)
        with colA:
            mostrar_frecuencias("Noche", datos_noche)
        with colB:
            mostrar_frecuencias("Tarde", datos_tarde)
