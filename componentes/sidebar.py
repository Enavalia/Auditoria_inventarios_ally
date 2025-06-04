import streamlit as st



def mostrar_sidebar():
    st.markdown("### ⚙️ Opciones de sesión")

    if "confirm_reset" not in st.session_state:
        st.session_state["confirm_reset"] = False

    if st.button("🧹 Limpiar todo y reiniciar"):
        st.session_state["confirm_reset"] = True

    if st.session_state["confirm_reset"]:
        st.warning("¿Seguro que quieres limpiar toda la sesión?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmar limpieza"):
                st.session_state.clear()
                st.success("Sesión limpiada correctamente.")
                st.rerun()
        with col2:
            if st.button("❌ Cancelar"):
                st.session_state["confirm_reset"] = False


