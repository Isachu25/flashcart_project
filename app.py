import streamlit as st
import json
import time
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Simulador KV + Analítica", layout="wide")
st.title("⚡ KV Store: Monitor de Infraestructura & RAM")

# --- INICIALIZACIÓN DEL ESTADO ---
if 'kv_store' not in st.session_state:
    st.session_state.kv_store = {}

# --- LAYOUT PRINCIPAL ---
col_set, col_get = st.columns(2)

# ==========================================
# 1. SET (GUARDAR)
# ==========================================
with col_set:
    st.subheader("1. Guardar (SET)")
    with st.form("set_form"):
        key_input = st.text_input("🔑 Clave (ID Cliente):", placeholder="cliente_A")
        # Un JSON más pesado por defecto para que se note en la gráfica
        default_json = """{
  "usuario": "Ana",
  "historial": ["Login", "Compra", "Logout", "Login"],
  "metadata": "Este es un objeto más pesado para probar la RAM"
}"""
        value_input = st.text_area("📦 Valor (JSON):", value=default_json, height=150)
        submitted = st.form_submit_button("Guardar en RAM")
        
        if submitted and key_input:
            try:
                json_obj = json.loads(value_input)
                st.session_state.kv_store[key_input] = {
                    'value': json_obj,
                    'timestamp': time.time()
                }
                st.success(f"✅ Guardado: {key_input}")
            except json.JSONDecodeError:
                st.error("❌ JSON inválido")

# ==========================================
# 2. GET (RECUPERAR)
# ==========================================
with col_get:
    st.subheader("2. Leer (GET)")
    search_key = st.text_input("🔍 Buscar Clave:", placeholder="cliente_A")
    if st.button("Buscar"):
        if search_key in st.session_state.kv_store:
            data = st.session_state.kv_store[search_key]
            # Validar TTL visual (60s)
            age = time.time() - data['timestamp']
            if age > 60:
                st.error(f"❌ Expirado (hace {age:.1f}s)")
            else:
                st.success(f"🚀 Activo ({age:.1f}s antigüedad)")
                st.json(data['value'])
        else:
            st.warning("⚠️ Clave no encontrada")

# ==========================================
# 3. ANALÍTICA DE INFRAESTRUCTURA (NUEVO)
# ==========================================
st.divider()
st.header("📊 Dashboard de Infraestructura (Memoria)")

# Preparación de datos para analítica
analytics_data = []
total_ram_usage = 0
current_time = time.time()
keys_to_delete = [] # Para el garbage collector

if st.session_state.kv_store:
    for key, item in st.session_state.kv_store.items():
        # 1. CÁLCULO DE BYTES (Size of Payload)
        # Convertimos el objeto a string JSON y medimos sus bytes reales (utf-8)
        # Esto simula el espacio que ocuparía en disco o red.
        serialized_data = json.dumps(item['value'])
        size_in_bytes = len(serialized_data.encode('utf-8'))
        
        total_ram_usage += size_in_bytes
        
        # Lógica de expiración para la tabla
        age = current_time - item['timestamp']
        status = "🔴 Expirado" if age > 60 else "🟢 Activo"
        if age > 60: keys_to_delete.append(key)

        analytics_data.append({
            "Clave (ID)": key,
            "Tamaño (Bytes)": size_in_bytes,
            "Estado": status,
            "Antigüedad (s)": round(age, 1)
        })

    # Creación del DataFrame
    df_analytics = pd.DataFrame(analytics_data)

    # --- MÉTRICAS Y GRÁFICOS ---
    
    # Layout de métricas
    m1, m2, m3 = st.columns(3)
    
    with m1:
        # 3. MÉTRICA DE PESO TOTAL
        st.metric(label="💾 Consumo Total RAM", value=f"{total_ram_usage} Bytes")
    
    with m2:
        st.metric(label="🔑 Claves Totales", value=len(analytics_data))
        
    with m3:
        if keys_to_delete:
            st.metric(label="🗑️ Basura Detectada", value=f"{len(keys_to_delete)} claves", delta="-Limpiar", delta_color="inverse")
        else:
            st.metric(label="Estado Salud", value="Óptimo")

    # 2. GRÁFICO DE BARRAS (CONSUMO POR CLIENTE)
    st.subheader("Top Consumidores de Memoria")
    # Configuramos el índice para que st.bar_chart use la Clave como eje X
    chart_data = df_analytics.set_index("Clave (ID)")
    st.bar_chart(chart_data["Tamaño (Bytes)"])

    # Tabla detallada y Botón de Limpieza
    c_table, c_clean = st.columns([3, 1])
    with c_table:
        st.dataframe(df_analytics, use_container_width=True)
        
    with c_clean:
        st.write("### Mantenimiento")
        if st.button("🧹 Garbage Collector", type="primary"):
            for k in keys_to_delete:
                del st.session_state.kv_store[k]
            st.toast("Memoria liberada correctamente")
            time.sleep(1)
            st.rerun()

else:
    st.info("💡 La base de datos está vacía. Añade claves arriba para ver las métricas de infraestructura.")
   
