import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io
import chardet
from componentes import (
    modo_ciego,
    modo_general,
    modo_ciclico,
    captura_sobrantes,
    generar_csv_ciego,
    generar_csv_sobrantes,
    generar_csv_reporte,
    generar_csv_ciclico,
    generar_pdf,
    mostrar_avance_general,
    mostrar_avance_ciclico,
    mostrar_avance_ciego,
    mostrar_sidebar,
)

with st.sidebar:
    mostrar_sidebar()

# Configuración de página y encabezado
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.image(r"asstes\Ally_logo_mayo_2025.png", width=80)
with col_title:
    st.title("Auditoría de Inventario")

# Validación de datos necesarios desde session_state
if (
    "auditor" not in st.session_state or not st.session_state.auditor or
    "puesto" not in st.session_state or not st.session_state.puesto
):
    st.warning("Faltan datos del auditor o del puesto para comenzar.")
    st.stop()

# Verificar archivo y permitir carga si falta
if "archivo" not in st.session_state or st.session_state.archivo is None:
    st.warning("Falta subir el archivo de inventario.")
    st.session_state.archivo = st.file_uploader(
        "📁 Sube archivo de inventario (.csv)", 
        type=["csv"]
    )
    # Verificar si ya se cargó durante esta interacción
    if st.session_state.archivo is None:
        st.stop()

# Ya tenemos archivo: cargarlo
archivo = st.session_state.archivo

# Leer unos bytes del archivo para detectar la codificación
raw_data = archivo.getvalue()
result = chardet.detect(raw_data)
encoding_detected = result['encoding']

# Leer el CSV con la codificación detectada
df = pd.read_csv(io.StringIO(raw_data.decode(encoding_detected)))

# Cambiamos nombres de columnas
if df is not None:
    df.rename(columns={
                    "codigo de barras": "barcode",
                    "producto": "desc_corta",
                    "descripcion": "nombre",
                    "lote": "lote",
                    "unidades iniciales": "stock_inicial",
                    "unidades disponibles": "cantidad_sistema",
                    "costo del lote": "costo",
                    "fecha de expiracion": "caducidad",
                    "almacen": "almacen"
                }, inplace=True)


# Validar estructura del archivo
if "almacen" not in df.columns:
    st.error("La columna 'almacen' no está presente en el archivo.")
    st.stop()

if "auditoria_iniciada" not in st.session_state:
    st.session_state.auditoria_iniciada = False

col1, col2, col3 = st.columns(3)

with col1:
    # Selección de almacén
    #almacenes = df["almacen"].unique().tolist()
    #almacen = st.selectbox("🏬 Almacén a auditar", almacenes)
    #df = df[df["almacen"] == almacen]
    #df["cantidad_fisica"] = pd.NA

    # Selección de almacén (solo editable si no ha comenzado)
    almacenes = df["almacen"].unique().tolist()
    if not st.session_state.auditoria_iniciada:
        almacen = st.selectbox("🏬 Almacén a auditar", almacenes, key="select_almacen")
    else:
        almacen = st.session_state.get("almacen_seleccionado", "")
        st.markdown(f"**🏬 Almacén seleccionado:** {almacen}")

with col2:
    # Selección del tipo de inventario
    #modo = st.radio("📋 Tipo de inventario", ["Ciego", "General", "Cíclico"], horizontal=True)

    # Selección de tipo de inventario (solo editable si no ha comenzado)
    if not st.session_state.auditoria_iniciada:
        modo = st.radio("📋 Tipo de inventario", ["Ciego", "General", "Cíclico"], horizontal=True, key="modo_inventario")
    else:
        modo = st.session_state.get("modo_seleccionado", "")
        st.markdown(f"**📋 Modo de inventario:** {modo}")

with col3:
# Botón para fijar selección
    if not st.session_state.auditoria_iniciada:
        if st.button("✅ Empezar captura"):
                st.session_state.auditoria_iniciada = True
                st.session_state.almacen_seleccionado = st.session_state.select_almacen
                st.session_state.modo_seleccionado = st.session_state.modo_inventario
                st.rerun()
    else:
        st.markdown("#### 🧾 Generar y descargar:")
        col_csv, col_pdf = st.columns(2)

        with col_csv:
            exportar = st.button("📤 CSV")

        with col_pdf:
            exportar_pdf = st.button("📄 PDF")

        # Lógica de CSV
        if exportar:
            if modo == "Ciego":
                generar_csv_ciego()
            elif modo == "General":
                df_export = st.session_state.get("inventario-general_df")
                if df_export is not None:
                    generar_csv_reporte(df_export, st.session_state.auditor, modo)
            elif modo == "Cíclico":
                df_ciclico = st.session_state.get("inventario-ciclico_df")
                generar_csv_ciclico(df_ciclico)

        # Lógica de PDF
        if exportar_pdf:
            if modo == "General":
                df_export = st.session_state.get("inventario-general_df")
                if df_export is not None:
                    path_pdf = generar_pdf(
                        df_export,
                        st.session_state.auditor,
                        st.session_state.puesto,
                        almacen,
                        modo
                    )
                    with open(path_pdf, "rb") as f:
                        st.download_button(
                            label="⬇️ Descargar PDF",
                            data=f,
                            file_name=f"RI-{modo}-{datetime.now().strftime('%d-%m-%y')}.pdf",
                            mime="application/pdf",
                            key="download_pdf_general"  # 👈 clave única
                        )
            else:
                st.warning("PDF solo disponible por el momento para inventario general")



df = df[df["almacen"] == almacen]
df["cantidad_fisica"] = pd.NA

if not st.session_state.auditoria_iniciada:
    st.warning("Selecciona almacén y tipo de inventario y presiona 'Empezar captura'")
else:
    #seleccion de Modo
    modo = st.session_state.modo_seleccionado

    if modo == "Ciego":
        mostrar_avance_ciego()
        modo_ciego(st.session_state.auditor)


    # GENERAL
    elif modo == "General":
        if "inventario-general_df" not in st.session_state:
            modo_general(df, st.session_state.auditor, st.session_state.puesto, almacen, session_key="inventario-general_df")
        mostrar_avance_general(st.session_state["inventario-general_df"])

        if "sobrantes" not in st.session_state:
            st.session_state["sobrantes"] = []
        captura_sobrantes()
        

    # CÍCLICO
    elif modo == "Cíclico":
        if "inventario-ciclico_df" not in st.session_state:
            modo_ciclico(df, almacen, session_key="inventario-ciclico_df")

        if "sobrantes" not in st.session_state:
            st.session_state["sobrantes"] = []

        mostrar_avance_ciclico(st.session_state["inventario-ciclico_df"])
        captura_sobrantes()
        














