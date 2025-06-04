import streamlit as st
import pandas as pd
from datetime import datetime

def modo_ciego(auditor):
    if "ciego_df" not in st.session_state:
        st.session_state["ciego_df"] = pd.DataFrame(columns=["barcode", "cantidad_fisica", "auditor", "fecha_hora"])

    with st.form("form_ciego", clear_on_submit=True):
        barcode = st.text_input("🔍 Escanea o escribe el código de barras", max_chars=50)
        cantidad = st.number_input("📦 Cantidad física", min_value=0, step=1)
        submitted = st.form_submit_button("➕ Agregar registro")

        if submitted and barcode.strip():
            nueva_fila = {
                "barcode": barcode.strip(),
                "cantidad_fisica": cantidad,
                "auditor": auditor,
                "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state["ciego_df"] = pd.concat(
                [st.session_state["ciego_df"], pd.DataFrame([nueva_fila])],
                ignore_index=True
            )
            st.success("✅ Registro agregado.")

    if not st.session_state["ciego_df"].empty:
        st.markdown("### 📋 Registros capturados:")
        st.dataframe(st.session_state["ciego_df"], use_container_width=True)

    if st.button("🔄 Otra captura"):
        st.session_state["ciego_df"] = pd.DataFrame(columns=["barcode", "cantidad_fisica", "auditor", "fecha_hora"])
        st.success("🚫 Registros eliminados.")

def modo_general(df, auditor, puesto, almacen, session_key="inventario-general_df"):
    df = df[df["almacen"] == almacen].copy()
    df["cantidad_fisica"] = pd.NA

    if session_key not in st.session_state:
        st.session_state[session_key] = df
    else:
        df = st.session_state[session_key]

    search_input = st.text_input("🔍 Escanea o escribe el código de barras (solo números)", key=f"search_input_general_{session_key}", placeholder="Ej. 7501234567890")

    if search_input and not search_input.isdigit():
        st.warning("⚠️ Solo se permiten números en el campo de búsqueda.")
        return

    if search_input:
        filtered_df = df[df["barcode"].astype(str).str.contains(search_input.strip())]

        if filtered_df.empty:
            st.error("❌ No se encontraron coincidencias con ese código de barras.")
        else:
            st.markdown(f"### 📋 Resultados para código: `{search_input}`")
            for idx, row in filtered_df.iterrows():
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    col1.markdown(f"**🧾 Nombre:** {row['nombre']}")
                    col2.markdown(f"**🏷️ Código:** {row['barcode']}")
                    col3.markdown(f"**🔢 Lote:** {row['lote']}")
                    col4.markdown(f"**📅 Caducidad:** {row['caducidad']}")
                    col5.markdown(f"**📦 Sistema:** {row['cantidad_sistema']}")
                    with col6:
                        cantidad_fisica = st.number_input(
                            f"Cantidad física (Lote {row['lote']})",
                            min_value=0, step=1,
                            key=f"cantidad_general_{idx}"
                        )
                        st.session_state[session_key].at[idx, "cantidad_fisica"] = cantidad_fisica


def modo_ciclico(df, almacen, session_key="inventario-ciclico_df"):
    df = df[df["almacen"] == almacen].copy()
    df["cantidad_fisica"] = pd.NA

    if session_key not in st.session_state:
        st.session_state[session_key] = df
    else:
        df = st.session_state[session_key]

    search_input = st.text_input(
        "🔍 Escanea o escribe el código de barras (solo números)",
        key=f"search_input_ciclico_{session_key}",
        placeholder="Ej. 7501234567890"
    )

    if search_input:
        if not search_input.isdigit():
            st.warning("⚠️ Solo se permiten números en el campo de búsqueda.")
            return

        filtered_df = df[df["barcode"].astype(str).str.contains(search_input.strip())]

        if filtered_df.empty:
            st.error("❌ No se encontraron coincidencias.")
        else:
            grouped = filtered_df.groupby("barcode").agg({
                "nombre": "first",
                "cantidad_sistema": "sum"
            }).reset_index()

            st.markdown(f"### 📋 Resultados para código: `{search_input}`")

            for idx, row in grouped.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns(3)
                    col1.markdown(f"**🧾 Nombre:** {row['nombre']}")
                    col2.markdown(f"**📦 Cant. Sistema total:** {row['cantidad_sistema']}")
                    with col3:
                        cantidad = st.number_input(
                            f"Cantidad física total para código {row['barcode']}",
                            min_value=0,
                            step=1,
                            key=f"cantidad_ciclica_{idx}"
                        )

                    # Distribuir proporcionalmente entre todas las filas con ese barcode
                    indices = df[df["barcode"] == row["barcode"]].index
                    for i in indices:
                        st.session_state[session_key].at[i, "cantidad_fisica"] = cantidad / len(indices)



