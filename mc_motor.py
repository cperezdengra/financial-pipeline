import pandas as pd
import numpy as np
from scipy.stats import t, norm

def simular_monte_carlo(hist, n_simulaciones=1000, dias_pred=90, detectar_inicio=False):
    # 1. Análisis de Retornos Históricos
    retornos = hist['Close'].pct_change().dropna()
    ultimo_precio = hist['Close'].iloc[-1]
    
    # Parámetros por régimen (estimados del histórico)
    mu_calma = retornos[retornos > retornos.quantile(0.2)].mean()
    sigma_calma = retornos[retornos > retornos.quantile(0.2)].std()
    
    mu_caos = retornos[retornos < retornos.quantile(0.2)].mean()
    sigma_caos = retornos[retornos < retornos.quantile(0.2)].std()

    # 2. Matriz de Transición de Markov
    matriz_transicion = np.array([
        [0.95, 0.05], # Es muy probable seguir en calma si ya estás en calma
        [0.15, 0.85]  # Si entras en caos, es probable que te quedes ahí un tiempo
    ])

    # Detección de estado inicial
    if detectar_inicio:
        p20 = retornos.quantile(0.2)
        estado_inicial = 1 if retornos.iloc[-1] < p20 else 0
    else:
        estado_inicial = 0

    simulaciones = np.zeros((dias_pred, n_simulaciones))

    for s in range(n_simulaciones):
        precios_camino = [ultimo_precio]
        estado_actual = estado_inicial 
        
        for d in range(dias_pred):
            # Determinamos el estado del día siguiente usando la cadena de Markov
            probabilidades = matriz_transicion[estado_actual]
            estado_actual = np.random.choice([0, 1], p=probabilidades)

            if estado_actual == 0:
                retorno_dia = norm.rvs(loc=mu_calma, scale=sigma_calma)
            else:
                ruido_t = t.rvs(df=3)
                retorno_dia = mu_caos + (ruido_t * sigma_caos)

            nuevo_precio = precios_camino[-1] * (1 + retorno_dia)
            precios_camino.append(max(nuevo_precio, 0.0001))
            
        simulaciones[:, s] = precios_camino[1:]

    # 3. Preparación de Datos para Streamlit
    ultima_fecha = hist.index[-1]
    fechas_futu = pd.date_range(start=ultima_fecha + pd.Timedelta(days=1), periods=dias_pred, freq='B')

    curvas = {
        'Muy Optimista (P95)': np.percentile(simulaciones, 95, axis=1),
        'Optimista (P75)': np.percentile(simulaciones, 75, axis=1),
        'Neutral (P50)': np.percentile(simulaciones, 50, axis=1),
        'Conservador (P25)': np.percentile(simulaciones, 25, axis=1),
        'Pesimista (P5)': np.percentile(simulaciones, 5, axis=1)
    }
    
    error = np.std(simulaciones[-1, :]) / np.sqrt(n_simulaciones)
    
    return fechas_futu, curvas, error, estado_inicial