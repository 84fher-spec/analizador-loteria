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
    return sum(1 for i in range(len(comb) - 1) if comb[i] + 1 == comb[i + 1])


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
                comb = sorted(pool[i * 5:(i + 1) * 5])

                if len(set(comb)) < 5:
                    valido = False
                    break

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
                elif nivel == 2:
                    if contar_consecutivos(comb) > 0:
                        valido = False
                        break
                    if not decenas_ok(comb, 3):
                        valido = False
                        break
                elif nivel == 3:
                    if contar_consecutivos(comb) > 1:
                        valido = False
                        break
                    if not decenas_ok(comb, 2):
                        valido = False
                        break

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
    objetivo = cantidad_total
    mejor_combinaciones = None
    mejor_puntuacion = None

    for _ in range(5000):
        if len(numeros) > objetivo:
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
        combinaciones = [seleccion[i:i + 5] for i in range(0, len(seleccion), 5)]

        if len(combinaciones) < 3 or any(len(c) < 5 for c in combinaciones):
            continue

        combinaciones = [sorted(c) for c in combinaciones]
        cantidades_globales = [
            sum(1 for n in seleccion if 1 <= n <= 9),
            sum(1 for n in seleccion if 10 <= n <= 19),
            sum(1 for n in seleccion if 20 <= n <= 28)
        ]
        diferencia_global = max(cantidades_globales) - min(cantidades_globales)
        diferencia_combos = 0
        concentracion = 0

        for comb in combinaciones:
            cantidades = [
                sum(1 for n in comb if 1 <= n <= 9),
                sum(1 for n in comb if 10 <= n <= 19),
                sum(1 for n in comb if 20 <= n <= 28)
            ]
            diferencia_combos += max(cantidades) - min(cantidades)
            if max(cantidades) >= 4:
                concentracion += 3

        puntuacion = diferencia_global * 10 + diferencia_combos + concentracion

        if mejor_puntuacion is None or puntuacion < mejor_puntuacion:
            mejor_puntuacion = puntuacion
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
            nums = df_bloque[["r1", "r2", "r3", "r4", "r5"]]
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
        st.session_state["df_calculo"] = df_calculo


# =========================================
# RESULTADOS AGRUPADOS POR DECENAS
# =========================================

if "resultados" in st.session_state:
    r = st.session_state["resultados"]
    st.markdown("---")
    st.subheader("📊 Resultados por periodo")

    periodos_mostrar = ["1 semana", "15 días", "Histórico completo"]
    grupos = {
        "1-9": range(1, 10),
        "10-19": range(10, 20),
        "20-28": range(20, 29)
    }

    for periodo in periodos_mostrar:
        if periodo in r:
            st.markdown(f"#### 📅 {periodo}")
            serie = r[periodo]
            bloques_html = ""

            for nombre_grupo, rango in grupos.items():
                grupo = serie[serie.index.isin(rango)].sort_values(ascending=False)
                lista_html = ""

                for numero, frecuencia in grupo.items():
                    lista_html += (
                        f"<div style='text-align:center;margin:2px 0;white-space:nowrap;"
                        f"font-size:17px;line-height:1.25;'>"
                        f"<span style='font-weight:600;'>{numero}</span> "
                        f"<span style='color:#888;'>({frecuencia})</span></div>"
                    )

                bloques_html += (
                    f"<div style='flex:1 1 0;min-width:0;width:33.333%;box-sizing:border-box;padding:0 2px;'>"
                    f"<div style='text-align:center;font-weight:bold;margin-bottom:6px;"
                    f"white-space:nowrap;font-size:14px;'>{nombre_grupo}</div>"
                    f"{lista_html}</div>"
                )

            st.markdown(
                f"<div style='display:flex;flex-direction:row;flex-wrap:nowrap;width:100%;"
                f"max-width:100%;box-sizing:border-box;overflow:hidden;align-items:flex-start;"
                f"justify-content:space-between;'>{bloques_html}</div>",
                unsafe_allow_html=True
            )
            st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)


# =========================================
# DESCARTES DE NÚMEROS Y RESULTADO FINAL
# =========================================