def captura_sobrantes():
    if "sobrantes" not in st.session_state:
        st.session_state["sobrantes"] = []

    with st.expander("➕ Capturar productos sobrantes"):
        with st.form("form_sobrantes", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                codigo_sobrante = st.text_input("Código de barras*")
                producto_sobrante = st.text_input("Producto*")
            with col2:
                unidades_sobrante = st.number_input("Unidades encontradas", min_value=1, step=1)

            submitted = st.form_submit_button("Agregar sobrante")
            if submitted and codigo_sobrante and producto_sobrante:
                st.session_state["sobrantes"].append({
                    "codigo de barras": codigo_sobrante,
                    "producto": producto_sobrante,
                    "unidades encontradas": unidades_sobrante
                })
                st.success("✅ Producto sobrante agregado")
                st.rerun()

        if st.session_state["sobrantes"]:
            st.markdown("### 📋 Productos sobrantes registrados")
            sobrantes_df = pd.DataFrame(st.session_state["sobrantes"])
            st.dataframe(sobrantes_df, use_container_width=True)

            # Generar botón de descarga
            csv_sobrantes = sobrantes_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Descargar productos sobrantes",
                data=csv_sobrantes,
                file_name="productos_sobrantes.csv",
                mime="text/csv",
                key="csv_sobrantes"
            )


def mostrar_avance_general(df: pd.DataFrame):
    st.markdown("### 📊 Avance de captura - Inventario General")
    col1, col2, col3 = st.columns(3)

    # Productos completos
    def producto_completo(grupo):
        return grupo["cantidad_fisica"].notna().all()

    productos = df.groupby("barcode", group_keys=False).apply(lambda g: producto_completo(g.drop(columns="barcode")))
    productos_totales = len(productos)
    productos_completos = productos.sum()
    col1.metric("Productos completos", f"{productos_completos} / {productos_totales}")
    col1.progress(productos_completos / productos_totales if productos_totales else 0)

    # Lotes capturados
    total_lotes = len(df)
    lotes_capturados = df["cantidad_fisica"].notna().sum()
    col2.metric("Lotes capturados", f"{lotes_capturados} / {total_lotes}")
    col2.progress(lotes_capturados / total_lotes if total_lotes else 0)

    # Sobrantes
    if "sobrantes" in st.session_state:
        total_sobrantes = len(st.session_state["sobrantes"])
    else:
        total_sobrantes = 0
    col3.metric("Sobrantes registrados", f"{total_sobrantes}")


def mostrar_avance_ciclico(df: pd.DataFrame):
    st.markdown("### 📊 Avance de captura - Inventario Cíclico")
    col1, col2 = st.columns(2)

    total_codigos = df["barcode"].nunique()
    codigos_capturados = df[df["cantidad_fisica"].notna()]["barcode"].nunique()

    col1.metric("Productos capturados", f"{codigos_capturados} / {total_codigos}")
    col1.progress(codigos_capturados / total_codigos if total_codigos else 0)

    # Sobrantes
    col2.metric("Sobrantes registrados", f"{len(st.session_state['sobrantes'])}")
    

def mostrar_avance_ciego():
    st.markdown("### 📊 Avance de captura - Inventario Ciego")
    df_ciego = st.session_state.get("ciego_df", pd.DataFrame())
    total = len(df_ciego)

    st.metric("Capturas registradas", f"{total}")
    st.progress(min(total / 100, 1.0))  # escala opcional


