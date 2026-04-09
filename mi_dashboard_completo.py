import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
from mc_motor import simular_monte_carlo
from long_term_mc import simular_jump_diffusion 

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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Analisis Visual", "Dividendos", "Ficha Tecnica", "Guia de Uso", "Simulacion Monte Carlo", "Simulacion Monte Carlo (cierre)", "Simulacion a largo plazo MC (Ising+Brownian model)"])
    
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
                fechas_futu, curvas, error, _ = simular_monte_carlo(hist, n_simulaciones=n_sim)
                
                fig_mc = go.Figure()
                # Histórico reciente
                hist_view = hist.tail(120)
                fig_mc.add_trace(go.Scatter(x=hist_view.index, y=hist_view['Close'], name="Histórico", line=dict(color='black', width=2)))
                
                # Escenarios con colores RGBA para mejor visualización
                colores = {
                    'Muy Optimista (P95)': 'rgba(0, 128, 0, 0.9)', 
                    'Optimista (P75)': 'rgba(0, 128, 0, 0.4)', 
                    'Neutral (P50)': 'rgba(0, 0, 255, 1.0)', 
                    'Conservador (P25)': 'rgba(255, 165, 0, 0.4)', 
                    'Pesimista (P5)': 'rgba(255, 0, 0, 0.9)'
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
                c3.metric("Confianza (N)", f"{n_sim}")

    with tab6:
        st.subheader(f"Monte Carlo con Detección de Cierre: {ticker}")
        
        n_sim_c = st.select_slider(f"Número de Realizaciones (Cierre) para {ticker}:", options=[100, 500, 1000, 5000], value=1000, key=f"sim_c_{ticker}")
        
        st.caption("Esta simulación analiza el último cierre para decidir si empieza en modo Calma o Caos.")

        if st.button(f"Lanzar Simulación (Cierre) para {ticker}", key=f"btn_c_{ticker}"):
            with st.spinner('Analizando cierre y ejecutando...'):
                fechas_futu, curvas, error, est_ini = simular_monte_carlo(hist, n_simulaciones=n_sim_c, detectar_inicio=True)
                
                estado_str = "CAOS (Volatilidad Alta)" if est_ini == 1 else "CALMA (Normalidad)"
                st.info(f"Estado inicial detectado: **{estado_str}**")

                fig_mc = go.Figure()
                hist_view = hist.tail(120)
                fig_mc.add_trace(go.Scatter(x=hist_view.index, y=hist_view['Close'], name="Histórico", line=dict(color='black', width=2)))
                
                colores = {
                    'Muy Optimista (P95)': 'rgba(0, 128, 0, 0.9)', 
                    'Optimista (P75)': 'rgba(0, 128, 0, 0.4)', 
                    'Neutral (P50)': 'rgba(0, 0, 255, 1.0)', 
                    'Conservador (P25)': 'rgba(255, 165, 0, 0.4)', 
                    'Pesimista (P5)': 'rgba(255, 0, 0, 0.9)'
                }
                
                for nombre, valores in curvas.items():
                    fig_mc.add_trace(go.Scatter(
                        x=fechas_futu, 
                        y=valores, 
                        name=nombre, 
                        line=dict(dash='dash' if 'Neutral' not in nombre else 'solid', color=colores.get(nombre, 'grey'))
                    ))

                fig_mc.update_layout(title=f"Markov Chain Monte Carlo (Detección: {estado_str})", height=500)
                st.plotly_chart(fig_mc, use_container_width=True)
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Escenario Central (P50)", f"{curvas['Neutral (P50)'][-1]:.2f}")
                c2.metric("Error Est. Simulación", f"{error:.5f}")
                c3.metric("Estado Inicial", est_ini)

    with tab7:
        st.subheader(f"Proyección Estocástica (Jump-Diffusion): {ticker}")
        st.markdown("Modelo híbrido: **Movimiento Browniano (Normalidad)** + **Procesos de Poisson (Caos/Pánico)**")
        
        c_p1, c_p2, c_p3 = st.columns(3)
        anios_lp = c_p1.slider("Años a simular:", 1, 10, 5)
        n_sim_lp = c_p2.selectbox("Nº Simulaciones:", [1000, 5000, 10000], index=1)
        prob_caos = c_p3.slider("Prob. diaria de Caos (Ising effect):", 0.001, 0.05, 0.015, format="%.3f")
        
        if st.button(f"Simular Largo Plazo para {ticker}", key=f"lp_{ticker}"):
            with st.spinner(f'Calculando {n_sim_lp} universos paralelos con shocks de mercado...'):
                fechas_lp, curvas_lp, caminos_ejemplo = simular_jump_diffusion(hist, anios=anios_lp, n_simulaciones=n_sim_lp, prob_caos=prob_caos)
                
                fig_lp = go.Figure()
                
                # Contexto histórico (últimos 2 años)
                hist_view = hist.tail(500)
                fig_lp.add_trace(go.Scatter(x=hist_view.index, y=hist_view['Close'], name="Histórico Real", line=dict(color='black', width=2)))
                
                # 1. Dibujar el Cono de Probabilidades (Percentiles)
                colores_lp = {'Techo Histórico (P95)': 'rgba(0, 128, 0, 0.4)', 
                              'Tendencia Central (P50)': 'blue', 
                              'Suelo de Riesgo (P05)': 'rgba(255, 0, 0, 0.4)'}
                
                for nombre, valores in curvas_lp.items():
                    grosor = 3 if 'Central' in nombre else 1
                    fig_lp.add_trace(go.Scatter(x=fechas_lp, y=valores, name=nombre, line=dict(width=grosor, color=colores_lp[nombre])))

                # 2. Dibujar 3 Caminos Caóticos (Para ver los saltos)
                for i in range(caminos_ejemplo.shape[1]):
                    fig_lp.add_trace(go.Scatter(x=fechas_lp, y=caminos_ejemplo[:, i], name=f"Ruta Posible {i+1}", 
                                                line=dict(width=1, dash='dot', color='rgba(128, 128, 128, 0.6)')))

                fig_lp.update_layout(title=f"Evolución a {anios_lp} años (Mostrando 3 rutas específicas vs. Media)", height=600)
                st.plotly_chart(fig_lp, use_container_width=True)
                
                st.info(f"Fíjate en las líneas grises punteadas: representan 3 futuros posibles elegidos al azar. A diferencia del cono azul que es suave, estas líneas muestran **caídas abruptas** cuando el componente de Caos ($\lambda={prob_caos}$) se activa.")

                # --- SECCIÓN: VALORACIÓN CUANTITATIVA ---
                st.markdown("### Diagnóstico de la Simulación")
                
                from long_term_mc import evaluar_salud_proyeccion # Import local
                valoracion, color_val, ret_esp, ries_max = evaluar_salud_proyeccion(curvas_lp, precio_fin)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"**Estado General:**")
                    st.markdown(f"<h3 style='color:{color_val};'>{valoracion}</h3>", unsafe_allow_html=True)
                
                with col2:
                    st.metric("Retorno Mediano Est. (P50)", f"{ret_esp:+.2%}")
                    st.caption("Expectativa central tras X años.")
                
                with col3:
                    st.metric("Riesgo de 'Cisne Negro' (P05)", f"{ries_max:.2%}")
                    st.caption("Peor escenario estadístico (Caos).")

                # Análisis de convergencia de tendencias
                st.markdown("---")
                st.markdown("**Interpretación de Fuerzas:**")
                
                if ret_esp > 0 and abs(ries_max) < ret_esp:
                    st.success("Tendencia Dominante: Las tres métricas muestran resiliencia. El crecimiento orgánico del activo supera la probabilidad de shocks de Caos.")
                elif ret_esp > 0 and abs(ries_max) > ret_esp:
                    st.warning("Volatilidad Dominante: Aunque la media sube, un evento de Caos podría borrar años de ganancias. Es un activo para perfiles agresivos.")
                else:
                    st.error("Caos Dominante: La frecuencia de saltos o la baja rentabilidad histórica sugieren que el activo no compensa el riesgo a largo plazo.")


st.sidebar.markdown("---")
st.sidebar.caption("Pipeline Optimizado para Mac")