if "resultados" in st.session_state:
    resultados = st.session_state["resultados"]
    st.markdown("---")
    st.subheader("🧹 Descarte de números")

    # Todos los números posibles, inicialmente disponibles.
    disponibles = set(range(1, 29))
    descartados_totales = set()

    def mostrar_numeros(titulo, numeros):
        numeros = sorted(set(int(n) for n in numeros))
        st.markdown(f"**{titulo}**")
        if numeros:
            st.write(", ".join(str(n) for n in numeros))
        else:
            st.write("Ningún número")

    # 1. Descartar números con 0 o 1 aparición en la última semana.
    if "1 semana" in resultados:
        serie_semana = resultados["1 semana"]
        candidatos_semana = set(
            int(n) for n, frecuencia in serie_semana.items()
            if int(frecuencia) <= 1
        )
        descartados_semana = candidatos_semana & disponibles
        disponibles -= descartados_semana
        descartados_totales |= descartados_semana
        mostrar_numeros(
            "Descartados, 1 semana (0 y 1 aparición)",
            descartados_semana
        )
    else:
        st.warning("No hay datos disponibles para calcular el periodo de 1 semana.")

    # 2. Descartar los dos niveles de frecuencia más bajos del periodo de 15 días.
    if "15 días" in resultados:
        serie_quincena = resultados["15 días"]
        niveles_quincena = sorted(set(int(f) for f in serie_quincena.values))
        niveles_bajos_quincena = niveles_quincena[:2]
        candidatos_quincena = set(
            int(n) for n, frecuencia in serie_quincena.items()
            if int(frecuencia) in niveles_bajos_quincena
        )
        descartados_quincena = candidatos_quincena & disponibles
        disponibles -= descartados_quincena
        descartados_totales |= descartados_quincena
        mostrar_numeros(
            "Descartados, 15 días (2 niveles)",
            descartados_quincena
        )
    else:
        st.warning("No hay datos disponibles para calcular el periodo de 15 días.")

    # 3. Descartar los dos números menos frecuentes del histórico completo.
    if "Histórico completo" in resultados:
        serie_historica = resultados["Histórico completo"]
        candidatos_historicos = sorted(
            serie_historica.items(),
            key=lambda elemento: (int(elemento[1]), int(elemento[0]))
        )
        numeros_menos_frecuentes_historicos = [
            int(n) for n, _ in candidatos_historicos[:2]
        ]
        descartados_historicos = set(numeros_menos_frecuentes_historicos) & disponibles
        disponibles -= descartados_historicos
        descartados_totales |= descartados_historicos
        mostrar_numeros(
            "Descartados, histórico completo (2 niveles)",
            descartados_historicos
        )
    else:
        st.warning("No hay datos disponibles para el histórico completo.")

    # 4. Descartar los números del último sorteo registrado.
    columnas_numeros = ["r1", "r2", "r3", "r4", "r5"]
    df_calculo_actual = st.session_state.get("df_calculo")
    if df_calculo_actual is not None and all(columna in df_calculo_actual.columns for columna in columnas_numeros):
        ultimo_registro = df_calculo_actual.sort_values("fecha").iloc[-1]
        numeros_ultimo_sorteo = set()
        for columna in columnas_numeros:
            valor = pd.to_numeric(ultimo_registro[columna], errors="coerce")
            if pd.notna(valor) and 1 <= int(valor) <= 28:
                numeros_ultimo_sorteo.add(int(valor))

        descartados_ultimo_sorteo = numeros_ultimo_sorteo & disponibles
        disponibles -= descartados_ultimo_sorteo
        descartados_totales |= descartados_ultimo_sorteo
        mostrar_numeros(
            "Descartados, último sorteo",
            descartados_ultimo_sorteo
        )
        st.caption(
            "Último sorteo: "
            + (", ".join(str(n) for n in sorted(numeros_ultimo_sorteo))
               if numeros_ultimo_sorteo else "No se encontraron números válidos")
        )
    else:
        st.warning("No se pudieron identificar las columnas R1–R5 del último sorteo.")

    # 5. Descarte final: los dos niveles de frecuencia más altos de la semana.
    if "1 semana" in resultados:
        serie_semana = resultados["1 semana"]
        niveles_frecuentes_semana = sorted(
            set(int(frecuencia) for frecuencia in serie_semana.values),
            reverse=True
        )[:2]
        candidatos_niveles_frecuentes_semana = set(
            int(n) for n, frecuencia in serie_semana.items()
            if int(frecuencia) in niveles_frecuentes_semana
        )
        descartados_niveles_frecuentes_semana = (
            candidatos_niveles_frecuentes_semana & disponibles
        )
        disponibles -= descartados_niveles_frecuentes_semana
        descartados_totales |= descartados_niveles_frecuentes_semana
        mostrar_numeros(
            "Descartados, más frecuentes de una semana (2 niveles)",
            descartados_niveles_frecuentes_semana
        )
    else:
        st.warning("No hay datos disponibles para realizar el descarte final de 1 semana.")

    # 6. Mostrar los números restantes al final, después de todos los descartes.
    st.markdown("---")
    st.markdown(
        "<div style='font-size:20px;font-weight:600;margin-bottom:8px;'>Números restantes</div>",
        unsafe_allow_html=True
    )
    restantes = sorted(disponibles)
    if restantes:
        filas_por_decena = [
            [n for n in restantes if 1 <= n <= 9],
            [n for n in restantes if 10 <= n <= 19],
            [n for n in restantes if 20 <= n <= 28],
        ]
        for fila in filas_por_decena:
            if fila:
                st.markdown(
                    f"<div style='font-size:22px;font-weight:700;line-height:1.7;'>"
                    f"{', '.join(str(n) for n in fila)}</div>",
                    unsafe_allow_html=True
                )
    else:
        st.write("Ninguno")

    st.write("")
    st.caption(
        f"Descartados {len(descartados_totales)}. Restantes {len(restantes)}."
    )

    # 7. Generar combinaciones equilibradas con los números restantes.
    # Todas las combinaciones completas deben incluir unidades, decenas y veintenas.
    import itertools

    numeros_disponibles = sorted(set(restantes))
    unidades = [n for n in numeros_disponibles if 1 <= n <= 9]
    decenas = [n for n in numeros_disponibles if 10 <= n <= 19]
    veintenas = [n for n in numeros_disponibles if 20 <= n <= 28]
    grupos = [unidades, decenas, veintenas]

    # Solo se admiten combinaciones con distribución 2-2-1 entre los tres grupos.
    combinaciones_validas = []
    for combinacion in itertools.combinations(numeros_disponibles, 5):
        cantidades_grupos = (
            sum(1 <= n <= 9 for n in combinacion),
            sum(10 <= n <= 19 for n in combinacion),
            sum(20 <= n <= 28 for n in combinacion),
        )
        if (
            all(cantidad >= 1 for cantidad in cantidades_grupos)
            and sorted(cantidades_grupos) == [1, 2, 2]
        ):
            combinaciones_validas.append(tuple(combinacion))

    # Buscar el conjunto de combinaciones sin números repetidos que use más números.
    mejores_combinaciones = []
    mejor_cantidad = -1
    if combinaciones_validas:
        for _ in range(2000):
            candidatas = combinaciones_validas[:]
            random.shuffle(candidatas)
            usadas = set()
            seleccionadas = []
            for combinacion in candidatas:
                if not usadas.intersection(combinacion):
                    # Validación final: ninguna combinación completa puede omitir un grupo.
                    tiene_unidades = any(1 <= n <= 9 for n in combinacion)
                    tiene_decenas = any(10 <= n <= 19 for n in combinacion)
                    tiene_veintenas = any(20 <= n <= 28 for n in combinacion)
                    if len(combinacion) == 5 and tiene_unidades and tiene_decenas and tiene_veintenas:
                        seleccionadas.append(combinacion)
                        usadas.update(combinacion)
            if len(seleccionadas) > mejor_cantidad:
                mejor_cantidad = len(seleccionadas)
                mejores_combinaciones = seleccionadas
                if len(usadas) == (len(numeros_disponibles) // 5) * 5:
                    break

    numeros_usados = {n for combinacion in mejores_combinaciones for n in combinacion}
    numeros_incompletos = sorted(set(numeros_disponibles) - numeros_usados)

    for combinacion in mejores_combinaciones:
        st.markdown(
            f"<div style='font-size:22px;font-weight:700;line-height:1.7;'>"
            f"{', '.join(str(n) for n in sorted(combinacion))}</div>",
            unsafe_allow_html=True
        )

    if numeros_incompletos:
        st.markdown(
            f"<div style='font-size:22px;font-weight:700;line-height:1.7;'>"
            f"{', '.join(str(n) for n in numeros_incompletos)}</div>",
            unsafe_allow_html=True
        )
