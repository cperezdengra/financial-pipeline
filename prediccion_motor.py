from prophet import Prophet
import pandas as pd

def generar_escenarios(df_historico, dias_a_predecir=90):
    # Preparar datos para Prophet (requiere columnas 'ds' y 'y')
    df_prophet = df_historico.reset_index()[['Date', 'Close']]
    df_prophet.columns = ['ds', 'y']
    df_prophet['ds'] = df_prophet['ds'].dt.tz_localize(None)

    # Configurar y entrenar el modelo
    modelo = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=True)
    modelo.fit(df_prophet)

    # Crear dataframe futuro
    futuro = modelo.make_future_dataframe(periods=dias_a_predecir)
    forecast = modelo.predict(futuro)

    # Extraer solo el futuro
    prediccion = forecast.tail(dias_a_predecir)
    
    # Definir Escenarios basados en intervalos de confianza
    escenarios = {
        "Muy Optimista": prediccion['yhat_upper'] * 1.05,
        "Optimista": prediccion['yhat_upper'],
        "Neutral (Base)": prediccion['yhat'],
        "Conservador": prediccion['yhat_lower'],
        "Pesimista": prediccion['yhat_lower'] * 0.95
    }
    
    return prediccion['ds'], escenarios