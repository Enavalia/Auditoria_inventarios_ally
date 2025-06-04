from componentes import (
    mostrar_sidebar,
    )
import streamlit as st
import pandas as pd



st.set_page_config(page_title="Investigación de Inventario", layout="wide")
st.title("🔍 Módulo de Investigación de Inventario")
st.warning("V.Beta.0.1 -- Junio 2025 -- Modulo todavía en construcción y bajo pruebas")
with st.sidebar:
    mostrar_sidebar()


archivo = st.file_uploader("Sube el archivo de Inventario General", type="csv")

if archivo:
    df = pd.read_csv(archivo)

    # Verifica si la columna 'diferencia' existe y está llena, si no la calcula
    if "diferencia" not in df.columns or df["diferencia"].isna().all():
        df["diferencia"] = df["cantidad_fisica"] - df["cantidad_sistema"]


    diferencias = df[df["diferencia"].notna() & (df["diferencia"] != 0)].copy()


    if not diferencias.empty:
        st.subheader("📋 Productos con Diferencias")
        st.write("Asigna estatus de investigación, motivo y comentarios:")

        estatus_opciones = ["No empezado", "Bajo investigación", "Resuelto"]
        motivos_opciones = [
            "Falta por robo o merma", "Entrada mal registrada",
            "Error en conteo físico", "Producto mal ubicado",
            "Sobrante sin identificar", "Otro"
        ]

        # Mostrar resumen de faltantes y sobrantes
        faltantes = diferencias[diferencias["diferencia"] < 0]
        sobrantes = diferencias[diferencias["diferencia"] > 0]

        st.markdown(f"### 📉 Faltantes: {len(faltantes)} | 📈 Sobrantes: {len(sobrantes)}")

        for idx, row in diferencias.iterrows():
            with st.expander(f'📦 {row["desc_corta"]} | Diferencia: {row["diferencia"]}'):
                diferencias.at[idx, "estatus"] = st.selectbox("Estatus", estatus_opciones, key=f"estatus_{idx}")
                diferencias.at[idx, "motivo"] = st.selectbox("Motivo", motivos_opciones, key=f"motivo_{idx}")
                diferencias.at[idx, "comentarios"] = st.text_input("Comentarios", key=f"coment_{idx}")

        # Botón para exportar CSV
        st.markdown("---")
        st.success("✅ Revisión completa. Puedes descargar el reporte.")
        st.download_button(
            label="📥 Descargar reporte de investigación",
            data=diferencias.to_csv(index=False).encode("utf-8"),
            file_name="reporte_investigacion.csv",
            mime="text/csv"
        )
    else:
        st.info("No se encontraron productos con diferencia para investigar.")
