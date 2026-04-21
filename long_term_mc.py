import numpy as np
import pandas as pd

def simular_jump_diffusion(df_historico, anios=5, n_simulaciones=1000, prob_caos=0.015):
    """
    Modelo de Merton Jump-Diffusion
    Combina Movimiento Browniano (Normalidad) con un Proceso de Poisson (Caos/Ising-like jumps)
    """
    dias_a_predecir = int(anios * 252)
    
    # 1. Extraer comportamiento base
    log_returns = np.log(1 + df_historico['Close'].pct_change().dropna())
    mu_diario = log_returns.mean()
    sigma_diario = log_returns.std()
    
    # 2. Parámetros del CAOS (Saltos markovianos)
    # Asumimos que cuando hay pánico (Ising herd effect), el mercado cae un 5% de media, con mucha varianza
    mu_jump = -0.05 
    sigma_jump = 0.08
    
    # Corrección matemática para que el drift no se desvíe por incluir los saltos
    k = np.exp(mu_jump + 0.5 * sigma_jump**2) - 1
    drift_corregido = mu_diario - 0.5 * sigma_diario**2 - (prob_caos * k)
    
    precio_inicial = df_historico['Close'].iloc[-1]
    
    # 3. MATRICES DE SIMULACIÓN (Ejecución Vectorizada ultrarrápida)
    # Componente NORMAL (Browniano Geométrico)
    Z = np.random.normal(0, 1, size=(dias_a_predecir, n_simulaciones))
    difusion = sigma_diario * Z
    
    # Componente CAOS (Proceso de Poisson para decidir si hoy hay pánico)
    eventos_caos = np.random.poisson(prob_caos, size=(dias_a_predecir, n_simulaciones))
    # Magnitud del pánico si ocurre el evento
    magnitud_saltos = np.random.normal(mu_jump, sigma_jump, size=(dias_a_predecir, n_simulaciones))
    saltos_totales = eventos_caos * magnitud_saltos
    
    # Ecuación Estocástica Completa
    daily_returns = np.exp(drift_corregido + difusion + saltos_totales)
    
    # Construir caminos de precios
    price_list = np.zeros((dias_a_predecir + 1, n_simulaciones))
    price_list[0] = precio_inicial
    
    for t in range(1, dias_a_predecir + 1):
        price_list[t] = price_list[t-1] * daily_returns[t-1]
        
    fechas_futu = pd.date_range(start=df_historico.index[-1], periods=dias_a_predecir + 1, freq='B')
    
    # 4. Resultados
    curvas_estadisticas = {
        "Techo Histórico (P95)": np.percentile(price_list, 95, axis=1),
        "Tendencia Central (P50)": np.percentile(price_list, 50, axis=1),
        "Suelo de Riesgo (P05)": np.percentile(price_list, 5, axis=1)
    }
    
    # Seleccionamos aleatoriamente 3 caminos individuales para "ver" el caos
    indices_aleatorios = np.random.choice(n_simulaciones, 3, replace=False)
    caminos_caoticos = price_list[:, indices_aleatorios]
    
    return fechas_futu, curvas_estadisticas, caminos_caoticos

def evaluar_salud_proyeccion(curvas, precio_inicial):
    p50_final = curvas["Tendencia Central (P50)"][-1]
    p05_final = curvas["Suelo de Riesgo (P05)"][-1]
    
    retorno_esperado = (p50_final / precio_inicial) - 1
    riesgo_maximo = (p05_final / precio_inicial) - 1
    
    # Lógica de valoración
    if retorno_esperado > 0.50 and riesgo_maximo > -0.20:
        score = "Excelente (Crecimiento Robusto)"
        color = "green"
    elif retorno_esperado > 0 and riesgo_maximo > -0.40:
        score = "Moderada (Tendencia Positiva con Volatilidad)"
        color = "orange"
    elif retorno_esperado < 0:
        score = "Alerta (El Caos domina la tendencia)"
        color = "red"
    else:
        score = "Especulativa (Alto Riesgo de Cola)"
        color = "darkred"
        
    return score, color, retorno_esperado, riesgo_maximo