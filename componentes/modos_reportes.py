import pandas as pd
import streamlit as st
from datetime import datetime
import tempfile
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pathlib import Path


img_path = Path(__file__).parents[1] / "assets" / "Ally_logo_mayo_2025.png"
fecha_formateada = datetime.now().strftime("%d%m%Y")

def generar_csv_reporte(df_final, auditor, modo):
    # Agregar columnas necesarias
    df_final["diferencia"] = df_final["cantidad_fisica"] - df_final["cantidad_sistema"]
    df_final["auditor"] = auditor
    df_final["fecha_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Nombre de archivo
    fecha_archivo = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"Inventario-{modo}_{fecha_archivo}.csv"

    # Generar CSV en memoria
    csv_bytes = df_final.to_csv(index=False).encode("utf-8")

    # Botón de descarga
    st.download_button(
        label="⬇️ Descargar reporte CSV",
        data=csv_bytes,
        file_name=nombre_archivo,
        mime="text/csv",
        key=f"download_csv_{modo}_{fecha_archivo}"
    )



def generar_csv_sobrantes():
    if "sobrantes" in st.session_state and st.session_state["sobrantes"]:
        df = pd.DataFrame(st.session_state["sobrantes"])
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Descargar CSV de sobrantes",
            data=csv,
            file_name=f"Inventario-Sobrantes_{fecha_formateada}.csv",
            mime="text/csv"
        )

def generar_csv_ciego():
    if "ciego_df" in st.session_state and not st.session_state["ciego_df"].empty:
        csv = st.session_state["ciego_df"].to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Descargar archivo CSV",
            data=csv,
            file_name=f"Inventario-Ciego_{fecha_formateada}.csv",
            mime="text/csv"
        )

def generar_csv_ciclico(df_ciclico):
    if df_ciclico is None or df_ciclico.empty:
        st.warning("⚠️ No hay datos cíclicos para exportar.")
        return

    # Validar que exista el auditor y el almacén
    auditor = st.session_state.get("auditor", "Desconocido")
    almacen = df_ciclico["almacen"].iloc[0] if "almacen" in df_ciclico.columns else "N/A"
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Agrupar por código
    df_grouped = df_ciclico.groupby("barcode", as_index=False).agg({
        "nombre": "first",
        "cantidad_fisica": "sum",
        "cantidad_sistema": "sum"
    })

    # Agregar columnas adicionales
    df_grouped["diferencia"] = df_grouped["cantidad_fisica"] - df_grouped["cantidad_sistema"]
    df_grouped["auditor"] = auditor
    df_grouped["fecha_check"] = fecha_actual
    df_grouped["almacen"] = almacen

    # Exportar
    csv_ciclico = df_grouped.to_csv(index=False).encode("utf-8")
    nombre_archivo = f"Inventario-Ciclico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    st.download_button(
        label="⬇️ Descargar CSV de inventario cíclico",
        data=csv_ciclico,
        file_name=nombre_archivo,
        mime="text/csv",
        key="download_csv_ciclico"
    )


def generar_pdf(df, auditor, puesto, sucursal, modo):
    faltantes = df[df["cantidad_fisica"] < df["cantidad_sistema"]]
    excedentes = df[df["cantidad_fisica"] > df["cantidad_sistema"]]

    faltantes["diferencia"] = faltantes["cantidad_sistema"] - faltantes["cantidad_fisica"]
    excedentes["diferencia"] = excedentes["cantidad_fisica"] - excedentes["cantidad_sistema"]

    faltantes["costo_total"] = faltantes["diferencia"] * faltantes["costo"]
    excedentes["costo_total"] = excedentes["diferencia"] * excedentes["costo"]

    total_faltantes = faltantes["diferencia"].sum()
    total_excedentes = excedentes["diferencia"].sum()
    costo_faltantes = faltantes["costo_total"].sum()
    costo_excedentes = excedentes["costo_total"].sum()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        c = canvas.Canvas(tmpfile.name, pagesize=letter)
        width, height = letter

        # Título
        c.setFont("Helvetica-Bold", 18)
        c.drawString(40, height - 20, "Resumen de Inventario")
        c.setFont("Helvetica", 10)
        c.drawString(40, height - 40, f"{modo}")

        # Logo
        try:
            c.drawImage(img_path, width - 120, height - 100, width=80, preserveAspectRatio=True) #CAMBIAR UBICACION
        except:
            #c.setFont("Helvetica-Bold", 18)
            pass

        c.setFont("Helvetica", 10)
        c.drawString(40, height - 60, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        c.drawString(40, height - 75, f"Sucursal: {sucursal}")
        c.drawString(40, height - 90, f"Elaborado por: {auditor} - {puesto}")
        c.line(40, height - 97, width - 40, height - 95)

        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, height - 115, "Productos con faltantes:")

        c.setFont("Helvetica", 10)
        c.drawString(40, height - 130, "Código de barras | Lote | Producto | Piezas Faltantes / Excedentes")

        y = height - 150
        for idx, row in faltantes.iterrows():
            if y < 100:
                c.showPage()
                y = height - 80
            c.drawString(50, y, f"- {row['barcode']} | {row['lote']} | {row['nombre']} | Faltan: {int(row['diferencia'])}")
            y -= 15

        y -= 15
        c.drawString(40, y, f"Total de piezas faltantes: {int(total_faltantes)}")
        y -= 15
        c.drawString(50, y, f"Costo total de faltantes: ${costo_faltantes:,.2f}")

        y -= 40
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, "Productos con excedentes:")
        y -= 20

        c.setFont("Helvetica", 10)
        for idx, row in excedentes.iterrows():
            if y < 100:
                c.showPage()
                y = height - 80
            c.drawString(50, y, f"- {row['barcode']} | {row['lote']} | {row['nombre']} | Excedente: {int(row['diferencia'])}")
            y -= 15

        y -= 15
        c.drawString(50, y, f"Total de piezas excedentes: {int(total_excedentes)}")
        y -= 15
        c.drawString(50, y, f"Costo total de excedentes: ${costo_excedentes:,.2f}")

        # Firmas
        y -= 50
        c.drawString(40, y, "______________________________")
        c.drawString(40, y - 15, f"Elaboró: {auditor}")

        c.drawString(250, y, "______________________________")
        c.drawString(250, y - 15, "Líder de Operaciones")

        c.drawString(40, y - 60, "______________________________")
        c.drawString(40, y - 75, "Director de Operaciones")

        # Footer
        c.setLineWidth(0.5)
        c.line(40, 50, width - 40, 50)
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.4, 0.4, 0.4)

        footer_text_1 = "CHASE FARMACEUTICAL GROUP, S.A.P.I DE C.V."
        footer_text_2 = "RFC: CFG181003SI1"
        c.drawString((width - c.stringWidth(footer_text_1, "Helvetica", 8)) / 2, 40, footer_text_1)
        c.drawString((width - c.stringWidth(footer_text_2, "Helvetica", 8)) / 2, 30, footer_text_2)

        c.setFillColorRGB(0, 0, 0)
        c.save()

        return tmpfile.name