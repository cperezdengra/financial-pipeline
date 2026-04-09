import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from mc_motor import simular_monte_carlo

# Configuracion visual
st.set_page_config(page_title="Analisis Pro de Inversiones", layout="wide")
st.title("Financial Bear buddies")

# Gestion de tickers
CONFIG_FILE = "tickers_config.txt"

def obtener_tickers():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f: 
            return f.read().strip()
    return "IWDA.AS, VOO, QQQ"

# Sidebar
st.sidebar.header("Parametros del Pipeline")
lista_input = st.sidebar.text_area("Lista de Tickers (separados por coma):", value=obtener_tickers())
periodo = st.sidebar.select_slider("Ventana Temporal:", options=["1y", "2y", "5y", "10y", "max"], value="2y")

if st.sidebar.button("Guardar y Ejecutar"):
    with open(CONFIG_FILE, "w") as f: 
        f.write(lista_input)

# Procesamiento de la lista
tickers = [t.strip() for t in lista_input.split(",") if t.strip()]

for ticker in tickers:
    st.markdown(f"---")
    st.header(f"Activo: {ticker}")
    
    dat = yf.Ticker(ticker)
    hist = dat.history(period=periodo)
    info = dat.info
    
    if hist.empty:
        st.error(f"No hay datos para {ticker}")
        continue

    # --- CALCULO DE METRICAS ---
    precio_ini = hist['Close'].iloc[0]
    precio_fin = hist['Close'].iloc[-1]
    retorno_total = (precio_fin / precio_ini) - 1
    anios = (hist.index[-1] - hist.index[0]).days / 365.25
    cagr = (precio_fin / precio_ini) ** (1/anios) - 1
    rolling_max = hist['Close'].cummax()
    drawdown = (hist['Close'] / rolling_max) - 1
    max_drawdown = drawdown.min()
    retornos_diarios = hist['Close'].pct_change()
    sharpe = (retornos_diarios.mean() / retornos_diarios.std()) * np.sqrt(252) if retornos_diarios.std() != 0 else 0

    # KPIs Principales
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Precio Actual", f"{precio_fin:.2f}")
    m2.metric("Retorno Total", f"{retorno_total:.2%}")
    m3.metric("CAGR (Anual)", f"{cagr:.2%}")
    m4.metric("Max Drawdown", f"{max_drawdown:.2%}", delta_color="inverse")
    m5.metric("Sharpe Ratio", f"{sharpe:.2f}")

    # --- TABS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Analisis Visual", "Dividendos", "Ficha Tecnica", "Guia de Uso", "Simulacion Monte Carlo"])
    
    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name="Precio", line=dict(color='green')))
        fig.add_trace(go.Scatter(x=hist.index, y=rolling_max, name="Maximo", line=dict(dash='dash', color='grey')))
        fig.update_layout(title="Historico de Precios", height=400, margin=dict(l=0,r=0,b=0,t=40))
        st.plotly_chart(fig, use_container_width=True)
        st.write("**Caidas desde Maximos (Drawdown)**")
        st.area_chart(drawdown)

    with tab2:
        divs = dat.dividends
        if not divs.empty:
            divs.index = divs.index.tz_localize(None)
            c1, c2 = st.columns(2)
            c1.write("**Ultimos pagos registrados:**")
            c1.dataframe(divs.tail(10))
            # Fix compatible con pandas 3.x (reemplaza .last())
            div_anual = divs[divs.index > (divs.index.max() - pd.Timedelta(days=365))].sum()
            c2.metric("Dividend Yield Est.", f"{(div_anual/precio_fin):.2%}")
            c2.write(f"Total dividendos 12m: {div_anual:.2f}")
        else:
            st.info("Activo de acumulacion o sin dividendos reportados.")

    with tab3:
        st.subheader(info.get('longName', ticker))
        
        tipo_activo = info.get('quoteType', 'N/A')
        if tipo_activo == 'EQUITY':
            st.info("Este activo es una Accion (Empresa individual)")
        elif tipo_activo == 'ETF':
            st.info("Este activo es una ETF (Fondo Cotizado)")
        
        m_cap = info.get('marketCap', 'N/A')
        m_cap_str = f"{m_cap:,}" if isinstance(m_cap, (int, float)) else "N/A"
        
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            st.write(f"**Sector:** {info.get('sector', 'N/A')}")
            st.write(f"**Beta:** {info.get('beta', 'N/A')}")
            st.write(f"**Capitalizacion:** {m_cap_str}")
        with c_f2:
            st.write(f"**PER:** {info.get('trailingPE', 'N/A')}")
            st.write(f"**Precio/Ventas:** {info.get('priceToSalesTrailing12Months', 'N/A')}")
            st.write(f"**Moneda:** {info.get('currency', 'N/A')}")
        
        st.markdown("---")
        st.write("**Descripcion Detallada:**")
        st.write(info.get('longBusinessSummary', 'No hay descripcion disponible.'))

    with tab4:
        st.subheader("Explicacion de Funcionalidades")
        explicacion = """
        * **CAGR (Compound Annual Growth Rate):** Es la tasa de retorno media anual. Permite comparar activos de forma equitativa.
        * **Max Drawdown:** Indica la mayor caida porcentual desde un punto maximo anterior. Vital para entender el riesgo de perdida temporal.
        * **Sharpe Ratio:** Mide la rentabilidad en relacion al riesgo (volatilidad). >1.0 es bueno.
        * **Beta:** Sensibilidad respecto al mercado general (S&P 500).
        """
        st.markdown(explicacion)

    with tab5:
        st.subheader(f"Simulacion Monte Carlo: {ticker}")
        # Uso de claves únicas para mantener el estado en Streamlit
        n_sim = st.select_slider(f"Número de Realizaciones para {ticker}:", options=[100, 500, 1000, 5000], value=1000, key=f"sim_{ticker}")
        
        if st.button(f"Lanzar Simulación para {ticker}", key=f"btn_{ticker}"):
            with st.spinner('Ejecutando Caminos Aleatorios...'):
                fechas_futu, curvas, error = simular_monte_carlo(hist, n_simulaciones=n_sim)
                
                fig_mc = go.Figure()
                # Histórico reciente
                hist_view = hist.tail(120)
                fig_mc.add_trace(go.Scatter(x=hist_view.index, y=hist_view['Close'], name="Histórico", line=dict(color='black', width=2)))
                
                # Escenarios con colores RGBA para mejor visualización
                colores = {
                    'Muy Optimista': 'rgba(0, 128, 0, 0.9)', 
                    'Optimista': 'rgba(0, 128, 0, 0.4)', 
                    'Neutral': 'rgba(0, 0, 255, 1.0)', 
                    'Conservador': 'rgba(255, 165, 0, 0.4)', 
                    'Pesimista': 'rgba(255, 0, 0, 0.9)'
                }
                
                for nombre, valores in curvas.items():
                    fig_mc.add_trace(go.Scatter(
                        x=fechas_futu, 
                        y=valores, 
                        name=nombre, 
                        line=dict(dash='dash' if 'Neutral' not in nombre else 'solid', color=colores.get(nombre, 'grey'))
                    ))

                fig_mc.update_layout(title=f"Abanico de Probabilidades (Monte Carlo 90d) - {ticker}", height=500)
                st.plotly_chart(fig_mc, use_container_width=True)
                
                # Métricas de la simulación
                c1, c2, c3 = st.columns(3)
                c1.metric("Escenario Central (P50)", f"{curvas['Neutral'][-1]:.2f}")
                c2.metric("Error Est. Simulación", f"{error:.5f}")
                c3.metric("Confianza (N)", f"{n_sim}")

st.sidebar.markdown("---")
st.sidebar.caption("Pipeline Optimizado para Mac")