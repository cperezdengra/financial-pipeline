import streamlit as st
import yfinance as yf
import pandas as pd
import os

# Configuración de la página
st.set_page_config(page_title="Monitor de Inversion Profesional", layout="wide")
st.title("Monitor Avanzado de Inversiones")

# Archivo local muy ligero para persistir solo los nombres de los tickers
CONFIG_FILE = "mis_fondos.txt"

def cargar_tickers():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return f.read().strip()
    return "IWDA.AS, VOO, AAPL"

def guardar_tickers(tickers_str):
    with open(CONFIG_FILE, "w") as f:
        f.write(tickers_str)

# Sidebar para gestión de cartera
st.sidebar.header("Configuracion de Cartera")
tickers_input = st.sidebar.text_input(
    "Introduce tickers separados por coma:", 
    value=cargar_tickers()
)

if st.sidebar.button("Guardar lista de fondos"):
    guardar_tickers(tickers_input)
    st.sidebar.success("Lista actualizada")

# Division de la pantalla principal
tickers = [t.strip() for t in tickers_input.split(',') if t.strip()]

if st.button('Ejecutar Pipeline de Analisis'):
    for t in tickers:
        st.markdown("---")
        st.header(f"Activo: {t}")
        
        activo = yf.Ticker(t)
        # Descarga de historico y fundamentales a RAM
        df = activo.history(period="1y")
        info = activo.info
        
        if not df.empty:
            # Creacion de pestañas
            tab1, tab2, tab3, tab4 = st.tabs([
                "Analisis de Precio", 
                "Rendimiento y Dividendos", 
                "Datos Fundamentales",
                "Glosario de Terminos"
            ])
            
            with tab1:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.line_chart(df['Close'])
                with col2:
                    precio_actual = df['Close'].iloc[-1]
                    precio_inicial = df['Close'].iloc[0]
                    retorno_anual = ((precio_actual - precio_inicial) / precio_inicial) * 100
                    
                    st.metric("Precio Actual", f"{precio_actual:.2f}")
                    st.metric("Retorno 1 Año", f"{retorno_anual:.2f}%")
                    st.write("Volatilidad (Std Dev):", round(df['Close'].pct_change().std(), 4))
            
            with tab2:
                col_div1, col_div2 = st.columns(2)
                with col_div1:
                    dividendos = activo.dividends
                    if not dividendos.empty:
                        dividendos.index = dividendos.index.tz_localize(None)
                        st.write("Historico de Pagos")
                        st.bar_chart(dividendos.tail(10))
                    else:
                        st.write("No se detectan pagos de dividendos (Posible fondo de acumulacion).")
                with col_div2:
                    # Feature de volumen relativo
                    st.write("Volumen de Negociacion (Ultimos 30 dias)")
                    st.area_chart(df['Volume'].tail(30))
            
            with tab3:
                st.subheader(info.get('longName', t))
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    st.write("**Sector:**", info.get('sector', 'N/A'))
                    st.write("**Industria:**", info.get('industry', 'N/A'))
                    st.write("**Sede:**", info.get('city', 'N/A'), f", {info.get('country', 'N/A')}")
                with col_f2:
                    st.write("**Capitalizacion de Mercado:**", info.get('marketCap', 'N/A'))
                    st.write("**PER (Price/Earnings):**", info.get('trailingPE', 'N/A'))
                
                with st.expander("Descripcion del Negocio / Estrategia del Fondo"):
                    st.write(info.get('longBusinessSummary', 'No hay descripcion disponible.'))

            with tab4:
                st.subheader("Guia de Metricas")
                st.write("**Precio Actual:** Ultima cotizacion registrada por la API en tiempo real.")
                st.write("**Retorno 1 Año:** Variacion porcentual del precio desde hace 365 dias hasta hoy.")
                st.write("**Volatilidad:** Medicion del riesgo basada en la desviacion estandar de los retornos diarios.")
                st.write("**Market Cap:** Valor total de todas las acciones de la empresa o patrimonio del fondo.")
                st.write("**PER:** Relacion entre el precio y el beneficio; indica cuanto paga el mercado por cada euro de beneficio.")
                st.write("**Volumen:** Cantidad de activos intercambiados; indica la liquidez del instrumento.")
        else:
            st.error(f"Error al cargar {t}. Verifique el ticker.")

st.sidebar.markdown("---")
st.sidebar.write("Estado: Pipeline listo")