import streamlit as st
import pandas as pd
from pathlib import Path
from componentes import mostrar_sidebar
import unicodedata

# --- Configuración general ---
st.set_page_config(page_title="Visualización de Inventarios", layout="wide")

# --- Sidebar ---
with st.sidebar:
    mostrar_sidebar()

# --- Encabezado con logo ---
img_path = Path(__file__).parents[1] / "assets" / "Ally_logo_mayo_2025.png"
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.image(img_path, width=80)
with col_title:
    st.title("📊 Visualización de Inventarios")
st.text("V.Beta.0.2 -- Junio 2025")

# --- Subida de archivo ---
archivo = st.file_uploader("📁 Sube archivo CSV de inventario", type=["csv"])

if archivo is not None:
    try:
        df = pd.read_csv(archivo)
        st.success(f"Archivo cargado: {archivo.name}")
        
        # --- Verificación de columnas ---
        columnas_necesarias = ["barcode", "lote", "cantidad_sistema"]
        faltantes = [col for col in columnas_necesarias if col not in df.columns]
        if faltantes:
            st.error(f"❌ Faltan las columnas requeridas: {', '.join(faltantes)}")
            st.stop()
        
        # --- Asegurar columnas opcionales ---
        for col in ["desc_corta", "nombre"]:
            if col not in df.columns:
                df[col] = ""
         #--- Normalización profunda de columnas clave ---
            for col in ["barcode", "lote", "desc_corta", "nombre"]:
                if col in df.columns:
                    df[col] = (
                        df[col]
                        .astype(str)
                        .apply(lambda x: unicodedata.normalize("NFKC", x))  # normaliza Unicode
                        .str.replace(r"\s+", " ", regex=True)               # colapsa espacios múltiples
                        .str.strip()                                        # elimina espacios al inicio/final
                        .str.upper()                                        # homogeneiza mayúsculas
                    )
        # --- Agrupar por barcode y lote ---
        df_agrupado = (
            df.groupby(["barcode", "lote"], as_index=False)["cantidad_sistema"]
            .sum()
            .sort_values(by="cantidad_sistema", ascending=False)
        )

        # --- Buscador ---
        st.subheader("🔎 Buscador")
        term = st.text_input("Buscar por código, lote, nombre o descripción corta")

        if term:
            term_lower = term.lower()
            mask = (
                df["barcode"].astype(str).str.contains(term_lower, case=False, na=False)
                | df["lote"].astype(str).str.contains(term_lower, case=False, na=False)
                | df["desc_corta"].astype(str).str.contains(term_lower, case=False, na=False)
                | df["nombre"].astype(str).str.contains(term_lower, case=False, na=False)
            )

            resultados = (
                df.loc[mask, ["barcode", "lote", "desc_corta", "nombre", "cantidad_sistema"]]
                .drop_duplicates()
                .sort_values(by=["barcode", "lote"])
            )

            if resultados.empty:
                st.info("No se encontraron resultados.")
            else:
                st.dataframe(resultados, use_container_width=True)

                # --- Selección de un registro ---
                opciones = resultados.apply(
                    lambda x: f"{x['barcode']} | {x['lote']} | {x['nombre'] or x['desc_corta']}", axis=1
                )
                seleccion = st.selectbox("Selecciona un registro para ver detalles", opciones)

                if seleccion:
                    barcode_sel, lote_sel, *_ = seleccion.split(" | ")
                    detalle = df[
                        (df["barcode"].astype(str) == barcode_sel)
                        & (df["lote"].astype(str) == lote_sel)
                    ]
                    st.subheader("📦 Detalle del registro seleccionado")
                    st.dataframe(detalle, use_container_width=True)

        else:
            # --- Vista general agrupada ---
            st.subheader("Resumen agrupado por Barcode y Lote")
            cols = ["barcode", "lote", "cantidad_sistema"]
            if "nombre" in df.columns:
                cols.insert(2, "nombre")
            if "desc_corta" in df.columns:
                cols.insert(3, "desc_corta")
            df_resumen = (
                df.groupby(["barcode", "lote", "desc_corta", "nombre"], as_index=False)["cantidad_sistema"]
                .sum()
                .sort_values(by="cantidad_sistema", ascending=False)
            )
            st.dataframe(df_resumen, use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("Sube un archivo CSV para comenzar.")
