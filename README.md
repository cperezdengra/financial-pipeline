# 📈 Unified Investment Portfolio Dashboard Pro

![Tech Stack](https://img.shields.io/badge/Tech-Python%20%7C%20Streamlit%20%7C%20SciPy%20%7C%20Plotly-blue)
![Status](https://img.shields.io/badge/Status-Advanced-success)

Un ecosistema avanzado de análisis financiero diseñado para la toma de decisiones basada en datos. Este dashboard no solo rastrea el rendimiento histórico, sino que utiliza modelos estocásticos de última generación para proyectar escenarios de riesgo y retorno.

---

## Funcionalidades Clave

### 1. Análisis Pro de Métricas
Visualización instantánea de los KPIs vitales para cualquier inversor:
*   **CAGR (Tasa de Crecimiento Anual Compuesta)**: Medición del rendimiento real temporalizado.
*   **Max Drawdown**: Evaluación del riesgo de pérdida máxima histórica.
*   **Sharpe Ratio**: Ratio de eficiencia rentabilidad/riesgo.
*   **Beta**: Sensibilidad respecto al mercado general (S&P 500).

### 2. Motores de Simulación Estocástica
El núcleo del proyecto integra modelos matemáticos avanzados para predecir el comportamiento del activo:

*   **Motor Monte Carlo Markoviano (90d)**: Utiliza una **Cadena de Markov de primer orden** para alternar entre regímenes de **Calma** (distribución Normal) y **Caos** (distribución t-Student con colas pesadas). Incluye detección automática del estado inicial basada en el último cierre del mercado.
*   **Modelo Jump-Diffusion (Largo Plazo)**: Basado en el modelo de **Merton**, proyecta hasta 10 años integrando el **Efecto Ising** (comportamiento de rebaño) para simular Shocks sistémicos y "Cisnes Negros" que no captura la estadística tradicional.

### 3. Gestión Dinámica de Cartera
*   **Configuración de Tickers**: Persistencia automática de la lista de activos a través de `tickers_config.txt`.
*   **Análisis Individualizado**: Pestañas dedicadas para Dividendos, Ficha Técnica y análisis visual de Drawdown.

---

## 🛠️ Arquitectura Técnica

*   **Backend**: Python con procesamiento vectorizado en NumPy para simulaciones de Monte Carlo ultrarrápidas.
*   **Estadística**: SciPy (Stats) para modelado de distribuciones Cauchy, t-Student, y Skew-Normal.
*   **Frontend**: Streamlit para una interfaz reactiva y profesional.
*   **Visualización**: Plotly Graph Objects para gráficos financieros interactivos y dinámicos.

---

## Instalación y Despliegue

### Requisitos Previos
*   Python 3.9 o superior.
*   Entorno virtual (recomendado).

### Pasos para Ejecución Local

1.  **Clonar el repositorio**:
    ```bash
    git clone https://github.com/cperezdengra/financial-pipeline.git
    cd Unified-Investment-Portfolio-Dashboard
    ```

2.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Ejecutar el Dashboard**:
    ```bash
    streamlit run mi_dashboard_completo.py
    ```

---

## Estructura del Proyecto

*   `mi_dashboard_completo.py`: Punto de entrada principal y orquestador de la UI en Streamlit.
*   `mc_motor.py`: Motor de simulación de corto plazo con lógica de estados de Markov.
*   `long_term_mc.py`: Implementación del modelo stocástico de Jump-Diffusion para largo plazo.
*   `tickers_config.txt`: Archivo de configuración que almacena tu lista de activos.

---

## Autor
Proyecto desarrollado por **Carlos Pérez Dengra**.

> [!NOTE]
> Este dashboard es una herramienta de análisis estadístico y no constituye asesoramiento financiero. Las simulaciones de Monte Carlo se basan en probabilidades históricas y no garantizan rendimientos futuros.