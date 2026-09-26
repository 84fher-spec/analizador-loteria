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
# GENERAR 3 COMBINACIONES DESDE SELECCIÓN
# =========================================

def generar_3_combinaciones_semana(numeros):

    numeros = list(dict.fromkeys(int(n) for n in numeros))

    if len(numeros) < 5:
        return []

    cantidad_total = min(15, len(numeros))

    grupos = {
        1: [n for n in numeros if 1 <= n <= 9],
        2: [n for n in numeros if 10 <= n <= 19],
        3: [n for n in numeros if 20 <= n <= 28]
    }

    objetivo = cantidad_total

    mejor_seleccion = None
    mejor_combinaciones = None
    mejor_puntuacion = None

    for _ in range(5000):

        # -----------------------------------------
        # SELECCIÓN DE LOS NÚMEROS
        # -----------------------------------------

        if len(numeros) > objetivo:

            candidatos = numeros[:]
            random.shuffle(candidatos)

            seleccion = candidatos[:objetivo]

            # Mejoramos la distribución global de decenas
            # buscando cantidades lo más cercanas posible.
            mejor_local = None
            mejor_score_local = None

            for _ in range(100):

                prueba = random.sample(numeros, objetivo)

                cantidades = [
                    sum(1 for n in prueba if 1 <= n <= 9),
                    sum(1 for n in prueba if 10 <= n <= 19),
                    sum(1 for n in prueba if 20 <= n <= 28)
                ]

                score = max(cantidades) - min(cantidades)

                if mejor_score_local is None or score < mejor_score_local:
                    mejor_score_local = score
                    mejor_local = prueba

                    if score == 0:
                        break

            seleccion = mejor_local

        else:
            seleccion = numeros[:]

        random.shuffle(seleccion)

        # -----------------------------------------
        # SEPARAR EN 3 COMBINACIONES
        # -----------------------------------------

        combinaciones = [
            seleccion[i:i+5]
            for i in range(0, len(seleccion), 5)
        ]

        if len(combinaciones) < 3 or any(len(c) < 5 for c in combinaciones):
            continue

        combinaciones = [sorted(c) for c in combinaciones]

        # -----------------------------------------
        # PUNTUACIÓN DE EQUILIBRIO
        # -----------------------------------------

        cantidades_globales = [
            sum(1 for n in seleccion if 1 <= n <= 9),
            sum(1 for n in seleccion if 10 <= n <= 19),
            sum(1 for n in seleccion if 20 <= n <= 28)
        ]

        diferencia_global = max(cantidades_globales) - min(cantidades_globales)

        diferencia_combos = 0

        for comb in combinaciones:

            cantidades = [
                sum(1 for n in comb if 1 <= n <= 9),
                sum(1 for n in comb if 10 <= n <= 19),
                sum(1 for n in comb if 20 <= n <= 28)
            ]

            diferencia_combos += max(cantidades) - min(cantidades)

        concentracion = 0

        for comb in combinaciones:

            cantidades = [
                sum(1 for n in comb if 1 <= n <= 9),
                sum(1 for n in comb if 10 <= n <= 19),
                sum(1 for n in comb if 20 <= n <= 28)
            ]

            if max(cantidades) >= 4:
                concentracion += 3

        puntuacion = (
            diferencia_global * 10
            + diferencia_combos
            + concentracion
        )

        if mejor_puntuacion is None or puntuacion < mejor_puntuacion:
            mejor_puntuacion = puntuacion
            mejor_seleccion = seleccion[:]
            mejor_combinaciones = combinaciones

    return mejor_combinaciones if mejor_combinaciones else []


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
            "15 días": 15
        }

        resultados = {}

        for et, d in etiquetas.items():
            datos = df_calculo[df_calculo["fecha"] >= fecha_base - timedelta(days=d)]
            if not datos.empty:
                resultados[et] = calcular(datos)

        # =========================================
        # HISTÓRICO COMPLETO
        # =========================================

        resultados["Histórico completo"] = calcular(df_calculo)

        st.session_state["resultados"] = resultados

# =========================================
# RESULTADOS AGRUPADOS POR DECENAS
# =========================================

