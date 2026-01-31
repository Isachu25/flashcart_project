import streamlit as st
import pandas as pd
import time
import uuid
from datetime import datetime

# Configuración
st.set_page_config(page_title="FlashCartPro: Polyglot Persistence", layout="wide")
st.title("⚡ FlashCartPro: Arquitectura Políglota")
st.markdown("### Redis (Caché/Carrito) + MongoDB (Persistencia/Pedidos)")

# --- SIMULACIÓN DE BASES DE DATOS (Backend) ---

# 1. Simulación de Redis (Key-Value Store)
# En la vida real, esto sería un servidor Redis. Aquí es un diccionario en memoria.
if 'redis_db' not in st.session_state:
    st.session_state.redis_db = {}

# 2. Simulación de MongoDB (Document Store)
# En la vida real, esto sería un cluster MongoDB. Aquí es una lista de objetos.
if 'mongo_db' not in st.session_state:
    st.session_state.mongo_db = []

# --- INTERFAZ DE USUARIO (Frontend) ---

col1, col2, col3 = st.columns(3)

# COLUMNA 1: Catálogo de Productos (La Tienda)
with col1:
    st.subheader("1. Tienda (Catálogo)")
    st.info("Selecciona productos para enviar a Redis.")
    
    products = [
        {"id": "p1", "name": "Laptop Gamer", "price": 1200},
        {"id": "p2", "name": "Ratón Inalámbrico", "price": 25},
        {"id": "p3", "name": "Teclado Mecánico", "price": 80},
        {"id": "p4", "name": "Monitor 4K", "price": 300}
    ]
    
    for p in products:
        c1, c2 = st.columns([3, 1])
        c1.write(f"**{p['name']}** (${p['price']})")
        if c2.button("➕", key=p['id']):
            # LÓGICA REDIS: SET key value
            # Usamos el ID del usuario (simulado) + ID producto como clave
            user_session = "user_123" 
            redis_key = f"cart:{user_session}:{p['id']}"
            
            # En Redis real: r.set(redis_key, json.dumps(p))
            st.session_state.redis_db[redis_key] = p
            st.toast(f"Guardado en Redis: {redis_key}")

# COLUMNA 2: El Carrito (Redis - Key-Value)
with col2:
    st.subheader("2. Redis (Carrito en Vivo)")
    st.warning("Almacenamiento temporal. Alta velocidad. Estructura Clave-Valor.")
    
    # Mostrar contenido de Redis
    if st.session_state.redis_db:
        st.write("keys (claves) almacenadas:")
        st.json(st.session_state.redis_db)
        
        # Calcular total
        total = sum([item['price'] for item in st.session_state.redis_db.values()])
        st.metric("Total en Carrito", f"${total}")
        
        if st.button("🛒 Finalizar Compra (Checkout)", type="primary"):
            # LÓGICA DE MIGRACIÓN: De Redis a MongoDB
            
            # 1. Crear el objeto "Pedido" (Documento)
            order_doc = {
                "order_id": str(uuid.uuid4())[:8],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "completed",
                "items": list(st.session_state.redis_db.values()), # Anidamiento
                "total_paid": total
            }
            
            # 2. Guardar en MongoDB
            # En Mongo real: db.orders.insert_one(order_doc)
            st.session_state.mongo_db.append(order_doc)
            
            # 3. Limpiar Redis (El carrito temporal muere)
            st.session_state.redis_db = {}
            st.rerun()
            
    else:
        st.write("*El carrito está vacío (Redis keys = 0)*")

# COLUMNA 3: Historial de Pedidos (MongoDB - Documental)
with col3:
    st.subheader("3. MongoDB (Pedidos)")
    st.success("Almacenamiento persistente. Estructura JSON anidada.")
    
    if st.session_state.mongo_db:
        for order in reversed(st.session_state.mongo_db):
            with st.expander(f"Pedido #{order['order_id']}"):
                st.write(f"📅 {order['timestamp']}")
                st.write(f"💰 Total: ${order['total_paid']}")
                st.write("**Detalle del Documento JSON:**")
                st.json(order)
    else:
        st.write("*No hay pedidos históricos.*")

# --- Explicación Técnica ---
st.divider()
with st.expander("ℹ️ Arquitectura: ¿Por qué dos bases de datos?"):
    st.markdown("""
    * **Redis (Izquierda/Centro):** Se usa para el carrito porque necesitamos escribir y leer muy rápido cada vez que haces clic. No nos importa si la estructura es simple (Clave-Valor), nos importa la **velocidad**. Si el servidor se reinicia, no es grave perder un carrito.
    * **MongoDB (Derecha):** Se usa para el pedido final. Aquí necesitamos guardar la historia completa, con objetos anidados (lista de items dentro del pedido). Necesitamos **persistencia** y flexibilidad para análisis futuros.
    """)
