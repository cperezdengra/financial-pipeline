import yfinance as yf

# Esto descarga los datos directos a la variable 'df' en tu RAM
print("Descargando datos de ETF...")
df = yf.download("IWDA.AS", period="5d")

print("\n--- DATOS EN MEMORIA ---")
print(df)
print("\nEspacio en disco usado: 0 KB")
