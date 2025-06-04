import streamlit as st
import pandas as pd
from componentes import mostrar_sidebar
import os

img_path = os.path.join(os.path.dirname(__file__), "asstes", "Ally_logo_mayo_2025.png")

# Configuración de página y encabezado
st.set_page_config(page_title="Inventarios Ally", layout="wide")
col_logo, col_title = st.columns([1, 6])
with col_logo:
    st.image(img_path, width=80)
with col_title:
    st.title("Inventarios Ally")
st.text("V.Beta.0.1 -- Junio 2025")


if "registro_completado" not in st.session_state:
    st.session_state.registro_completado = False



col_a, col_b, col_c = st.columns(3)

with col_a:
    if "auditor" not in st.session_state:
        st.session_state.auditor = ""
    st.session_state.auditor = st.text_input(
        "👤 Nombre", 
        value=st.session_state.auditor, 
        placeholder="Ej. Carlos Salazar",
        disabled=st.session_state.registro_completado
    )

with col_b:
    if "puesto" not in st.session_state:
        st.session_state.puesto = ""
    st.session_state.puesto = st.text_input(
        "🪪 Puesto", 
        value=st.session_state.puesto, 
        placeholder="Ej. Supervisor de Almacén",
        disabled=st.session_state.registro_completado
    )

with col_c:
    st.session_state.archivo = st.file_uploader(
        "📁 Sube archivo de inventario (.csv)", 
        type=["csv"],
        disabled=st.session_state.registro_completado
    )
if st.session_state.registro_completado:
    st.markdown(f"""
    ### ✅ Registro completado
    **Auditor:** {st.session_state.auditor}  
    **Puesto:** {st.session_state.puesto}  
    **Archivo cargado:** `{st.session_state.archivo.name if st.session_state.archivo else 'Ninguno'}`
    """)

if st.button("Registrar") and not st.session_state.registro_completado:
    if st.session_state.auditor and st.session_state.puesto and st.session_state.archivo:
        # Leer archivo una vez y guardarlo como df en memoria
        st.session_state.df_original = pd.read_csv(st.session_state.archivo)
        
        # Guardar nombre para mostrar después si quieres
        st.session_state.archivo_nombre = st.session_state.archivo.name
        st.session_state.registro_completado = True
        st.success("✅ Sesión iniciada correctamente.")
        st.rerun()
    else:
        st.warning("❗️ Por favor llena todos los campos y sube el archivo.")


st.markdown("### ⚙️ Opciones")
st.markdown("Usa este botón si quieres **limpiar todo y comenzar desde cero**.")

if st.button("🧹 Limpiar todo"):
    st.session_state.clear()
    st.rerun()
    st.success("✅ Sesión reiniciada correctamente. Puedes empezar de nuevo.")


with st.sidebar:
    mostrar_sidebar()