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
# GENERADOR ORIGINAL
# =========================================
def generar(pool_base, repeticiones):
    total_nums = len(pool_base)
    num_combinaciones = total_nums // 5

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
# GENERADOR 6 (OPTIMIZADO)
# =========================================
def generar_6(balance):
    frecuencias = balance
    max_freq = frecuencias.max()

    top_real = frecuencias[frecuencias >= max_freq - 1].index.tolist()
    if len(top_real) < 4:
        top_real = frecuencias.head(4).index.tolist()

    top_extendido = frecuencias.head(10).index.tolist()
    base_nums = list(range(1, 29))

    def construir_pool(top_usar):
        repetidos = random.sample(top_usar, 2)
        pool = base_nums + repetidos
        random.shuffle(pool)
        return pool

    def dividir_pool(pool):
        return [sorted(pool[i * 5:(i + 1) * 5]) for i in range(6)]

    for nivel in [1, 2, 3]:
        top_usar = top_real if nivel < 3 else top_extendido

        for _ in range(3000):
            pool = construir_pool(top_usar)
            combinaciones = dividir_pool(pool)

            plano = [n for c in combinaciones for n in c]
            conteo = pd.Series(plano).value_counts()

            if len(conteo) != 28:
                continue

            if not all(v in [1, 2] for v in conteo):
                continue

            if sum(v == 2 for v in conteo) != 2:
                continue

            valido = True

            for comb in combinaciones:
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

            if valido:
                return combinaciones, nivel

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
                "r1": r1,
                "r2": r2,
                "r3": r3,
                "r4": r4,
                "r5": r5,
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

        if "15 días" in resultados:
            st.session_state["c6_15"], st.session_state["n6_15"] = generar_6(resultados["15 días"])

        if "1 mes" in resultados:
            st.session_state["c6_m"], st.session_state["n6_m"] = generar_6(resultados["1 mes"])

# =========================================
# TABLA RESULTADOS
# =========================================
if "resultados" in st.session_state:
    r = st.session_state["resultados"]

    st.markdown("---")
    st.subheader("📊 Top 28 por periodo")

    html = "<table style='width:100%; text-align:center;'>"
    html += "<tr>" + "".join(f"<th>{c}</th>" for c in r) + "</tr>"

    for i in range(28):
        html += "<tr>"

        for col in r:
            if i < len(r[col]):
                n = r[col].index[i]
                f = r[col].iloc[i]
                html += f"<td>{n} <span style='color:#888'>({f})</span></td>"
            else:
                html += "<td></td>"

        html += "</tr>"

    html += "</table>"

    st.markdown(html, unsafe_allow_html=True)

# =========================================
# DISPLAY ORIGINAL
# =========================================
def mostrar(titulo, key_c, key_n, key_i, rep, boton):
    if key_c in st.session_state:
        st.markdown("---")
        st.subheader(titulo)

        if key_i in st.session_state:
            base_nums = sorted(st.session_state[key_i])
            st.write(f"Base seleccionada: {base_nums}")

        if st.session_state[key_c]:
            st.info(f"Nivel: {st.session_state[key_n]}")
            for i, c in enumerate(st.session_state[key_c], 1):
                st.write(f"{i}: {c}")
        else:
            st.warning("No fue posible generar las combinaciones")

        if st.button(boton, key=boton):
            c, n = generar(st.session_state[key_i], rep)
            st.session_state[key_c] = c
            st.session_state[key_n] = n

# =========================================
# BLOQUES ORIGINALES
# =========================================
mostrar("🎯 15 números (15 días)", "c15", "n15", "i15", 2, "🔄 Generar nuevas (15 días)")
mostrar("🎯 15 números (1 mes)", "c15_m", "n15_m", "i15_m", 2, "🔄 Generar nuevas (15 números - 1 mes)")

# =========================================
# DISPLAY 6 COMBINACIONES
# =========================================
def mostrar_6(titulo, key_c, key_n, boton, balance):
    if key_c in st.session_state:
        st.markdown("---")
        st.subheader(titulo)

        if st.session_state[key_c]:
            st.info(f"Nivel: {st.session_state[key_n]}")
            for i, c in enumerate(st.session_state[key_c], 1):
                st.write(f"{i}: {c}")
        else:
            st.warning("No fue posible generar")

        if st.button(boton, key=boton):
            c, n = generar_6(balance)
            st.session_state[key_c] = c
            st.session_state[key_n] = n

if "resultados" in st.session_state:
    r = st.session_state["resultados"]

    if "15 días" in r:
        mostrar_6(
            "🔥 6 combinaciones (15 días)",
            "c6_15",
            "n6_15",
            "🔄 Generar nuevas (6 - 15 días)",
            r["15 días"]
        )

    if "1 mes" in r:
        mostrar_6(
            "🔥 6 combinaciones (1 mes)",
            "c6_m",
            "n6_m",
            "🔄 Generar nuevas (6 - 1 mes)",
            r["1 mes"]
        )
