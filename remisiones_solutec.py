import streamlit as st
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
import os
from datetime import datetime

FOLIO_FILE = "folio_remisiones.txt"


# =========================
# FUNCION FOLIO AUTOMATICO
# =========================
def obtener_folio():

    if not os.path.exists(FOLIO_FILE):
        with open(FOLIO_FILE, "w") as f:
            f.write("1")

    with open(FOLIO_FILE, "r") as f:
        folio = int(f.read())

    with open(FOLIO_FILE, "w") as f:
        f.write(str(folio + 1))

    return folio


# =========================
# GENERAR PDF
# =========================
def generar_pdf(datos, logo_path):

    folio = datos["folio"]
    archivo = f"remision_{folio}.pdf"

    c = canvas.Canvas(archivo, pagesize=(80 * mm, 160 * mm))

    y = 150 * mm

    if logo_path and os.path.exists(logo_path):
        c.drawImage(logo_path, 20 * mm, 138 * mm, 40 * mm, 12 * mm, preserveAspectRatio=True)

    y -= 20 * mm

    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(40 * mm, y, "HOJA DE SERVICIO")

    y -= 5 * mm

    c.setFont("Helvetica", 8)
    c.drawCentredString(40 * mm, y, "Reparación de computadoras, laptops y celulares")

    y -= 10 * mm

    c.line(5 * mm, y, 75 * mm, y)

    y -= 6 * mm
    c.drawString(5 * mm, y, f"Folio: {folio}")

    y -= 6 * mm
    c.drawString(5 * mm, y, f"Fecha: {datos['fecha']}")

    y -= 6 * mm
    c.drawString(5 * mm, y, f"Cliente: {datos['cliente']}")

    y -= 6 * mm
    c.drawString(5 * mm, y, f"Tel: {datos['telefono']}")

    y -= 8 * mm
    c.line(5 * mm, y, 75 * mm, y)

    y -= 6 * mm
    c.drawString(5 * mm, y, f"Equipo: {datos['equipo']}")

    y -= 6 * mm
    c.drawString(5 * mm, y, f"Marca: {datos['marca']}")

    y -= 6 * mm
    c.drawString(5 * mm, y, f"Modelo: {datos['modelo']}")

    y -= 8 * mm
    c.drawString(5 * mm, y, "Servicio:")

    y -= 6 * mm
    c.drawString(5 * mm, y, datos["servicio"])

    y -= 10 * mm
    c.line(5 * mm, y, 75 * mm, y)

    y -= 8 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(5 * mm, y, f"Total: ${datos['costo']}")

    y -= 18 * mm
    c.line(20 * mm, y, 60 * mm, y)

    y -= 5 * mm
    c.setFont("Helvetica", 7)
    c.drawCentredString(40 * mm, y, "Firma de conformidad")

    c.save()

    return archivo


# =========================
# INTERFAZ STREAMLIT
# =========================

st.set_page_config(page_title="Remisiones SoluTec", layout="centered")

st.title("🧾 Generador de Remisiones - SoluTec")

st.write("Sistema sencillo para generar notas de entrega de equipos.")

logo = st.file_uploader("Subir logotipo (opcional)", type=["png", "jpg"])

fecha = st.date_input("Fecha", datetime.today())
cliente = st.text_input("Nombre del cliente")
telefono = st.text_input("Teléfono")

st.subheader("Datos del equipo")

equipo = st.text_input("Equipo")
marca = st.text_input("Marca")
modelo = st.text_input("Modelo")

servicio = st.text_area("Servicio realizado")

costo = st.text_input("Costo")

if st.button("📄 Generar Remisión PDF"):

    folio = obtener_folio()

    logo_path = None

    if logo:
        logo_path = "logo_temp.png"
        with open(logo_path, "wb") as f:
            f.write(logo.read())

    datos = {
        "folio": folio,
        "fecha": fecha,
        "cliente": cliente,
        "telefono": telefono,
        "equipo": equipo,
        "marca": marca,
        "modelo": modelo,
        "servicio": servicio,
        "costo": costo
    }

    pdf = generar_pdf(datos, logo_path)

    st.success(f"Remisión generada correctamente (Folio {folio})")

    with open(pdf, "rb") as f:
        st.download_button(
            label="⬇ Descargar PDF",
            data=f,
            file_name=pdf,
            mime="application/pdf"
        )
