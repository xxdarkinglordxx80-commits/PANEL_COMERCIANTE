import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe

# ==========================
# ⚙️ CONFIGURACIÓN STREAMLIT
# ==========================
st.set_page_config(page_title="💫 Panel de Comerciantes Galáctico", layout="wide", page_icon="🌌")

# 🌌 Tema galáctico neón
st.markdown("""
<style>
body {
    background: radial-gradient(circle at 20% 20%, #0b0f29, #060717, #01010a);
    color: #e0e0ff;
    font-family: 'Segoe UI', sans-serif;
}
@keyframes stars {
    from {background-position: 0 0;}
    to {background-position: -10000px 5000px;}
}
body::before {
    content: "";
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: url("https://www.transparenttextures.com/patterns/stardust.png");
    opacity: 0.15;
    z-index: -1;
    animation: stars 200s linear infinite;
}
h1, h2, h3 {
    color: #00ffff;
    text-shadow: 0 0 10px #00ffff, 0 0 20px #0088ff;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080b1a, #0f1a3b);
    border-right: 1px solid rgba(0,255,255,0.3);
}
.stButton>button {
    background: linear-gradient(90deg, #00ffff, #9b00ff);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.6em 1.2em;
    box-shadow: 0 0 15px #00ffff88;
    transition: 0.3s;
    font-weight: 600;
}
.stButton>button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 25px #9b00ffcc, 0 0 50px #00ffffaa;
}
input, textarea, select {
    background-color: rgba(20,20,40,0.8) !important;
    color: #fff !important;
    border-radius: 10px !important;
    border: 1px solid rgba(0,255,255,0.4) !important;
}
hr {
    border-color: rgba(0,255,255,0.2);
}
</style>
""", unsafe_allow_html=True)

# ==========================
# 🔐 CONEXIÓN GOOGLE SHEETS
# ==========================
def conectar_google():
    try:
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file("client_secret.json", scopes=SCOPES)
        cliente = gspread.authorize(creds)
        return cliente
    except Exception as e:
        st.error(f"❌ Error de autenticación: {e}")
        return None

# ==========================
# 📄 LEER DATOS DE SHEETS
# ==========================
def obtener_datos(hoja):
    try:
        datos = get_as_dataframe(hoja, evaluate_formulas=True, dtype=str).dropna(how="all")
        datos.columns = datos.columns.str.strip().str.upper()
        return datos.fillna("")
    except Exception as e:
        st.error(f"❌ Error al leer la hoja: {e}")
        return pd.DataFrame()

# ==========================
# 💾 GUARDAR DATOS Y RECARGAR
# ==========================
def guardar_y_recargar(hoja, df):
    try:
        hoja.clear()
        set_with_dataframe(hoja, df.fillna(""))
        st.success("✅ Cambios guardados correctamente.")
        # 🔄 Forzar recarga inmediata desde Sheets
        return obtener_datos(hoja)
    except Exception as e:
        st.error(f"❌ Error al guardar: {e}")
        return df

# ==========================
# 🧮 INTERFAZ PRINCIPAL
# ==========================
def main():
    st.title("🌌 Panel de Comerciantes Galáctico 💼")

    st.markdown("#### 🧩 Ingresa el ID de tu Google Sheet:")
    GOOGLE_SHEET_ID = st.text_input("ID del documento (lo que va después de `/d/` y antes de `/edit`):")

    if not GOOGLE_SHEET_ID:
        st.info("👉 Ingresa el ID del documento para continuar.")
        return

    cliente = conectar_google()
    if not cliente:
        return

    try:
        hoja = cliente.open_by_key(GOOGLE_SHEET_ID).sheet1
    except Exception as e:
        st.error(f"❌ No se pudo acceder a la hoja: {e}")
        return

    # Estado persistente para mantener los datos actualizados en tiempo real
    if "datos" not in st.session_state:
        st.session_state.datos = obtener_datos(hoja)

    datos = st.session_state.datos

    # ==========================
    # 🔎 BUSCADOR
    # ==========================
    st.markdown("### 🔍 Buscar Comerciante")
    columnas = list(datos.columns)
    columna_busqueda = st.selectbox("Buscar por columna:", columnas, index=0)
    termino = st.text_input("Ingrese término de búsqueda:")

    if termino:
        datos_filtrados = datos[datos[columna_busqueda].str.contains(termino, case=False, na=False)]
    else:
        datos_filtrados = datos

    st.dataframe(datos_filtrados, use_container_width=True)

    # ==========================
    # ➕ AGREGAR NUEVO COMERCIANTE
    # ==========================
    st.markdown("---")
    st.subheader("💠 Agregar Nuevo Comerciante")

    with st.form("nuevo_comerciante"):
        nuevas_filas = {}
        for col in columnas:
            nuevas_filas[col] = st.text_input(f"{col}:")

        submitted = st.form_submit_button("🚀 Agregar Comerciante")

        if submitted:
            nueva_fila = pd.DataFrame([nuevas_filas]).reindex(columns=datos.columns, fill_value="")
            datos_actualizados = pd.concat([datos, nueva_fila], ignore_index=True)
            st.session_state.datos = guardar_y_recargar(hoja, datos_actualizados)

    # ==========================
    # ✏️ EDITAR DATOS
    # ==========================
    st.markdown("---")
    st.subheader("🪄 Editar Datos del Comerciante")

    indice_editar = st.number_input("Fila a editar (empezando en 0)", min_value=0, max_value=len(datos)-1, step=1)
    if 0 <= indice_editar < len(datos):
        fila_actual = datos.iloc[indice_editar]
        st.write("🧾 Datos actuales:", fila_actual.to_dict())

        columna_edit = st.selectbox("Selecciona columna a editar:", columnas)
        nuevo_valor = st.text_input("Nuevo valor:")

        if st.button("💫 Actualizar Registro"):
            if nuevo_valor:
                datos.at[indice_editar, columna_edit] = nuevo_valor
                st.session_state.datos = guardar_y_recargar(hoja, datos)
            else:
                st.warning("⚠️ Ingrese un nuevo valor antes de actualizar.")

    # ==========================
    # 🗑️ ELIMINAR DATOS
    # ==========================
    st.markdown("---")
    st.subheader("☄️ Eliminar Comerciante")

    indice_eliminar = st.number_input("Fila a eliminar (empezando en 0)", min_value=0, max_value=len(datos)-1, step=1)
    if st.button("💥 Eliminar Registro"):
        datos = datos.drop(index=indice_eliminar).reset_index(drop=True)
        st.session_state.datos = guardar_y_recargar(hoja, datos)

# ==========================
# 🚀 EJECUCIÓN
# ==========================
if __name__ == "__main__":
    main()
