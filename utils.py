import streamlit as st
import time
import base64

def mostrar_splash_screen(ruta_logo, duracion=3):
    # Convertimos imagen a base64 para que Streamlit la lea bien en HTML
    with open(ruta_logo, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(f"""
            <style>
                .stApp {{ background-color: white; }} /* Fondo limpio */
                .centered {{
                    display: flex; flex-direction: column;
                    justify-content: center; align-items: center;
                    height: 70vh; text-align: center;
                }}
            </style>
            <div class="centered">
                <img src="data:image/jpeg;base64,{data}" width="250" style="border-radius: 20px;">
                <h1 style="margin-top: 20px;">Financial Bear Buddies</h1>
                <div class="loader"></div>
            </div>
        """, unsafe_allow_html=True)
        time.sleep(duracion)
    placeholder.empty()