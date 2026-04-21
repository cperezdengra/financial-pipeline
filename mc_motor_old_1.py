import numpy as np
import pandas as pd

def simular_monte_carlo(df_historico, dias_a_predecir=90, n_simulaciones=1000):
    # Calcular retornos logarítmicos
    log_returns = np.log(1 + df_historico['Close'].pct_change()).dropna()
    
    # Parámetros estadísticos
    u = log_returns.mean()  # Drift (Tendencia media)
    var = log_returns.var() # Varianza
    stdev = log_returns.std() # Volatilidad
    
    # Cálculo del Drift ajustado
    drift = u - (0.5 * var)
    
    # Generar movimientos aleatorios (Brownian Motion)
    # Z representa el shock aleatorio del mercado
    Z = np.random.normal(size=(dias_a_predecir, n_simulaciones))
    
    # Matriz de retornos diarios proyectados
    daily_returns = np.exp(drift + stdev * Z)
    
    # Proyección de precios inicializando en el último precio real
    precio_inicial = df_historico['Close'].iloc[-1]
    price_list = np.zeros_like(daily_returns)
    price_list[0] = precio_inicial * daily_returns[0]
    
    for t in range(1, dias_a_predecir):
        price_list[t] = price_list[t-1] * daily_returns[t]
    
    # Cálculo de Escenarios (Percentiles)
    # 95% = Muy Optimista, 75% = Optimista, 50% = Mediana, etc.
    escenarios = {
        "Muy Optimista (P95)": price_list[-1, :], 
        "Optimista (P75)": price_list[-1, :],
        "Neutral (P50)": price_list[-1, :],
        "Conservador (P25)": price_list[-1, :],
        "Pesimista (P05)": price_list[-1, :]
    }
    
    # Creamos un eje de tiempo para la gráfica
    fechas_futu = pd.date_range(start=df_historico.index[-1], periods=dias_a_predecir + 1, freq='B')[1:]
    
    # Calculamos las líneas de evolución para cada percentil
    curvas = {
        "Muy Optimista": np.percentile(price_list, 95, axis=1),
        "Optimista": np.percentile(price_list, 75, axis=1),
        "Neutral": np.percentile(price_list, 50, axis=1),
        "Conservador": np.percentile(price_list, 25, axis=1),
        "Pesimista": np.percentile(price_list, 5, axis=1)
    }
    
    # El error estándar de la media en MC es sigma / sqrt(N)
    error_est = stdev / np.sqrt(n_simulaciones)
    
    return fechas_futu, curvas, error_est