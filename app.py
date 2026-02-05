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

    # Normalizar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()

    # Validar columnas obligatorias
    columnas_esperadas = {"concurso", "r1", "r2", "r3", "r4", "r5", "fecha"}
    if not columnas_esperadas.issubset(set(df.columns)):
        st.error(
            "❌ El archivo debe contener las columnas:\n"
            "CONCURSO, R1, R2, R3, R4, R5, FECHA"
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

        # fila 0 → Noche
        # fila 1 → Tarde
        datos_noche = datos.iloc[::2]
        datos_tarde = datos.iloc[1::2]

        # =========================================
        # FUNCIÓN PARA MOSTRAR TABLA
        # =========================================
        def mostrar_tabla(nombre, datos_bloque):
            st.subheader("🌙 Noche" if nombre == "Noche" else "☀️ Tarde")

            nums = datos_bloque[["r1", "r2", "r3", "r4", "r5"]]
            nums = nums.apply(pd.to_numeric, errors="coerce")

            nums = nums.values.flatten()
            nums = pd.Series(nums).dropna().astype(int)

            if nums.empty:
                st.warning("No hay números en este bloque.")
                return

            frec = nums.value_counts().sort_values(ascending=False)

            # MOSTRAR TABLA (SIN BARRA DE DESPLAZAMIENTO)
            st.table(frec.rename("Frecuencia"))

        # =========================================
        # MOSTRAR BLOQUES
        # =========================================
        colA, colB = st.columns(2)

        with colA:
            mostrar_tabla("Noche", datos_noche)

        with colB:
            mostrar_tabla("Tarde", datos_tarde)
