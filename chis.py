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
# CARGA CSV
# =========================================

archivo = st.file_uploader("📂 Selecciona el archivo CSV")

if archivo is not None:
    archivo.seek(0)
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
            "15 días": 15,
            "1 mes": 30,
            "2 meses": 60,
            "3 meses": 90
        }
        resultados = {}

        for et, d in etiquetas.items():
            datos = df_calculo[df_calculo["fecha"] >= fecha_base - timedelta(days=d)]
            if not datos.empty:
                resultados[et] = calcular(datos)

        st.session_state["resultados"] = resultados
        st.session_state["df_calculo"] = df_calculo


# =========================================
# DESCARTES DE NÚMEROS Y RESULTADO FINAL
# =========================================

if "resultados" in st.session_state:
    resultados = st.session_state["resultados"]

    # Resultados del periodo de 15 días con el diseño del código de referencia.
    st.markdown("---")
    st.subheader("📊 Resultados por periodo")

    if "15 días" in resultados:
        st.markdown("#### 📅 15 días")
        serie = resultados["15 días"]
        bloques_html = ""
        grupos = {
            "1-9": range(1, 10),
            "10-19": range(10, 20),
            "20-28": range(20, 29)
        }

        for nombre_grupo, rango in grupos.items():
            grupo = serie[serie.index.isin(rango)].sort_values(ascending=False)
            lista_html = ""

            for numero, frecuencia in grupo.items():
                lista_html += (
                    f"<div style='text-align:center;margin:2px 0;white-space:nowrap;"
                    f"font-size:17px;line-height:1.25;'>"
                    f"<span style='font-weight:600;'>{int(numero)}</span> "
                    f"<span style='color:#888;'>({int(frecuencia)})</span></div>"
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
    else:
        st.warning("No hay datos disponibles para calcular el periodo de 15 días.")

    st.markdown("---")
    st.subheader("🧹 Descarte de números, nivel 1")

    disponibles = set(range(1, 29))
    descartados_totales = set()

    def mostrar_numeros(titulo, numeros, color="#000000"):
        numeros = sorted(set(int(n) for n in numeros))
        st.markdown(
            f"<div style='color:{color};font-weight:bold;margin-top:5px;'>{titulo}</div>",
            unsafe_allow_html=True
        )
        texto = ", ".join(str(n) for n in numeros) if numeros else "Ningún número"
        st.markdown(
            f"<div style='color:{color};'>{texto}</div>",
            unsafe_allow_html=True
        )

    rangos_decenas = {
        "unidad": range(1, 10),
        "decena": range(10, 20),
        "veintena": range(20, 29)
    }

    def obtener_candidatos_frecuencia(periodo, tipo):
        if periodo not in resultados:
            return None

        serie = resultados[periodo]
        candidatos_periodo = set()

        for rango_dec in rangos_decenas.values():
            serie_dec = serie[serie.index.isin(rango_dec)]
            if not serie_dec.empty:
                frecuencias = [int(f) for f in serie_dec.values]
                nivel = min(frecuencias) if tipo == "menos" else max(frecuencias)
                candidatos_periodo.update(
                    int(n) for n, frecuencia in serie_dec.items()
                    if int(frecuencia) == nivel
                )

        return candidatos_periodo

    def aplicar_y_mostrar(candidatos, titulo, color):
        afectados = candidatos & disponibles
        disponibles.difference_update(afectados)
        descartados_totales.update(afectados)
        mostrar_numeros(titulo, afectados, color=color)
        return afectados

    for periodo in ["15 días", "1 mes", "2 meses", "3 meses"]:
        with st.container(border=True):
            candidatos_mas = obtener_candidatos_frecuencia(periodo, "mas")
            candidatos_menos = obtener_candidatos_frecuencia(periodo, "menos")

            if candidatos_mas is None or candidatos_menos is None:
                st.warning(f"No hay datos disponibles para calcular el periodo de {periodo}.")
            else:
                aplicar_y_mostrar(
                    candidatos_mas,
                    f"Más frecuentes, {periodo}",
                    "#28a745"
                )
                aplicar_y_mostrar(
                    candidatos_menos,
                    f"Menos frecuentes, {periodo}",
                    "#ff4b4b"
                )

    with st.container(border=True):
        df_calculo_actual = st.session_state.get("df_calculo")
        columnas_numeros = ["r1", "r2", "r3", "r4", "r5"]

        if (
            df_calculo_actual is not None
            and all(columna in df_calculo_actual.columns for columna in columnas_numeros)
        ):
            ultimos_4 = df_calculo_actual.sort_values("fecha").tail(4)
            numeros_ultimos_4 = (
                ultimos_4[columnas_numeros]
                .apply(pd.to_numeric, errors="coerce")
                .stack()
            )
            numeros_ultimos_4 = numeros_ultimos_4[
                numeros_ultimos_4.between(1, 28)
            ].astype(int)

            frecuencias_ultimos_4 = numeros_ultimos_4.value_counts()
            candidatos_ultimos_4 = {
                int(n) for n, frecuencia in frecuencias_ultimos_4.items()
                if int(frecuencia) >= 2
            }

            # 1. Se aplican y muestran los descartes reales en el sistema
            aplicar_y_mostrar(
                candidatos_ultimos_4,
                "Últimos 4 sorteos (2 o más apariciones)",
                "#007bff"
            )
            
            # 2. CORRECCIÓN: Se muestran TODOS los números completos (independientemente de descartes previos) en el renglón gris
            numeros_completos_ultimos_4 = ", ".join(
                str(n) for n in sorted(candidatos_ultimos_4)
            ) if candidatos_ultimos_4 else "Ningún número"
            
            st.markdown(
                f"<div style='color:#888;font-size:15px;margin-top:4px;'>"
                f"{numeros_completos_ultimos_4}</div>",
                unsafe_allow_html=True
            )

            ultimo_registro = df_calculo_actual.sort_values("fecha").iloc[-1]
            candidatos_ultimo_sorteo = set()
            for columna in columnas_numeros:
                valor = pd.to_numeric(ultimo_registro[columna], errors="coerce")
                if pd.notna(valor) and 1 <= int(valor) <= 28:
                    candidatos_ultimo_sorteo.add(int(valor))

            aplicar_y_mostrar(
                candidatos_ultimo_sorteo,
                "Último sorteo",
                "#007bff"
            )

            nums_ultimo = [int(ultimo_registro[col]) for col in columnas_numeros if pd.notna(ultimo_registro[col])]
            nums_ultimo_str = ", ".join(str(n) for n in sorted(nums_ultimo))
            st.markdown(
                f"<div style='color:#888;font-size:16px;margin-top:10px;margin-bottom:5px;'>"
                f"<b>Último sorteo:</b> {nums_ultimo_str}</div>",
                unsafe_allow_html=True
            )
        else:
            st.warning("No se pudieron identificar las columnas R1–R5 de los últimos sorteos.")

    st.markdown("---")
    st.markdown(
        "<div style='color:#28a745;font-size:20px;font-weight:600;margin-bottom:8px;'>Números restantes</div>",
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
                    f"<div style='color:#28a745;font-size:22px;font-weight:700;line-height:1.7;'>"
                    f"{', '.join(str(n) for n in fila)}</div>",
                    unsafe_allow_html=True
                )
    else:
        st.write("Ninguno")

    st.write("")
    st.caption(
        f"Total eliminados {len(descartados_totales)}. Restantes {len(restantes)}."
    )

    numeros_disponibles = sorted(set(restantes))
    unidades = [n for n in numeros_disponibles if 1 <= n <= 9]
    decenas = [n for n in numeros_disponibles if 10 <= n <= 19]
    veintenas = [n for n in numeros_disponibles if 20 <= n <= 28]
    grupos_numeros = [unidades, decenas, veintenas]
    cantidades = [len(grupo) for grupo in grupos_numeros]

    cantidad_combinaciones = 0
    asignacion_singulares = []
    for k in range(len(numeros_disponibles) // 5, 0, -1):
        opciones = []
        for s0 in range(k + 1):
            for s1 in range(k + 1):
                s2 = k - s0 - s1
                if not 0 <= s2 <= k:
                    continue
                singulares = [s0, s1, s2]
                usados_por_grupo = [2 * k - singulares[g] for g in range(3)]
                if all(usados_por_grupo[g] <= cantidades[g] for g in range(3)):
                    opciones.append(singulares)
        if opciones:
            cantidad_combinaciones = k
            asignacion_singulares = random.choice(opciones)
            break

    posiciones = [0, 0, 0]
    mejores_combinaciones = []
    if cantidad_combinaciones:
        grupos_singulares = []
        for indice_grupo, cantidad_singular in enumerate(asignacion_singulares):
            grupos_singulares.extend([indice_grupo] * cantidad_singular)
        random.shuffle(grupos_singulares)

        grupos_barajados = [grupo[:] for grupo in grupos_numeros]
        for grupo in grupos_barajados:
            random.shuffle(grupo)

        for grupo_singular in grupos_singulares:
            combinacion = []
            for indice_grupo in range(3):
                aporte = 1 if indice_grupo == grupo_singular else 2
                inicio = posiciones[indice_grupo]
                fin = inicio + aporte
                combinacion.extend(grupos_barajados[indice_grupo][inicio:fin])
                posiciones[indice_grupo] = fin

            if (
                len(combinacion) == 5
                and len(set(combinacion)) == 5
                and any(1 <= n <= 9 for n in combinacion)
                and any(10 <= n <= 19 for n in combinacion)
                and any(20 <= n <= 28 for n in combinacion)
            ):
                mejores_combinaciones.append(sorted(combinacion))

    numeros_usados = {n for combinacion in mejores_combinaciones for n in combinacion}
    numeros_incompletos = sorted(set(numeros_disponibles) - numeros_usados)

    st.session_state["combinaciones_descartes"] = mejores_combinaciones
    st.session_state["incompletos_descartes"] = numeros_incompletos

    for combinacion in mejores_combinaciones:
        st.markdown(
            f"<div style='color:#28a745;font-size:22px;font-weight:700;line-height:1.7;'>"
            f"{', '.join(str(n) for n in combinacion)}</div>",
            unsafe_allow_html=True
        )

    if numeros_incompletos:
        st.markdown(
            f"<div style='color:#28a745;font-size:22px;font-weight:700;line-height:1.7;'>"
            f"{', '.join(str(n) for n in numeros_incompletos)}</div>",
            unsafe_allow_html=True
        )

    st.button("Regenerar combinaciones")