if "resultados" in st.session_state:

    r = st.session_state["resultados"]

    st.markdown("---")
    st.subheader("📊 Resultados por periodo")

    periodos_mostrar = [
        "1 semana",
        "15 días",
        "Histórico completo"
    ]

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
            # 3 COLUMNAS FIJAS EN UNA SOLA FILA
            # SOLO PARA RESULTADOS
            # =========================================

            bloques_html = ""

            for nombre_grupo, rango in grupos.items():

                grupo = serie[serie.index.isin(rango)]
                grupo = grupo.sort_values(ascending=False)

                lista_html = ""

                for numero, frecuencia in grupo.items():
                    lista_html += (
                        f"<div style='"
                        f"text-align:center;"
                        f"margin:2px 0;"
                        f"white-space:nowrap;"
                        f"font-size:17px;"
                        f"line-height:1.25;"
                        f"'>"
                        f"<span style='font-weight:600;'>{numero}</span> "
                        f"<span style='color:#888;'>({frecuencia})</span>"
                        f"</div>"
                    )

                bloques_html += (
                    f"<div style='"
                    f"flex:1 1 0;"
                    f"min-width:0;"
                    f"width:33.333%;"
                    f"box-sizing:border-box;"
                    f"padding:0 2px;"
                    f"'>"
                    f"<div style='"
                    f"text-align:center;"
                    f"font-weight:bold;"
                    f"margin-bottom:6px;"
                    f"white-space:nowrap;"
                    f"font-size:14px;"
                    f"'>"
                    f"{nombre_grupo}"
                    f"</div>"
                    f"{lista_html}"
                    f"</div>"
                )

            st.markdown(
                f"""
                <div style="
                    display:flex;
                    flex-direction:row;
                    flex-wrap:nowrap;
                    width:100%;
                    max-width:100%;
                    box-sizing:border-box;
                    overflow:hidden;
                    align-items:flex-start;
                    justify-content:space-between;
                ">
                    {bloques_html}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

# =========================================
# SELECCIÓN DE NÚMEROS DE UNA SEMANA
# =========================================

if "resultados" in st.session_state and "1 semana" in st.session_state["resultados"]:

    st.markdown("---")
    st.subheader("🎯 Selección de números de una semana")

    serie_semana = st.session_state["resultados"]["1 semana"]

    # Descartar números con frecuencia de 0 a 1
    candidatos = serie_semana[serie_semana >= 2]

    if not candidatos.empty:

        # Obtener las dos frecuencias más altas
        frecuencias_altas = sorted(candidatos.unique(), reverse=True)[:2]

        # Descartar los números pertenecientes a los niveles
        # de frecuencia más altos 1 y 2
        intermedios = candidatos[
            ~candidatos.isin(frecuencias_altas)
        ]

        if not intermedios.empty:

            bloques_html = ""

            for nombre_grupo, rango in grupos.items():

                grupo = intermedios[
                    intermedios.index.isin(rango)
                ].sort_values(ascending=False)

                lista_html = ""

                for numero, frecuencia in grupo.items():
                    lista_html += (
                        f"<div style='"
                        f"text-align:center;"
                        f"margin:2px 0;"
                        f"white-space:nowrap;"
                        f"font-size:17px;"
                        f"line-height:1.25;"
                        f"'>"
                        f"<span style='font-weight:600;'>{numero}</span> "
                        f"<span style='color:#888;'>({frecuencia})</span>"
                        f"</div>"
                    )

                bloques_html += (
                    f"<div style='"
                    f"flex:1 1 0;"
                    f"min-width:0;"
                    f"width:33.333%;"
                    f"box-sizing:border-box;"
                    f"padding:0 2px;"
                    f"'>"
                    f"<div style='"
                    f"text-align:center;"
                    f"font-weight:bold;"
                    f"margin-bottom:6px;"
                    f"white-space:nowrap;"
                    f"font-size:14px;"
                    f"'>"
                    f"{nombre_grupo}"
                    f"</div>"
                    f"{lista_html}"
                    f"</div>"
                )

            st.markdown(
                f"""
                <div style="
                    display:flex;
                    flex-direction:row;
                    flex-wrap:nowrap;
                    width:100%;
                    max-width:100%;
                    box-sizing:border-box;
                    overflow:hidden;
                    align-items:flex-start;
                    justify-content:space-between;
                ">
                    {bloques_html}
                </div>
                """,
                unsafe_allow_html=True
            )

        else:
            st.info("No hay números intermedios disponibles con estos criterios.")

    else:
        st.info("No hay números con frecuencia de 2 o más en la semana.")

# =========================================
# 3 COMBINACIONES DE LA SELECCIÓN SEMANAL
# =========================================

if "resultados" in st.session_state and "1 semana" in st.session_state["resultados"]:

    serie_semana = st.session_state["resultados"]["1 semana"]

    # -----------------------------------------
    # RECONSTRUIR EXACTAMENTE LA SELECCIÓN
    # DE NÚMEROS INTERMEDIOS DE UNA SEMANA
    # -----------------------------------------

    candidatos = serie_semana[serie_semana >= 2]

    if not candidatos.empty:

        frecuencias_altas = sorted(candidatos.unique(), reverse=True)[:2]

        intermedios = candidatos[
            ~candidatos.isin(frecuencias_altas)
        ]

        numeros_seleccion = list(intermedios.index)

        # -----------------------------------------
        # GENERAR LAS 3 COMBINACIONES
        # -----------------------------------------

        combinaciones_semana = generar_3_combinaciones_semana(
            numeros_seleccion
        )

        if len(combinaciones_semana) == 3:

            st.markdown("---")
            st.subheader("🎲 3 combinaciones de la selección semanal")

            for i, comb in enumerate(combinaciones_semana, 1):

                texto = ", ".join(str(n) for n in comb)

                st.markdown(
                    f"<div style='"
                    f"text-align:center;"
                    f"font-size:20px;"
                    f"font-weight:600;"
                    f"margin:8px 0;"
                    f"'>"
                    f"<span style='color:#888;'>Combinación {i}:</span> "
                    f"<span>{texto}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

        elif len(numeros_seleccion) < 15:

            st.info(
                f"La selección semanal contiene solamente "
                f"{len(numeros_seleccion)} números intermedios, "
                f"por lo que no es posible formar 3 combinaciones "
                f"completas de 5 números sin repetir."
            )
