import streamlit as st
import pandas as pd
import io
from datetime import timedelta
import random

# =========================================
# CONFIG
# =========================================
st.set_page_config(page_title="Analizador", layout="centered")
st.title("📊 Analizador de Frecuencias")

archivo = st.file_uploader("📂 CSV", type=None)

# =========================================
# FUNCIONES
# =========================================
def frec(data, columnas):
    nums = data[columnas].apply(pd.to_numeric, errors="coerce")
    nums = pd.Series(nums.values.flatten()).dropna().astype(int)
    c = nums.value_counts().reindex(range(1,40), fill_value=0)
    return c.sort_values(ascending=False)

def seleccionar(freq):
    nums = list(freq.index)

    grupos = [
        [n for n in nums if 1<=n<=9],
        [n for n in nums if 10<=n<=19],
        [n for n in nums if 20<=n<=29],
        [n for n in nums if 30<=n<=39],
    ]

    sel = []
    for g in grupos:
        pares = [n for n in g if n%2==0]
        nones = [n for n in g if n%2!=0]
        sel += pares[:2] + nones[:2]

    faltan = [n for n in nums if n not in sel]
    while len(sel) < 18:
        sel.append(faltan.pop(0))

    return sorted(sel[:18])

def decena(n):
    return 1 if n<=9 else 2 if n<=19 else 3 if n<=29 else 4

def validar(combo, nivel):
    combo = sorted(combo)

    consecutivos = sum(1 for i in range(5) if combo[i]+1 == combo[i+1])
    if nivel == 1 and consecutivos > 0:
        return False
    if nivel == 2 and consecutivos > 1:
        return False

    pares = sum(n % 2 == 0 for n in combo)
    if pares < 2 or pares > 4:
        return False

    decs = len(set(decena(n) for n in combo))
    if nivel in [1,2] and decs != 4:
        return False
    if nivel == 3 and decs < 3:
        return False

    return True

def generar(nums):
    for nivel in [1,2,3]:
        for _ in range(4000):
            pool = nums.copy()
            random.shuffle(pool)

            c1, c2, c3 = pool[:6], pool[6:12], pool[12:18]

            if all(validar(c, nivel) for c in [c1, c2, c3]):
                return [sorted(c1), sorted(c2), sorted(c3)], nivel
    return [], 0

# =========================================
# CALLBACKS
# =========================================
def regen_2m():
    st.session_state.comb2, st.session_state.nivel2 = generar(st.session_state.sel2)

def regen_4m():
    st.session_state.comb4, st.session_state.nivel4 = generar(st.session_state.sel4)

# =========================================
# PROCESO PRINCIPAL
# =========================================
if archivo is not None:

    df = pd.read_csv(io.BytesIO(archivo.read()), sep=",", encoding="latin-1")
    df.columns = df.columns.str.strip().str.lower()

    columnas = ["r1","r2","r3","r4","r5"] if "r1" in df.columns else ["f1","f2","f3","f4","f5","f6","f7"]

    df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["fecha"])

    if st.button("🔍 Calcular frecuencias"):

        fecha_base = df["fecha"].max()

        resultados = {
            "2 meses": frec(df[df["fecha"] >= fecha_base - timedelta(days=60)], columnas),
            "4 meses": frec(df[df["fecha"] >= fecha_base - timedelta(days=120)], columnas),
            "8 meses": frec(df[df["fecha"] >= fecha_base - timedelta(days=240)], columnas)
        }

        st.session_state.resultados = resultados
        st.session_state.sel2 = seleccionar(resultados["2 meses"])
        st.session_state.sel4 = seleccionar(resultados["4 meses"])

        st.session_state.comb2, st.session_state.nivel2 = generar(st.session_state.sel2)
        st.session_state.comb4, st.session_state.nivel4 = generar(st.session_state.sel4)

# =========================================
# MOSTRAR RESULTADOS
# =========================================
if "resultados" in st.session_state:

    resultados = st.session_state.resultados

    st.subheader("📊 Frecuencias")

    html = "<table style='width:100%; text-align:center;'>"
    html += "<tr>" + "".join([f"<th>{k}</th>" for k in resultados]) + "</tr>"

    for i in range(39):
        html += "<tr>"
        for k in resultados:
            num = resultados[k].index[i]
            f = resultados[k].iloc[i]
            html += f"<td>{num} ({f})</td>"
        html += "</tr>"
    html += "</table>"

    st.markdown(html, unsafe_allow_html=True)

    if "comb2" not in st.session_state:
        st.session_state.comb2, st.session_state.nivel2 = generar(st.session_state.sel2)

    if "comb4" not in st.session_state:
        st.session_state.comb4, st.session_state.nivel4 = generar(st.session_state.sel4)

    # =========================================
    # 2 MESES
    # =========================================
    st.markdown("---")
    st.subheader("🎯 2 meses")

    st.write(", ".join(map(str, st.session_state.sel2)))
    st.write(f"Nivel: {st.session_state.nivel2}")

    for i, c in enumerate(st.session_state.comb2, 1):
        st.write(f"C{i}: {', '.join(map(str, c))}")

    st.button("🔁 Generar nuevas (2 meses)", key="btn_2m", on_click=regen_2m)

    # =========================================
    # 4 MESES
    # =========================================
    st.markdown("---")
    st.subheader("🎯 4 meses")

    st.write(", ".join(map(str, st.session_state.sel4)))
    st.write(f"Nivel: {st.session_state.nivel4}")

    for i, c in enumerate(st.session_state.comb4, 1):
        st.write(f"C{i}: {', '.join(map(str, c))}")

    st.button("🔁 Generar nuevas (4 meses)", key="btn_4m", on_click=regen_4m)
