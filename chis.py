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
# RESPONSIVE SOLO PARA LAS 3 COLUMNAS
# DE RESULTADOS
# =========================================

st.markdown("""
<style>
@media (max-width: 768px) {

    /* SOLO afecta al contenedor de resultados */
    .st-key-resultados_columnas [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 0.15rem !important;
    }

    .st-key-resultados_columnas [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        min-width: 0 !important;
        width: 33.3333% !important;
        max-width: 33.3333% !important;
        flex: 1 1 33.3333% !important;
    }

    .st-key-resultados_columnas [data-testid="column"] > div {
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
}
</style>
""", unsafe_allow_html=True)

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
# CLASIFICACIÓN
# =========================================

def clasificar_numeros(nums):
    unidades = [n for n in nums if 1 <= n <= 9]
    decenas = [n for n in nums if 10 <= n <= 19]
    veintenas = [n for n in nums if 20 <= n <= 28]
    return unidades, decenas, veintenas

# =========================================
# SELECCIÓN POR GRUPO (con fallback global)
# =========================================

def seleccionar_grupo(candidatos, todos, cantidad):
    candidatos = list(set(candidatos))
    todos = list(set(todos))

    if len(candidatos) >= cantidad:
        return random.sample(candidatos, cantidad)

    faltan = cantidad - len(candidatos)
    resto = [n for n in todos if n not in candidatos]

    seleccion_extra = random.sample(resto, min(faltan, len(resto)))
    resultado = candidatos + seleccion_extra

    while len(resultado) < cantidad:
        resultado.append(random.choice(todos))

    return resultado[:cantidad]

# =========================================
# 15 NÚMEROS (5-5-5 EXACTO)
# =========================================

def seleccionar_15_intermedios(base, full):

    u_base, d_base, v_base = clasificar_numeros(base)
    u_full, d_full, v_full = clasificar_numeros(full)

    sel_u = seleccionar_grupo(u_base, u_full, 5)
    sel_d = seleccionar_grupo(d_base, d_full, 5)
    sel_v = seleccionar_grupo(v_base, v_full, 5)

    return sel_u + sel_d + sel_v

# =========================================
# 10 NÚMEROS (3-4-3 EXACTO)
# =========================================

def seleccionar_10_intermedios(base, full):

    u_base, d_base, v_base = clasificar_numeros(base)
    u_full, d_full, v_full = clasificar_numeros(full)

    sel_u = seleccionar_grupo(u_base, u_full, 3)
    sel_d = seleccionar_grupo(d_base, d_full, 4)
    sel_v = seleccionar_grupo(v_base, v_full, 3)

    return sel_u + sel_d + sel_v

# =========================================
# GENERADOR (MODIFICADO)
# =========================================

def generar(pool_base, repeticiones):

    total_nums = len(pool_base)
    num_combinaciones = total_nums // 5  # 15→3, 10→2

    def generar_nivel(nivel):
        for _ in range(5000):

            pool = pool_base[:]
            random.shuffle(pool)

            temp = []
            valido = True

            for i in range(num_combinaciones):
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

            if valido and len(set(tuple(c) for c in temp)) == num_combinaciones:
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

    st.markdown("---")
    st.subheader("✍️ Agregar registro manual")

    col1, col2, col3, col4, col5 = st.columns(5)

    r1 = col1.number_input("R1", 1, 28)
    r2 = col2.number_input("R2", 1, 28)
    r3 = col3.number_input("R3", 1, 28)
    r4 = col4.number_input("R4", 1, 28)
    r5 = col5.number_input("R5", 1, 28)

    usar_manual = st.checkbox("Usar este registro en el cálculo")

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

            conteo = nums.value_counts()
            conteo = conteo.reindex(range(1, 29), fill_value=0)
            conteo = conteo.sort_values(ascending=False)

            return conteo.head(28)

        etiquetas = {
            "1 semana": 7,
            "15 días": 15,
            "1 mes": 30
        }

        resultados = {}

        for et, d in etiquetas.items():
            datos = df_calculo[df_calculo["fecha"] >= fecha_base - timedelta(days=d)]
            if not datos.empty:
                resultados[et] = calcular(datos)

        st.session_state["resultados"] = resultados

# =========================================
# RESULTADOS AGRUPADOS POR DECENAS
# =========================================

if "resultados" in st.session_state:

    r = st.session_state["resultados"]

    st.markdown("---")
    st.subheader("📊 Resultados por periodo")

    periodos_mostrar = ["1 semana", "15 días", "1 mes"]

    grupos = {
        "1-9": range(1, 10),
        "10-19": range(10, 20),
        "20-28": range(20, 29)
    }

    for periodo in periodos_mostrar:

        if periodo in r:

            # Título más pequeño
            st.markdown(f"#### 📅 {periodo}")

            serie = r[periodo]

            # =========================================
            # CONTENEDOR EXCLUSIVO DE LAS 3 COLUMNAS
            # =========================================

            with st.container(key="resultados_columnas"):

                columnas = st.columns(3)

                for idx, (nombre_grupo, rango) in enumerate(grupos.items()):

                    grupo = serie[serie.index.isin(rango)]
                    grupo = grupo.sort_values(ascending=False)

                    with columnas[idx]:

                        # Encabezado simple
                        st.markdown(
                            f"<div style='text-align:center; font-weight:bold; margin-bottom:6px;'>{nombre_grupo}</div>",
                            unsafe_allow_html=True
                        )

                        # Lista compacta
                        html = ""
                        for numero, frecuencia in grupo.items():
                            html += (
                                f"<div style='text-align:center; margin:2px 0;'>"
                                f"<span style='font-weight:600;'>{numero}</span> "
                                f"<span style='color:#888;'>({frecuencia})</span>"
                                f"</div>"
                            )

                        st.markdown(html, unsafe_allow_html=True)

            st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
